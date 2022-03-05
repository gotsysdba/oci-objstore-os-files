#!/bin/env python3

# Copyright (c) 2016, 2022, Oracle and/or its affiliates.  All rights reserved.
# This software is dual-licensed to you under the Universal Permissive License (UPL) 1.0 as shown at https://oss.oracle.com/licenses/upl or Apache License 2.0 as shown at http://www.apache.org/licenses/LICENSE-2.0. You may choose either license.
import oci
import os, argparse, stat
import glob, time, math, multiprocessing
from datetime import timedelta
from oci.object_storage.transfer.constants import MEBIBYTE

_success = 1
##########################################################################
# Print header centered
##########################################################################
def print_header(msg):
    chars = int(90)
    print("")
    print('#' * chars)
    print("#" + msg.center(chars - 2, " ") + "#")
    print('#' * chars)


##########################################################################
# Print header centered
##########################################################################
def set_value(key, arg, config):
  value = arg
  if not arg:
    try:
      value = config[key]
    except KeyError:
      value = None
  return value


##############################################################################
# get_namespace
##############################################################################
def get_namespace(client):
  print_header("Connecting to Object Storage")
  try:
    namespace = client.get_namespace().data
    print("Succeeded - Namespace = {}".format(namespace))
  except Exception as e:
      raise SystemExit("\nError connecting to object storage - {}".format(e))
  return namespace


##############################################################################
# list_object_storage
##############################################################################
def list_object_storage(client, namespace, bucket, src=None):
  object_dict = {}
  next_starts_with = None
  while True:
    try:
      response = client.list_objects(namespace, bucket, start=next_starts_with, prefix=None, fields='size')
    except Exception as e:
      raise SystemExit(e.message)
    next_starts_with = response.data.next_start_with
    for object_file in response.data.objects:
      if src and not object_file.name.startswith(src):
        continue
      object_dict[object_file.name] = object_file.size
    if not next_starts_with:
      break

  return object_dict

##############################################################################
# delete_from_object_storage
##############################################################################
def delete_from_object_storage(client, namespace, bucket, path):
  print("Deleting {} from {}".format(path, bucket), end=": ", flush=True)
  start_time = time.time()
  client.delete_object(namespace, bucket, path)
  print(str(timedelta(seconds=time.time() - start_time)))

##############################################################################
# upload_to_object_storage
##############################################################################
def upload_to_object_storage(client, namespace, bucket, path, cpu=1):
  global _success
  # Note using UploadManager instead of put_object for multipart
  file_size = os.stat(path).st_size
  if file_size > (1024 * MEBIBYTE):
    part_bytes = math.floor(file_size/(35*cpu))
  else:
      part_bytes = file_size

  try:
    part_count = round(file_size/part_bytes)
  except ZeroDivisionError:
    part_count = 1

  try:
    print("Uploading {} [{} part(s)]".format(path,part_count), end=": ", flush=True)
    start_time = time.time()
    client.upload_file(namespace, bucket, path, path, part_size=part_bytes)
    print(str(timedelta(seconds=time.time() - start_time)))
  except PermissionError:
    print("Failed - Unable to read local file")
    _success = 0
  except FileNotFoundError:
    print("Failed - File Not Found")
    _success = 0
  except OSError as e:
    print("Failed - {}".format(e))
    _success = 0

##############################################################################
# download_from_object_storage
##############################################################################
def download_from_object_storage(client, namespace, bucket, src, path, dst=None):
  global _success
  base = path.replace(src,'')
  if not base:
    base = os.path.basename(path)

  try:
    dst = os.path.normpath(dst+base)
  except:
    dst = os.path.normpath('./'+base)
  print("Downloading {} to {}".format(path, dst), end=": ", flush=True)

  try:
    os.makedirs(os.path.dirname(dst), exist_ok=True)
  except FileNotFoundError:
    pass

  try:
    get_obj = client.get_object(namespace, bucket, path)
  except Exception as e:
    print("Failed - {}".format(e.message))
    _success = 0
    return

  start_time = time.time()
  with open(dst, 'wb') as f:
    for chunk in get_obj.data.raw.stream(1024 * 1024, decode_content=False):
        f.write(chunk)
    print(str(timedelta(seconds=time.time() - start_time)))

##############################################################################
# MAIN
##############################################################################
if __name__ == "__main__":
  start_time = time.time()
  parser = argparse.ArgumentParser(description='Object Store Filesystem Utilities')
  parser.add_argument('-a', required=True,  dest='action', choices=['upload', 'download','list','delete'], help="Action")
  parser.add_argument('-b', required=False, default=None, dest='bucket', help='Bucket Name')
  parser.add_argument('-c', required=False, dest='config_file', help="Config File (default=~/.oci/config)")
  parser.add_argument('-t', required=False, dest='config_profile', help='Config file section to use (DEFAULT)')
  parser.add_argument('-p', required=False, default=None, dest='proxy', help='Set Proxy (i.e. www-proxy-server.com:80) ')
  parser.add_argument('-s', required=False, default=None, dest='src', help="Source path")
  parser.add_argument('-d', required=False, default=None, dest='dst', help="Destination path")
  args = parser.parse_args()

  # Update Variables based on the parameters
  config_file = (args.config_file if args.config_file else oci.config.DEFAULT_LOCATION)
  config_profile = (args.config_profile if args.config_profile else oci.config.DEFAULT_PROFILE)

  try:
    config = oci.config.from_file(
      (config_file if config_file else oci.config.DEFAULT_LOCATION),
      (config_profile if config_profile else oci.config.DEFAULT_PROFILE))
  except Exception as e:
    raise SystemExit(e)

  # Test for input overrides and config values
  bucket = set_value('bucket', args.bucket, config)
  proxy  = set_value('proxy', args.proxy, config)
  src    = set_value('src', args.src, config)
  dst    = set_value('dst', args.dst, config)

  if not bucket:
    raise SystemExit('-b <bucket> is requiered')
  if args.action == 'upload' and not src:
    raise SystemExit('For -a upload, -s <src> is required')
  if args.action == 'download' and not src:
    raise SystemExit('For -a download, -s <src> is required')
    
  # Establish the ObjStorage Client
  object_storage_client = oci.object_storage.ObjectStorageClient(config, retry_strategy=oci.retry.DEFAULT_RETRY_STRATEGY)
  if proxy:
    object_storage_client.base_client.session.proxies = {'https': proxy}

  namespace = get_namespace(object_storage_client)

  # Get a list of files in the bucket (this also verifies the existance of bucket)
  objects = {}
  objects = list_object_storage(object_storage_client, namespace, bucket, src)

  # Set successful 
  _success=1
  if args.action == 'list':
    print_header("Listing Objects in {} Bucket".format(bucket))
    for file in objects:
      print(str('{:10,.0f}'.format(objects[file])).rjust(10) + " - " + str(file))

  if args.action == 'delete':
    print_header("Deleting from Object Storage")
    for file in objects:
      delete_from_object_storage(object_storage_client, namespace, bucket, file)

  if args.action == 'download':
    print_header("Downloading from Object Storage")
    if dst and not dst.endswith('/'):
      dst = dst + '/'
    for file in objects:
      download_from_object_storage(object_storage_client, namespace, bucket, src, file, dst)

  if args.action == 'upload':
    parallel = multiprocessing.cpu_count()
    print('Setting Upload Parallelism to {}'.format(parallel))
    files = {}
    if os.path.isdir(src):
      if not src.endswith('/'):
        src = src + '/'
      print('Getting files in {}'.format(src))
      for file in glob.glob(src + "**/**", recursive=True):
        files[os.path.abspath(file)] = "local"
    else:
      files[os.path.abspath(src)] = "local"

    print_header("Uploading {} local files to Object Storage".format(len(files)))
    upload_manager = oci.object_storage.UploadManager(
      object_storage_client, allow_parallel_uploads=True, parallel_process_count=parallel)
    for filePath in files:
      if os.path.isdir(filePath):
        continue
      # Skip socket files
      mode = os.stat(filePath).st_mode
      if stat.S_ISSOCK(mode) or stat.S_ISFIFO(mode):
        continue
      full_path=os.path.abspath(filePath)
      upload_to_object_storage(upload_manager, namespace, bucket, full_path, parallel)

  elapsed_time = str(timedelta(seconds=time.time() - start_time))
  if not _success:
    raise SystemExit(print_header("Failures Detected; See Output ({})".format(elapsed_time)))
  print_header("Success; No Failures Detected ({})".format(elapsed_time))