import json
import logging

from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import backref

from .azure_tools import AzureTools
from .database import Model
from .extensions import db
from .host_status import HostStatus
from .roles import Roles
from . import names


logger = logging.getLogger("cloudlabs.admin")


class User(Model):
    """Representation of a CloudLabs user."""
    id = db.Column(db.Integer, primary_key=True)
    # admin = db.Column(db.Boolean)
    upi = db.Column(db.String(7), index=True, unique=True, nullable=False)
    ucl_id = db.Column(db.String(7), index=True, unique=True, nullable=False)
    name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False)
    # Azure child subscription ID
    # subscription_id = db.Column(db.String())

    ssh_keys = db.relationship('SshKey', backref='user',
                               order_by='SshKey.label')
    hosts = db.relationship('Host', backref='user', lazy='dynamic',
                            order_by='Host.label')
    _roles = db.relationship('UserRoles',
                             backref=backref('users', lazy='select', cascade='save-update, merge'),
                             lazy='joined',
                             collection_class=set,
                             cascade="all, delete-orphan",
                             passive_deletes=True)
    roles = association_proxy('_roles', 'name')

    def __repr__(self):
        return '<User: upi={}, name={}>'.format(self.upi, self.name)

    @classmethod
    def get_or_create(cls, eppn, **kwargs):
        """Find an existing user by ucl_id, or add a new one to the DB.

        Used typically when a user logs in to find the corresponding DB entry.

        Will update the user's UPI, name & email based on the latest Shibboleth
        data.
        """
        ucl_id, domain = eppn.split('@')
        user = cls.query.filter_by(ucl_id=ucl_id).first()
        if user is None:
            user = cls.create(ucl_id=ucl_id, **kwargs)
            logger.info("A new user %s (%s) has been created", user.ucl_id, user.name)
        else:
            fields = ['name', 'email', 'upi']
            updates = {}
            for field in fields:
                if kwargs[field] != getattr(user, field):
                    updates[field] = kwargs[field]
            if updates:
                logger.info(
                    "Updating information for user {} ".format(user.ucl_id)
                    + ", ".join("{}={}".format(attr, updates[attr]) for attr in updates)
                )
                user.update(**updates)
        return user


class UserRoles(Model):
    """Stores user roles."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.Enum(Roles), nullable=False, index=True)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, role):
        """Simple constructor for use by association_proxy."""
        self.name = role

    def __repr__(self):
        return '<Role: {}>'.format(self.name)


class SshKey(Model):
    """Stores public SSH keys for each user."""
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(50), nullable=False)
    public_key = db.Column(db.Text, nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<SshKey: user={}, label={}>'.format(
            self.user, self.label)


class Host(Model):
    """Stores details of virtual hosts created by CloudLabs."""
    id = db.Column(db.Integer, primary_key=True)
    # The canonical name of the host, as given by the user
    base_name = db.Column(db.String(50), unique=True, index=True,
                          nullable=False)
    # The actual domain name, including anything added for randomisation
    dns_name = db.Column(db.String(50), unique=True, index=True,
                         nullable=False)
    os_publisher = db.Column(db.String(50), default="Canonical")
    os_offer = db.Column(db.String(50), default="UbuntuServer")
    os_sku = db.Column(db.String(50), default="16.04-LTS")
    os_version = db.Column(db.String(50), default="latest")
    vm_type = db.Column(db.String(50))
    # TODO different max lenghts for base_name and dns_name?
    # TODO also keep the final DNS used, depending on the provider chosen?
    # (actually link() should be fine, but keeping comment for now for clarity)
    label = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    admin_username = db.Column(db.String(50), nullable=False)
    admin_password = db.Column(db.String(255))
    terraform_state = db.Column(db.Text)  # Could use JSON type???
    template = db.Column(db.Text)  # the Terraform template used for deployment

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    admin_ssh_key_id = db.Column(db.Integer, db.ForeignKey('ssh_key.id'),
                                 nullable=True)
    admin_ssh_key = db.relationship('SshKey', uselist=False)

    # Details used just when initialising the host
    git_repo = db.Column(db.String(1024))
    port = db.Column(db.Integer)
    setup_script = db.Column(db.Text)

    # Information about the running host
    status = db.Column(db.Enum(HostStatus), nullable=False,
                       server_default=HostStatus.defining.name)
    deploy_log = db.Column(db.Text, server_default='')

    # The task that will deploy this host (unless completed)
    task = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return '<Host: dns={}, user={}, label={}>'.format(
            self.dns_name, self.user, self.label)

    def __init__(self, *args, **kwargs):
        """Define a default setup_script as well as the supplied fields."""
        # Enrich the base name given in the form to add prefixes or randomness
        kwargs['dns_name'] = names.create_host_name(kwargs['base_name'])
        if ('setup_script' not in kwargs and 'git_repo' in kwargs and
                'port' in kwargs):
            kwargs['setup_script'] = self.default_setup_script(**kwargs)
        super(Host, self).__init__(*args, **kwargs)

    def default_setup_script(self, **kwargs):
        """Generate a default setup script for a new host.

        Will try to clone a specified git repo and build the Dockerfile
        contained within.

        :param git_repo: the git repository URL to clone on the host
        :param port: the port to expose, which should match that used by the
                     service defined in the Dockerfile
        """
        all_args = kwargs.copy()
        all_args['azure_url'] = names.azure_url(all_args['dns_name'])
        return '\n'.join([
            "sudo apt-get update",
            "sudo apt-get install docker.io -y",
            "git clone {git_repo} repo",
            "cd repo",
            "sudo docker build -t web-app .",
            ("sudo docker run -d -e "
             "AZURE_URL={azure_url} -p {port}:{port} web-app")]
            ).format(**all_args)

    @property
    def link(self):
        """The full URL to this host when deployed, for use in href attributes."""
        return 'http://{}:{}'.format(self.basic_url, self.port)

    @property
    def basic_url(self):
        """This host's URL without scheme, suitable for user display."""
        return self.base_name + '.cloudlabs.rc.ucl.ac.uk'

    @property
    def underlying_url(self):
        """The URL of the host in the underlying cloud provider.

        Should primarily be used for testing, not user display.
        """
        return 'http://{}:{}'.format(names.azure_url(self.dns_name), self.port)

    @property
    def auth_type(self):
        """Whether public key or password auth is used for this host."""
        if self.admin_ssh_key:
            return 'Public key'
        else:
            return 'Password'

    @property
    def parsed_state(self):
        """Lazily parse the Terraform state as JSON when needed."""
        if not hasattr(self, '_state'):
            if not self.terraform_state:
                return {}
            self._state = json.loads(self.terraform_state)
        return self._state

    @property
    def vm_info(self):
        """Extract our VM resource info from the Terraform state."""
        try:
            resources = self.parsed_state['modules'][0]['resources']
            return resources['azurerm_virtual_machine.vm']['primary']['attributes']
        except (KeyError, AttributeError):
            return {}

    @property
    def vm_id(self):
        """Extract our VM resource info from the Terraform state."""
        return self.vm_info.get('id', 'Error retrieving ID')

    @property
    def vm_size(self):
        return self.vm_info.get('vm_size', 'Unknown')

    @property
    def os_info(self):
        info = "Unknown"
        if self.os_offer:
            info = "{} {} ({})".format(self.os_offer,
                                       self.os_sku,
                                       self.os_version)
        return info

    @property
    def group_exists(self):
        """Whether or not the associated resource group exists on the cloud."""
        return AzureTools().group_exists(names.group_name(self))
