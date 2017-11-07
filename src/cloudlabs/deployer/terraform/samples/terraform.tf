# Azure subscription variables
variable "azure_subscription_id" {
}
variable "azure_client_id" {
}
variable "azure_client_secret" {
}
variable "azure_tenant_id" {
}

# Configure Azure provider
provider "azurerm" {
  subscription_id = "${var.azure_subscription_id}"
  client_id       = "${var.azure_client_id}"
  client_secret   = "${var.azure_client_secret}"
  tenant_id       = "${var.azure_tenant_id}"
  # Don't upgrade to newer versions automatically
  version = "~> 0.1"
}

# create a resource group if it doesn't exist
resource "azurerm_resource_group" "rg" {
    name = "uclsamplerg"
    location = "ukwest"
}

# create virtual network
resource "azurerm_virtual_network" "vnet" {
    name = "tfvnet"
    address_space = ["10.0.0.0/16"]
    location = "ukwest"
    resource_group_name = "${azurerm_resource_group.rg.name}"
}

# create subnet
resource "azurerm_subnet" "subnet" {
    name = "tfsub"
    resource_group_name = "${azurerm_resource_group.rg.name}"
    virtual_network_name = "${azurerm_virtual_network.vnet.name}"
    address_prefix = "10.0.2.0/24"
    #network_security_group_id = "${azurerm_network_security_group.nsg.id}"
}

# create public IPs
resource "azurerm_public_ip" "ip" {
    name = "tfip"
    location = "ukwest"
    resource_group_name = "${azurerm_resource_group.rg.name}"
    public_ip_address_allocation = "dynamic"
    domain_name_label = "uclsample"

    tags {
        environment = "staging"
    }
}

# create network interface
resource "azurerm_network_interface" "ni" {
    name = "tfni"
    location = "ukwest"
    resource_group_name = "${azurerm_resource_group.rg.name}"

    ip_configuration {
        name = "ipconfiguration"
        subnet_id = "${azurerm_subnet.subnet.id}"
        private_ip_address_allocation = "static"
        private_ip_address = "10.0.2.5"
        public_ip_address_id = "${azurerm_public_ip.ip.id}"
    }
}

# create storage account
resource "azurerm_storage_account" "storage" {
    name = "fa0e30c92f4f5ca69c256850"
    resource_group_name = "${azurerm_resource_group.rg.name}"
    location = "ukwest"
    account_replication_type = "LRS"
    account_tier = "Standard"

    tags {
        environment = "staging"
    }
}

# create storage container
resource "azurerm_storage_container" "storagecont" {
    name = "vhd"
    resource_group_name = "${azurerm_resource_group.rg.name}"
    storage_account_name = "${azurerm_storage_account.storage.name}"
    container_access_type = "private"
    depends_on = ["azurerm_storage_account.storage"]
}



# create virtual machine
resource "azurerm_virtual_machine" "vm" {
    name = "uclsamplevm"
    location = "ukwest"
    resource_group_name = "${azurerm_resource_group.rg.name}"
    network_interface_ids = ["${azurerm_network_interface.ni.id}"]
    vm_size = "Standard_A6"

    storage_image_reference {
        publisher = "Canonical"
        offer = "UbuntuServer"
        sku = "16.04-LTS"
        version = "latest"
    }

    storage_os_disk {
        name = "myosdisk"
        vhd_uri = "${azurerm_storage_account.storage.primary_blob_endpoint}${azurerm_storage_container.storagecont.name}/myosdisk.vhd"
        caching = "ReadWrite"
        create_option = "FromImage"
    }

    os_profile {
        computer_name = "sample"
        admin_username = "anastasis"
        
        admin_password = "Password!123"
        
    }

    os_profile_linux_config {
      disable_password_authentication = true
      ssh_keys = [{
            path     = "/home/anastasis/.ssh/authorized_keys"
            key_data = "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQC1kFcLSvCut62wCdq/oWXbbjLAXnKaKzzJAGYoYq0994nqWlhyUfTdWPt0SDQHKJZ9OMevyFB9qf0Qfuzd7+f7bsrUHuaaEavK3gMo+j1iKwGaXO36za9fwKMXiWnXFkgmUNJ51gdSKZjb//f9LicXIr4qVTfk+d6MBTBJmLxDSKdl+Sl3pK1K2YwI+2KQwj9t3udf/B8Tq/D1G617LFe+3EitByIpJhz6CnBXWv9raZWqUNeHQ2RqwgfHWJHztA3zhecDH4HizqW8DuPoH+pGQHwvx0nKYp+/XoUMyTfZ8bMtbS8PFRI6EXtYkG/K8v6orRa6Rwtd4C4zL0q228mz ageorgou@rits-102.rits-isd.ucl.ac.uk"
          },{
            path     = "/home/anastasis/.ssh/authorized_keys"
            key_data = "${file("/Users/ageorgou/.ssh/id_rsa.pub")}"
          }
      ]
    }

    connection {
        host = "uclsample.ukwest.cloudapp.azure.com"
        user = "anastasis"
        type = "ssh"
        private_key = "${file("/Users/ageorgou/.ssh/id_rsa")}"
        timeout = "1m"
        agent = false
    }

    provisioner "remote-exec" {
        inline = [
          
              "sudo apt-get update",
              "sudo apt-get install docker.io -y",
              "git clone https://github.com/UCL-CloudLabs/docker-sample -b levine repo",
              "cd repo",
              "sudo docker build -t web-app .",
              "sudo docker run -d -e AZURE_URL=sample.ukwest.cloudapp.azure.com -p 5006:5006 web-app",
        ]
    }

    tags {
        environment = "staging"
    }
}