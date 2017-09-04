import json
import os
import re
import subprocess
import uuid
from flask import current_app
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from python_terraform import Terraform
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
    TODO: For now these are stored in variables.tf, but they'll be moved to an
    Azure key vault.
    '''
    def __init__(self, app_path=Path.cwd()):
        '''
        Set python-terraform's instance with appropriate full path working dir.
        '''
        self.template_path = Path(app_path, "deployer", "terraform")
        self.tempdir = TemporaryDirectory()
        self.tfstate_path = self.tempdir.name
        self.tf = Terraform(working_dir=self.tfstate_path)

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
            names=self.resource_names(host),
            private_key_path=current_app.config['PRIVATE_SSH_KEY_PATH'])
        # # except TemplateNotFound:
        #     print("Template terraform-main.tf_template not found in {}."
        #               .format(template_path))
        #     return
        #     # TODO raise?

        print(rendered_template)

        # try:
        with open(str(Path(self.tfstate_path, "terraform.tf")), "w") as f:
                f.write(rendered_template)
        # except:
        #     # TODO: replace with logging and maybe raise?
        #     print("Error writing terraform's config file.")

    def resource_names(self, host):
        """Generate names for cloud resources for the given host.

        A deployed host requires various resources alongside the bare VM, such
        as networking, storage, containers, etc. Different providers have
        different constraints on these names, so we don't want to hardcode this
        within the Host class. Instead this method returns a dictionary with
        suitable names based on a given host configuration, providing a hook to
        abstract provider requirements.

        The resulting dictionary is designed to be passed as the 'names'
        parameter to the Terraform template in self._render.
        """
        base_name = 'UCLCloudLabs' + re.sub(r'[^a-zA-Z0-9]', '', host.dns_name)
        return {
            'resource_group': base_name + 'rg',
            'dns_name': base_name,
            'storage': uuid.uuid5(uuid.NAMESPACE_DNS, host.basic_url),
            'vm': base_name + 'vm',
        }

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
        state_path = os.path.join(self.tfstate_path, 'terraform.tfstate')
        try:
            with open(state_path, 'r') as tf_state:
                updates['terraform_state'] = tf_state.read()
        except IOError:
            pass
        if status is HostStatus.error:
            updates['deploy_log'] = (
                host.deploy_log + '\n\nTerraform {} failed with return code {}\n'.format(
                    command, return_code))
        host.update(**updates)

    def _run_cmd(self, name, host):
        '''Run a terraform command for the given host.

        Will append the command's output & stderr to the host's deploy_log.

        :param name: the name of the Terraform command to run
        :param host: the host object being deployed
        :returns: the subprocess object
        '''
        process = subprocess.Popen(['terraform', name, '-no-color'],
                                   cwd=self.tfstate_path,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.STDOUT)
        for line in process.stdout:
            print(line.decode('utf-8'), end='')
            host.update(deploy_log=host.deploy_log + line.decode('utf-8'))
        process.wait()
        return process

    def destroy(self, resource=None):
        '''
        Deletes given Terraform resource.
        It has to make sure there is a Terraform state containing the resource
        that will be destroyed.
        After applying a plan, Terraform saves the state on
        "terraform.tfstate". This is a JSON file that contains the list of
        resources deployed and their status.
        '''
        tf_state = Path(self.tempdir.name, 'terraform.tfstate')

        if tf_state.exists():
            if resource:
                with open(tf_state) as f:
                    tf_data = json.load(f)
                try:
                    res_label = tf_data['modules'][0]['resources'][resource]
                except KeyError:
                    print("Resource not found in Terraform state. The "
                          "available resources for destroying are {}.".format(
                           ', '.join(
                             [r for r in tf_data['modules'][0]['resources']])))
                    # TODO raise
                    return
                return_code, stdout, stderr = self.tf.destroy(
                                                        res_label,
                                                        capture_output=False
                                                        )
            else:
                print("Destroying all resources...")
                return_code, stdout, stderr = self.tf.destroy(
                                                        capture_output=False)

            if return_code == 0:  # All went well
                return ("Resource {} destroyed successfully.".format(resource))
            else:
                # TODO raise
                return ("Something went wrong when destroying {}: {}".format(
                                                                    resource,
                                                                    stderr))
        else:
            print("Terraform state does not exist in {}".format(tf_state))

    def refresh(self):
        '''
        User Terraform to update the current state file against real resources.
        '''
        # First refresh state
        return_code, stdout, stderr = self.tf.refresh()

        if return_code == 0:  # All went well
            return ("Local Terraform state successfully updated.")
        else:
            # TODO raise
            return ("Something went wrong when updating state: {}".format(
                                                                       stderr))
