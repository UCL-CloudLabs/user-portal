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
        # Randomise ucl_id a bit more. After running several tests locally,
        # random user names start repeating and breaking the tests.
        # Adding some more randomness.
        ucl_id = self._haikunate()[0:5] + self._haikunate()[-2:]
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
        with open(str(Path('test/id_rsa_travis_azure.pub').absolute())) as f:
            public_key = f.read().rstrip('\n')
        return public_key

    @pytest.fixture
    def private_key_path(self):
        return Path('test/id_rsa_travis_azure').absolute()

    # TODO: test with windows too
    # {'publisher': 'MicrosoftWindowsServer',
    #  'offer': 'WindowsServer',
    #  'sku': '2012-R2-Datacenter',
    #  'version': 'latest'},
    @pytest.fixture()
    def os(self):
        os.publisher = 'Canonical'
        os.offer = 'UbuntuServer'
        os.sku = '16.04-LTS'
        os.version = 'latest'
        return os

    @pytest.fixture(params=['Standard_A1_v2',
                            'Standard_A4_v2',
                            'Standard_A4m_v2'])
    def vm_type(self, request):
        return request.param

    @pytest.fixture
    def host(self, app, deployer, dnsname, public_key, private_key_path,
             resource_name, ssh_key, os, vm_type):
        '''
        Helper method to create a VM with random username/passwd and test
        SSH keys.
        '''
        # First we need to create a key with an ID so we can point to it
        # TODO: create test DB setup?

        fields = {
            'user_id': 1,
            'label': self._haikunate(),
            'base_name': dnsname,
            'description': self._haikunate(),
            'admin_username': self._haikunate(),
            'terraform_state': self._haikunate(),
            'git_repo':
                'https://github.com/UCL-CloudLabs/docker-sample.git -b levine',
            'port': 5006,
            'admin_ssh_key_id': 1,
            'admin_password': self._haikunate('!'),
            'vm_type': vm_type,
            'os_publisher': os.publisher,
            'os_offer': os.offer,
            'os_sku': os.sku,
            'os_version': os.version
        }
        host = Host.create(**fields)
        yield host
        deployer.destroy(host)

    def test_deployer_config(self, app, deployer):
        '''
        Check the path where the terraform files are is setup correctly.
        '''
        assert deployer.template_path == Path(
            'cloudlabs/deployer/terraform').absolute()

    def test_deployer(self, app, resource_name, deployer, host):
        '''
        Create a test host with made up parameters, deploy on azure and ping.
        '''
        deployer.deploy(host)
        # Wait for 10 secs so we make sure app has had the time to be deployed.
        sleep(10)
        # URL and port are available through the host's link property
        url = host.underlying_url
        # Check website is live
        response = requests.get(url)
        assert 200 == response.status_code

    def _haikunate(self, delimiter=''):
        '''
        Helper method to create random strings to use on the Terraform file.
        '''
        haiku = Haikunator()
        return haiku.haikunate(delimiter=delimiter, token_length=3)
