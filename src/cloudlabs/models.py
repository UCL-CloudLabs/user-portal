from .extensions import db
from .database import Model


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

    ssh_keys = db.relationship('SshKey', backref='user', order_by='SshKey.label')
    hosts = db.relationship('Host', backref='user', lazy='dynamic', order_by='Host.label')

    def __repr__(self):
        return '<User: upi={}, name={}>'.format(
            self.upi, self.name)

    @classmethod
    def get_or_create(cls, eppn, **kwargs):
        """Find an existing user by ucl_id, or add a new one to the DB.

        Used typically when a user logs in to find the corresponding DB entry.

        Will update the user's UPI, name & email based on the latest Shibboleth data.
        """
        ucl_id, domain = eppn.split('@')
        user = cls.query.filter_by(ucl_id=ucl_id).first()
        if user is None:
            user = cls.create(ucl_id=ucl_id, **kwargs)
        else:
            fields = ['name', 'email', 'upi']
            updates = {}
            for field in fields:
                if kwargs[field] != getattr(user, field):
                    updates[field] = kwargs[field]
            if updates:
                user.update(**updates)
        return user


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
    dns_name = db.Column(db.String(50), unique=True, index=True, nullable=False)
    label = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text)
    admin_username = db.Column(db.String(50), nullable=False)
    admin_password = db.Column(db.String(255))
    terraform_state = db.Column(db.Text)  # Could use JSON type???

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    admin_ssh_key_id = db.Column(db.Integer, db.ForeignKey('ssh_key.id'), nullable=True)
    admin_ssh_key = db.relationship('SshKey', uselist=False)

    def __repr__(self):
        return '<Host: dns={}, user={}, label={}>'.format(
            self.dns_name, self.user, self.label)

    @property
    def link(self):
        """The full URL to this host when deployed, for use in href attributes."""
        return 'http://' + self.basic_url

    @property
    def basic_url(self):
        """This host's URL without scheme, suitable for user display."""
        return self.dns_name + '.cloudlabs.rc.ucl.ac.uk'

    @property
    def status(self):
        """Whether this host is Running, Restarting, or Stopped."""
        return 'Stopped'

    @property
    def auth_type(self):
        """Whether public key or password auth is used for this host."""
        if self.admin_ssh_key:
            return 'Public key'
        else:
            return 'Password'
