from paramiko import SSHClient, AutoAddPolicy
from utils import json_get
import logging

def exec_cmd(server,cmd,ssh_client=None):
	""" 
		executes one command and returns the result to the user server :{host, uname , passwd } ,
		if ssh_client is None, creates it with no problem
		returns (result { type, msg } , <paramikon.SSHClient>)
		you can then use the second parameter again in your next call (as the third argument) to reduce
		the overhead of create/closing an ssh connection
		NOTE that you have to call paramikon.SSHCleint.close() on the outside from the returned object
	"""

	# init
	if not ssh_client:
		ssh_client=SSHClient()
		ssh_client.set_missing_host_key_policy(AutoAddPolicy()) # not dealing with pam_keys issues
	ssh_client.connect(server['host'],username=server['uname'],password=server['passwd'],port=server['port'])

	# the main functionality of this entire program:
	stdin,stdout,stderr=ssh_client.exec_command(cmd)

	# catching output
	err='done. '+read_answer(stderr)
	out='done. '+read_answer(stdout)
	if len(err) >= 1 :
		res={
			'type':'err',
			'msg':err
		}
	else:
		res={
			'type':'out',
			'msg':out
		}
	return (res,ssh_client)

def read_answer(std_channel,max_lines=15):
	lines=""
	while max_lines >0 :
		lines=lines+std_channel.readline()
		if std_channel.channel.exit_status_ready():
			break
		max_lines-=1
	return lines
