# Using NDScheduler on MS Windows

This example describe the installation process to run NDScheduler on Microsoft Windows.

It is possible to run the scheduler from the command line (development mode) and it also describes the possibilty to run the NDScheduler as a Windows service.

The description uses Miniconda as Python environment

MS SQL Server

TODO remove simple_scheduler_win from setup.py and MANIFEST.in


## Installation


```cmd
conda create -n ndscheduler python=3.6
conda activate ndscheduler
cd D:\application\VatSchedulerService

conda install pywin32
python c:\Miniconda3\envs\ndscheduler\Scripts\pywin32_postinstall.py -install

rem install as local dependency
pip install ndscheduler

rem used for MS SQL Server
pip install pyodbc

rem full path
setx /M PYTHONPATH "C:\ndscheduler"
rem Add c:\Miniconda3\envs\ndscheduler to PATH
setx /M PATH "c:\Miniconda3\envs\ndscheduler;%PATH%"

setx /M NDSCHEDULER_SETTINGS_MODULE=simple_scheduler_win.settings
```





## Start from command line (development)

## Creating a NDScheduler Windows Service (production)

## Using MS SQL Server




# VatSchedulerService



## Install the service


Change to application directory

Start command shell as **administrator**
```cmd
activate vatscheduler
cd D:\application\VatSchedulerService
python archive_scheduler\service.py --startup auto --username voestalpine\admin_tn63 --password Pa55W0rd install
deactivate
```

## Start the service

```cmd
python starter.py start
```


## Remove the service

```cmd
activate TbkLastPassSyncEnv
python starter.py stop
python starter.py remove
deactivate
```