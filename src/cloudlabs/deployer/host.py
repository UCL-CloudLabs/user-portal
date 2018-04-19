class Host:
    '''
    Contains all variables introduced by the user used to create a VM in Azure.
    '''
    def __init__(self, name=None, dnsname=None, username=None, passwd=None,
                 public_key=None, private_key_path=None, os_offer=None,
                 os_sku=None, os_version=None, vm_type=None):
        self.name = name
        self.dnsname = dnsname
        self.username = username
        self.passwd = passwd
        self.public_key = public_key
        self.private_key_path = private_key_path
        self.os_offer = os_offer
        self.os_sku = os_sku
        self.os_version = os_version
        self.vm_type = vm_type
