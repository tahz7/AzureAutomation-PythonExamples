"""
Python support for Azure automation is now public preview!

Azure automation documentation : https://aka.ms/azure-automation-python-documentation
Azure Python SDK documentation : http://azure-sdk-for-python.readthedocs.io/en/latest/index.html

"""
import sys
import threading
from datetime import datetime
import calendar
from collections import defaultdict

import automationassets
from azure.mgmt.compute import ComputeManagementClient


def _args():
    """ set arguments here """

    start_stop = sys.argv[1] # param_arg1: start_vm or stop_vm
    resource_groups = sys.argv[2:] # param arg2: rg1 rg2 rg3
    exclude_vm = [] # param_arg3: !_vm1 !_vm2

    for vm in sys.argv[2:]:
        if vm.startswith('!_'):
            resource_groups.remove(vm)
            vm = vm[2:]
            exclude_vm.append(vm)

    return start_stop, resource_groups, exclude_vm


def get_automation_runas_credential(runas_connection):
    """ Returns credentials to authenticate against Azure resource manager """
    from OpenSSL import crypto
    from msrestazure import azure_active_directory
    import adal

    # Get the Azure Automation RunAs service principal certificate
    cert = automationassets.get_automation_certificate("AzureRunAsCertificate")
    pks12_cert = crypto.load_pkcs12(cert)
    pem_pkey = crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                      pks12_cert.get_privatekey())

    # Get run as connection information for the Azure Automation service principal
    application_id = runas_connection["ApplicationId"]
    thumbprint = runas_connection["CertificateThumbprint"]
    tenant_id = runas_connection["TenantId"]

    # Authenticate with service principal certificate
    resource = "https://management.core.windows.net/"
    authority_url = ("https://login.microsoftonline.com/" + tenant_id)
    context = adal.AuthenticationContext(authority_url)
    return azure_active_directory.AdalAuthentication(
        lambda: context.acquire_token_with_client_certificate(
            resource,
            application_id,
            pem_pkey,
            thumbprint)
    )


def get_compute_client():
    """ Authenticate to Azure using the Azure Automation
     RunAs service principal
    """
    runas_connection = automationassets.get_automation_connection(
        "AzureRunAsConnection")
    azure_credential = get_automation_runas_credential(runas_connection)

    compute_client = ComputeManagementClient(
        azure_credential,
        str(runas_connection["SubscriptionId"])
    )

    return compute_client


def stop_start_vm(compute_client, rgn, vm_name, action):
    """ start or stop vm's """

    print "{} {}...".format(action, vm_name)
    if action == 'start_vm':
        async_vm_status = compute_client.virtual_machines.start(rgn, vm_name)
    else:
        async_vm_status = compute_client.virtual_machines.power_off(rgn,
                                                                    vm_name)
    async_vm_status.wait()
    print "{} Done".format(vm_name)
    sys.stdout.flush()


# sort out arguments
start_stop, resource_groups, exclude_vm = _args()

# exit if it's the weekend as we don't need to start any vm
today = datetime.today()
if today.weekday() in [5, 6] and start_stop == 'start_vm':
    raise SystemExit("It's {} which is the weekend, so not doing anything "
                     "today!".format(calendar.day_name[today.weekday()]))


compute_client = get_compute_client()
# dict for rg mapped to their vm list
vm_list = defaultdict(dict)

for rg in resource_groups:
    rg_vm_list = compute_client.virtual_machines.list(resource_group_name=rg)
    vm_list[rg] = [vm.name for vm in rg_vm_list if vm.name not in exclude_vm]

# restart vm's
threads = []
for rg, vm_group in vm_list.iteritems():
    for vm in vm_group:
        thread = threading.Thread(target=stop_start_vm,
        args=[compute_client, rg, vm, start_stop])
        thread.start()
        threads.append(thread)
        sys.stdout.flush()

print "Waiting on VMs operation to complete..."

for t in threads:
    t.join()

print "All thread joined."
