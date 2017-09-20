import json
import os
import subprocess
from flask import current_app
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from tempfile import TemporaryDirectory

from ..host_status import HostStatus


class Deployer:
    '''
    Deploys a VM on an Azure subscription using a tenant ID and secret stored
    on the machine running this app. The needed variables can be found on
    Azure's portal:
     * AZURE_TENANT_ID: 'cloudlabs' Azure Active Directory tenant id.
     * AZURE_CLIENT_ID: 'cloudlabs' Azure AD Application Client ID.
     * AZURE_CLIENT_ID: with your Azure AD Application Secret.
     * AZURE_SUBSCRIPTION_ID: UCL RSDG's Azure subscription ID.
    These variables are stored in environment variables and read by Terraform.
    '''
    def __init__(self, app_path=Path.cwd()):
        '''
        Set python-terraform's instance with appropriate full path working dir.
        '''
        self.template_path = Path(app_path, "deployer", "terraform")
        self.tempdir = TemporaryDirectory()
        self.tfstate_path = os.path.join(self.tempdir.name, 'terraform.tfstate')

    def _render(self, host):
        '''
        Terraform's only possible target is a folder and not a file. So we
        need to save the rendered template on a tf file in the terraform
        folder.
        '''
        # try:
        j2_env = Environment(loader=FileSystemLoader(str(self.template_path)))
        rendered_template = j2_env.get_template(
                'terraform.tf_template').render(
                host=host,
                private_key_path=current_app.config['PRIVATE_SSH_KEY_PATH'])
        # # except TemplateNotFound:
        #     print("Template terraform-main.tf_template not found in {}."
        #               .format(template_path))
        #     return
        #     # TODO raise?

        print(rendered_template)

        # try:
        with open(str(Path(self.tempdir.name, "terraform.tf")), "w") as f:
                f.write(rendered_template)
        # except:
        #     # TODO: replace with logging and maybe raise?
        #     print("Error writing terraform's config file.")

    def deploy(self, host):
        '''
        Renders the Terraform template with given user input.
        Then runs "terrraform apply" with appropriate template and displays
        message when it's done.
        '''
        # try:
        self._render(host)
        # except:
        #     # TODO: logging
        #     return "Error when rendering Terraform template."

        host.update(status=HostStatus.deploying,
                    deploy_log='Initialising deployment...\n\n')
        process = self._run_cmd('init', host)
        if process.returncode != 0:
            self._record_result(host, HostStatus.error, 'init', process.returncode)
            return
        host.update(deploy_log=host.deploy_log + '\n\nRunning deployment...\n\n')
        process = self._run_cmd('apply', host)
        if process.returncode == 0:
            self._record_result(host, HostStatus.running)
        else:
            self._record_result(host, HostStatus.error, 'apply', process.returncode)

    def _record_result(self, host, status, command=None, return_code=None):
        """Record the result of a Terraform run in the DB.

        :param host: the host being deployed
        :param status: the result status of the deployment
        :param command: the Terraform command name that was run
            (only required if there was an error)
        :param return_code: the return code of the Terraform command
            (only required if there was an error)
        """
        updates = {
            'status': status
        }
        try:
            with open(self.tfstate_path, 'r') as tf_state:
                updates['terraform_state'] = tf_state.read()
        except IOError:
            pass
        if status is HostStatus.error:
            updates['deploy_log'] = (
                host.deploy_log + '\n\nTerraform {} failed with return code {}\n'.format(
                    command, return_code))
        host.update(**updates)

    def _run_cmd(self, name, host, args=[]):
        '''Run a terraform command for the given host.

        Will append the command's output & stderr to the host's deploy_log.

        :param name: the name of the Terraform command to run
        :param host: the host object being deployed
        :returns: the subprocess object
        '''
        process = subprocess.Popen(['terraform', name, '-no-color'] + args,
                                   cwd=self.tempdir.name,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        for line in process.stdout:
            print(line.decode('utf-8'), end='')
            host.update(deploy_log=host.deploy_log + line.decode('utf-8'))
        process.wait()
        return process

    def destroy(self, host):
        """Remove the given CloudLabs host from the cloud.

        :param host: a Host instance
        """
        if not host.terraform_state:
            host.update(
                status=HostStatus.error,
                deploy_log=host.deploy_log +
                '\n\nUnable to destroy host as no state file present!\n\n')
            return
        # Write Terraform state to file so Terraform can destroy the host
        with open(self.tfstate_path, 'w') as tf_state:
            tf_state.write(host.terraform_state)
        # We need to write a config file and initialise Terraform (TODO: fix this?)
        self._render(host)
        process = self._run_cmd('init', host)
        if process.returncode != 0:
            self._record_result(host, HostStatus.error, 'init', process.returncode)
            return
        # Now we can destroy the host
        process = self._run_cmd('destroy', host, args=['-force'])
        if process.returncode == 0:
            self._record_result(host, HostStatus.defining)
        else:
            self._record_result(host, HostStatus.error, 'destroy', process.returncode)
