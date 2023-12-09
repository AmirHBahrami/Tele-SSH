from json import load as json_load
from json import dump as json_dump
import re

def regex_ip(ip):
  """matches given string to the regex of ip"""
  pattern = re.compile(r'^(\d{1,4})\.(\d{1,4})\.(\d{1,4})\.(\d{1,4})$')
  gaps=pattern.search(ip)
  if not gaps:
    return False
  gaps=pattern.search(ip).groups()
  if not bool(gaps) or len(gaps)==0:
    return False
  for g in gaps:
    if int(g) > 255 or int(g) < 0 : 
      return False
  return bool(gaps)

def json_get(path_to_file):
	""" read json file into an object """
	read_object=None
	with open(path_to_file,'r') as json_f:
		read_object=json_load(json_f)
	return read_object

def json_save(obj,path_to_file,mode='w+'):
	""" save json object to file """
	with open(path_to_file,mode) as json_f:
		json_dump(obj,json_f)
