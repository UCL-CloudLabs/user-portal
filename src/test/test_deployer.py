import os
import requests
import pytest
from time import sleep
from pathlib import Path
from haikunator import Haikunator
from cloudlabs.app import create_app
from cloudlabs.deployer.deployer import Deployer
from cloudlabs.models import Host, SshKey, User


class TestDeployer:
    '''
    Test the app's Deployer class.
    '''
    @pytest.fixture
    def user(self):
        ucl_id = self._haikunate()[0:7]
        domain = self._haikunate('.')
        kwargs = {
            'ucl_id': ucl_id,
            'email': ucl_id + '@' + domain,
            'name': self._haikunate(),
            'upi': ucl_id
        }
        User.create(**kwargs)
        return True

    @pytest.fixture
    def ssh_key(self, user, resource_name, public_key):
        SshKey.create(
            user_id=1,
            label=resource_name,
            public_key=public_key)
        return True

    @pytest.fixture
    def deployer(self):
        return Deployer(Path('cloudlabs').absolute())

    @pytest.fixture
    def resource_name(self):
        return self._haikunate()

    @pytest.fixture
    def dnsname(self):
        return self._haikunate()

    @pytest.fixture
    def app(self):
        return create_app(
            os.getenv('APP_SETTINGS', 'cloudlabs.config.Config'))

    @pytest.fixture
    def public_key(self):
        '''
        Read public key contents from encrypted file, ignore newline
        '''
        with open(str(Path('test/id_rsa_travis.pub').absolute())) as f:
            public_key = f.read().rstrip('\n')
        return public_key

    @pytest.fixture
    def private_key_path(self):
        return Path('test/id_rsa_travis').absolute()

    @pytest.fixture
    def host(self, app, deployer, dnsname, public_key, private_key_path,
             resource_name, ssh_key):
        '''
        Helper method to create a VM with randome username/passwd and test
        SSH keys.
        '''
        # First we need to create a key with an ID so we can point to it
        # TODO: create test DB setup?

        fields = {
            'user_id': 1,
            'label': self._haikunate(),
            'dns_name': dnsname,
            'description': self._haikunate(),
            'admin_username': self._haikunate(),
            'terraform_state': self._haikunate(),
            'git_repo':
                'https://github.com/UCL-CloudLabs/docker-sample.git -b levine',
            'port': 5006,
            'admin_ssh_key_id': 1,
            'admin_password': self._haikunate('!')
        }
        yield Host.create(**fields)
        deployer.destroy()

    def test_deployer_config(self, app, deployer):
        '''
        Check the path where the terraform files are is setup correctly.
        '''
        assert deployer.template_path == Path(
            'cloudlabs/deployer/terraform').absolute()

    def test_deployer(self, app, resource_name, deployer, dnsname, host):
        '''
        Create a test host with made up parameters, deploy on azure and ping.
        '''
        deployer.deploy(host)
        # Wait for 10 secs so we make sure app has had the time to be deployed.
        sleep(10)
        # Sample URL is exposing the webapp on port 5000
        url = "http://{}.ukwest.cloudapp.azure.com:5006".format(dnsname)
        # Check website is live
        response = requests.get(url)
        assert 200 == response.status_code

    def _haikunate(self, delimiter=''):
        '''
        Helper method to create random strings to use on the Terraform file.
        '''
        haiku = Haikunator()
        return haiku.haikunate(delimiter=delimiter, token_length=3)
