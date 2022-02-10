# Copyright (c) 2016, 2022, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.

import oci
import os, argparse, stat
from multiprocessing import Process
import glob

##########################################################################
# Print header centered
##########################################################################
def print_header(msg):
    chars = int(90)
    print("")
    print('#' * chars)
    print("#" + msg.center(chars - 2, " ") + "#")
    print('#' * chars)

##############################################################################
# get_namespace
##############################################################################
def get_namespace(client):
  print_header("Connecting to Object Storage")
  try:
    namespace = client.get_namespace(retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY).data
    print("Succeeded - Namespace = {}".format(namespace))
  except Exception as e:
      print("\nError connecting to object storage - {}".format(e))
      raise SystemExit
  return namespace

##############################################################################
# list_object_storage
##############################################################################
def list_object_storage(client, namespace, bucket, src=None):
  object_dict = {}
  next_starts_with = None
  while True:
    response = client.list_objects(namespace, bucket, start=next_starts_with, prefix=None, fields='size', retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
    next_starts_with = response.data.next_start_with
    for object_file in response.data.objects:
      if src and not object_file.name.startswith(src):
        continue
      object_dict[object_file.name] = object_file.size
    if not next_starts_with:
      break

  return object_dict

##############################################################################
# upload_to_object_storage
##############################################################################
def upload_to_object_storage(client, namespace, bucket, path):
  try:
    with open(path, "rb") as in_file:
      # name is the full path in ObjectStore; change as required
      name = path     
      client.put_object(namespace, bucket, name, in_file)
      print("Finished uploading {}".format(path))
  except PermissionError:
    print("Failed to upload {} - Unable to read local file".format(path))
  except FileNotFoundError:
    print("Failed to upload {} - File Not Found".format(path))
  except OSError as e:
    print("Failed to upload {} - {}".format(path, e))

##############################################################################
# download_from_object_storage
##############################################################################
def download_from_object_storage(client, namespace, bucket, path, out_file=None):
  get_obj = client.get_object(namespace, bucket, path)
  if out_file:
    out_file = os.path.normpath(out_file+path)
  else:
    out_file = path

  os.makedirs(os.path.dirname(out_file), exist_ok=True)

  with open(out_file, 'wb') as f:
    for chunk in get_obj.data.raw.stream(1024 * 1024, decode_content=False):
        f.write(chunk)
    print("Finished downloading {} to {}".format(path, out_file))

##############################################################################
# MAIN
##############################################################################
if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Object Store Filesystem Utilities')
  parser.add_argument('-a', required=True,  dest='action', choices=['upload', 'download','list'], help="Action")
  parser.add_argument('-b', required=True,  dest='bucket', help='Bucket Name')
  parser.add_argument('-c', required=False, dest='config_file', help="Config File (default=~/.oci/config)")
  parser.add_argument('-t', required=False, dest='config_profile', help='Config file section to use (DEFAULT)')
  parser.add_argument('-p', required=False, dest='proxy', help='Set Proxy (i.e. www-proxy-server.com:80) ')
  parser.add_argument('-s', required=False, default="", dest='src', help="Source path")
  parser.add_argument('-d', required=False, default="", dest='dst', help="Destination path")

  args = parser.parse_args()

  # Potentially will modify later
  src = args.src

  # Update Variables based on the parameters
  config_file = (args.config_file if args.config_file else oci.config.DEFAULT_LOCATION)
  config_profile = (args.config_profile if args.config_profile else oci.config.DEFAULT_PROFILE)

  try:
    config = oci.config.from_file(
      (config_file if config_file else oci.config.DEFAULT_LOCATION),
      (config_profile if config_profile else oci.config.DEFAULT_PROFILE))
  except Exception as e:
    print(e)
    raise SystemExit

  # Establish the ObjStorage Client
  object_storage_client = oci.object_storage.ObjectStorageClient(config)
  if args.proxy:
    object_storage_client.base_client.session.proxies = {'https': args.proxy}

  namespace = get_namespace(object_storage_client)

  filenames = {}
  if args.action == 'list':
    print_header("Listing Objects in {} Bucket".format(args.bucket))
    filenames = list_object_storage(object_storage_client, namespace, args.bucket, src)
    for file in filenames:
      print(str('{:10,.0f}'.format(filenames[file])).rjust(10) + " - " + str(file))

  if args.action == 'download':
    print_header("Downloading from Object Storage")
    filenames = list_object_storage(object_storage_client, namespace, args.bucket, src)
    for file in filenames:
      download_from_object_storage(object_storage_client, namespace, args.bucket, file, args.dst)

  if args.action == 'upload':
    print_header("Uploading to Object Storage")
    if os.path.isdir(src):
      if not src.endswith('/'):
        src = src + '/'
      print('Getting files in {}'.format(src))
      for file in glob.glob(src + "**/**", recursive=True):
        filenames[os.path.abspath(file)] = "local"
    else:
      filenames[os.path.abspath(src)] = "local"

    proc_list = []
    for filePath in filenames:
      if os.path.isdir(filePath):
        continue
      # Skip socket files
      mode = os.stat(filePath).st_mode
      if stat.S_ISSOCK(mode) or stat.S_ISFIFO(mode):
        continue

      full_path=os.path.abspath(filePath)
      print("Starting upload for {}".format(full_path))
      # Playing around with parallelism... to serialise, uncomment below and comment out everything after
      # upload_to_object_storage(object_storage_client, namespace, args.bucket, full_path)
      p = Process(target=upload_to_object_storage, args=(object_storage_client, namespace, args.bucket, full_path))
      p.start()
      proc_list.append(p)

    for job in proc_list:
        job.join()