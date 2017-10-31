# AzureAutomation-PythonExamples
Examples are from - https://github.com/Diastro/AzureAutomation-PythonExamples

Additions have been made to RunAs/azure-parallel-start-vm.py for personal usage. These are:

* start vm
* stop vm
* select which resource groups to apply to
* select if there's any vm's you want to exclude

# Usage for azure-parallel-start-vm.py

When you schedule the runbook, you need to fill out the parameters like this example:

    Param1: start_vm # start_vm or stop_vm
    Param2: rg-elasticsearch-prod # this is which rg's you want to start/stop vm's in. You can state multiple rg's like this: rg-mysql-prod rg-nginx-prod rg-apache-prod
    Param3: (leave empty by default) # this is which vm's you want to exclude. You can state multiple vm's like this: az-vm-prod-01 az-vm-prod-05
