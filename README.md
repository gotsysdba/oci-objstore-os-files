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
On your linux machine, as the user running the script, create a python virtual environment and install the OCI python module.  This is a one-off setup:
```
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip wheel
pip install oci
source .venv/bin/activate
```

To ensure that the above virtual environment is always used by the running OS user, activate with the users shell "rc" file; for example on bash:

Add to ~/.bashrc
```
# Source python virtual environment
if [ -f $HOME/.venv/bin/activate ]; then
        . $HOME/.venv/bin/activate
fi
```

### Globally 
If not using the Python Virtual Environment,to install the OCI module globally, as the root user:
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

### Advanced Configuration
The following script input variables can be specified in the config file to avoid having to input on the command line:
* bucket
* proxy
* src
* dst

For example:
```
[DEFAULT]
compartment=ocid1.compartment.oc1..
user=ocid1.user.oc1..
fingerprint=<fingerpring>
tenancy=ocid1.tenancy.oc1..
region=<region>
key_file=~/.oci/key.pem
proxy=myproxy-host.example.com:4889
bucket=FILESYSTEM
src=/u01/app/datapump/db1
dst=/u01/app/datapump/db1_new
```

Additionally, multiple profiles can be used for standard variations to the inputs.  For common configurations, such as the user, tenancy, fingerprint, proxy, etc. use `DEFAULT`; create new profiles for the variables:

For example:
```
[DEFAULT]
compartment=ocid1.compartment.oc1..
user=ocid1.user.oc1..
fingerprint=<fingerpring>
tenancy=ocid1.tenancy.oc1..
region=<region>
key_file=~/.oci/key.pem
proxy=myproxy-host.example.com:4889

[PROD]
bucket=PROD_FS
src=/u01/app/datapump/prod
dst=/u01/app/datapump/prod_new

[DEV]
bucket=DEV_FS
src=/u01/app/datapump/dev
dst=/u01/app/datapump/dev_new
```

Use `-t PROD` or `-t DEV` in the script to consume and set the script inputs.  What is not found in those configuration profiles will be obtained from the `DEFAULT`.

# Example Usage:
```
usage: objstore_backup.py [-h] -a {upload,download,list} -b BUCKET
                          [-c CONFIG_FILE] [-t CONFIG_PROFILE] [-p PROXY]
                          [-s SRC] [-d DST]

Object Store Filesystem Utilities

Required arguments:
  -a {upload,download,delete,list} : Action
  -b BUCKET                        : Bucket Name

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
    * `python3 ./objstore_backup.py -a upload -t cloud-backup-demo -b FILESYSTEM -s /u01/app/datapump`
* Upload Single File: 
    * `python3 ./objstore_backup.py -a upload -t cloud-backup-demo -b FILESYSTEM -s /u01/app/datapump/db1/file01.dmp`

## List Object Storage Files
* List all Object Storage: 
    * `python3 ./objstore_upload.py -a list -t cloud-backup-demo -b FILESYSTEM`
* List subset Object Storage: 
    * `python3 ./objstore_upload.py -a list -t cloud-backup-demo -b FILESYSTEM -s /u01/app/datapump/db1`

## Download
Use the -a list to find the full path of the object storage file, then pass to -s; use -d to place in a different local directory (avoid overwriting)
* Download Recursive Directory: 
    * `python3 ./objstore_backup.py -a download -t cloud-backup-demo -b FILESYSTEM -s /u01/app/datapump/db1 -d /u01/app/datapump/db1_new`
* Download Single File: 
    * `python3 ./objstore_backup.py -a download -t cloud-backup-demo -b FILESYSTEM -s /u01/app/datapump/db1/file01.dmp -d /u01/app/datapump/db1_new/file01.dmp`

## Delete
Use the -a list to find the full path of the object storage file, then pass to -s
* Delete Recursive Directory: 
    * `python3 ./objstore_backup.py -a delete -t cloud-backup-demo -b FILESYSTEM -s /u01/app/datapump/db1`
* Delete Single File: 
    * `python3 ./objstore_backup.py -a delete -t cloud-backup-demo -b FILESYSTEM -s /u01/app/datapump/db1/file01.dmp`
