# Overview
objstore_backup.py uses the [OCI Python SDK](https://oracle-cloud-infrastructure-python-sdk.readthedocs.io/en/latest/) to upload, download, and list objects in an Oracle Cloud Infrastructure Object Storage Bucket

# Setup
## Prerequisites
* Python version 3
* An Oracle Cloud Infrastructure account
* An existing [Object Storage Bucket](https://docs.oracle.com/en-us/iaas/Content/GSG/Tasks/addingbuckets.htm)

## Python Setup
The OCI Module must be installed and can be done either Globally or in a Virtual Environment (Recommended)

### Python Virtual Environment
On your linux machine, as the user running the script, create a python virtual environment and install the OCI python module
```
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install oci
source .venv/bin/activate
```

### Globally 
As the root user:
```
pip install --upgrade pip wheel
pip install oci
```

## OCI API Access
Before using the script, you must create a config file that contains the required credentials for working with Oracle Cloud Infrastructure.

1. Log into OCI with the OCI user that has permissions to the Object Bucket 
2. Open the Profile menu (User menu icon) and click User Settings.
3. Click Add API Key.
    1. In the dialog, select Generate API Key Pair.
    2. Click Download Private Key and save the key to your .oci directory. 
    3. Click Add.

The key is added and the Configuration File Preview is displayed. The file snippet includes required parameters and values you'll need to create your configuration file. Copy and paste the configuration file snippet from the text box into your ~/.oci/config file.

After you paste the file contents, you'll need to update the key_file parameter to the location where you saved your private key file.
    
If your config file already has a DEFAULT profile, you'll need to do one of the following:
* Replace the existing profile and its contents.
* Rename the existing profile.
* Rename this profile to a different name after pasting it into the config file.
The name of the profile, if not DEFAULT should be passed to the scripts `-t CONFIG_PROFILE` flag.

Update the permissions on your downloaded private key file so that only you can view it:
1. Go to the .oci directory where you placed the private key file.
2. Use the command chmod go-rwx ~/.oci/<oci_api_keyfile>.pem to set the permissions on the file.


# Example Usage:
```
usage: objstore_backup.py [-h] -a {upload,download,list} -b BUCKET
                          [-c CONFIG_FILE] [-t CONFIG_PROFILE] [-p PROXY]
                          [-s SRC] [-d DST]

Object Store Filesystem Utilities

Required arguments:
  -a {upload,download,list} : Action
  -b BUCKET                 : Bucket Name

Optional arguments:
  -c CONFIG_FILE        Config File (default=~/.oci/config)
  -t CONFIG_PROFILE     Config file section to use (DEFALUT)
  -p PROXY              Set Proxy (i.e. www-proxy-server.com:80)

Action Specific (upload/download) arguments:
  -s SRC                Source path
  -d DST                Destination path <- Use to avoid overwritting local files
```

## Upload Files/Directories to Object Storage
* Upload Recursive Directory: 
    * `python ./objstore_backup.py -a upload -t cloud-backup-demo -b FILESYSTEM -s /u01/app/datapump`
* Upload Single File: 
    * `python ./objstore_backup.py -a upload -t cloud-backup-demo -b FILESYSTEM -s /u01/app/datapump/db1/file01.dmp`

## List Object Storage Files
* List all Object Storage: 
    * `python ./objstore_upload.py -a list -t cloud-backup-demo -b FILESYSTEM`
* List subset Object Storage: 
    * `python ./objstore_upload.py -a list -t cloud-backup-demo -b FILESYSTEM -s /u01/app/datapump/db1`

## Download
Use the -a list to find the full path of the object storage file, then pass to -s; use -d to place in a different local directory (avoid overwriting)
* Download Recursive Directory: 
    * `python ./objstore_backup.py -a download -t cloud-backup-demo -b FILESYSTEM -s /u01/app/datapump/db1 -d /u01/app/datapump/db1_new`
* Download Single File: 
    * `python ./objstore_backup.py -a upload -t cloud-backup-demo -b FILESYSTEM -s /u01/app/datapump/db1/file01.dmp -d /u01/app/datapump/db1_new/file01.dmp`