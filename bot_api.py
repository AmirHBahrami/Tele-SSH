import telebot
from utils import json_get, json_save, regex_ip
from json import dumps as json_dumps
import traceback
import logging
import copy
import ssh_op

# initialize
settings=json_get('settings.json')
bot=telebot.TeleBot(settings['bot_token'])
users=json_get(settings['users_file'])
states=dict() # which user is doing what currently
del settings # clear from memory

def make_mention(message):
	return "(tg://user?id="+str(message.from_user.id)+")"

def update_state(message,state):
	states[make_mention(message)]=state

def save_users():
	json_save(users,'users.json')
    
def init_user(message):
	""" see user.setting for an example of how the data is structured """
	umention=make_mention(message)
	if not umention in users:
		users[umention]=dict()
	if not 'servers' in users[umention]:
		users[umention]['servers']=list()
	if not 'current' in users[umention]:
		users[umention]['current']=dict()
	if not 'cmd_list' in users[umention]:
		users[umention]['cmd_list']=list()	
	if not 'domains' in users[umention]:
		users[umention]['domains']=dict()

def reset_state(message):
	uname=make_mention(message)
	init_user(message)
	if uname in states:
		del states[uname]
	if 'current' in users[uname]:
		del users[uname]['current']
		users[uname]['current']=dict()

def check_profile(message):
	return make_mention(message) in users

# ---------------------------- server handlers
@bot.message_handler(commands=['delete_server'])
def delete_server(message):
	update_state(message,'should_del_server')
	init_user(message)
	get_del_server(message)

@bot.message_handler(commands=['add_server'])
def add_server(message):
	update_state(message,'should_set_server')
	init_user(message)
	get_server(message)

@bot.message_handler(commands=['see_servers'])
def add_server(message):
	if not check_profile(message) or not 'servers' in users[make_mention(message)]:
		bot.reply_to(message,'no servers added yet!')
	else:
		bot.reply_to(message,json_dumps(users[make_mention(message)]['servers']))

# ---------------------------- Domain handlers
@bot.message_handler(commands=['see_domains'])
def see_domains(message):
	init_user(message)
	list_domains(message)

@bot.message_handler(commands=['add_domain'])
def add_domain(message):
	init_user(message)
	users[make_mention(message)]['current']['operation']='add_domain'
	update_state(message,'should_get_domain_name')
	bot.reply_to(message,'enter domain name:')

@bot.message_handler(commands=['edit_domain_name'])
def edit_domain_name(message):
	init_user(message)
	users[make_mention(message)]['current']['operation']='edit_domain_name'
	update_state(message,'should_get_domain_name')
	if list_domains(message):
		bot.reply_to(message,'which domain:')

@bot.message_handler(commands=['edit_domain_ip'])
def edit_domain_ip(message):
	init_user(message)
	users[make_mention(message)]['current']['operation']='edit_domain_ip'
	update_state(message,'should_get_domain_name')
	if list_domains(message):
		bot.reply_to(message,'which domain:')

@bot.message_handler(commands=['delete_domain'])
def del_domain(message):
	init_user(message)
	users[make_mention(message)]['current']['operation']='delete_domain'
	update_state(message,'should_get_domain_name')
	if list_domains(message):
		bot.reply_to(message,'which domain:')

# ---------------------------- run handler
@bot.message_handler(commands=['run'])
def run_all(message):
	uname=make_mention(message)
	if uname not in states: # the default configs - updates everytime
		users[uname]=json_get('default_user.json')
		del users[uname]['passwd'] # should always be read directly from default_user.json
		users[uname]['auth']=False
		save_users()
	if not users[uname]['auth']:
		update_state(message,'should_authenticate')
		bot.reply_to(message,'please write your password:')
	else:
		cmd_runall(message)

# ---------------------------- commands handlers
@bot.message_handler(commands=['cmd','add_cmd'])
def add_cmd(message):
	update_state(message,'adding_cmd')
	cmd_add(message)

@bot.message_handler(commands=['see_cmds'])
def see_cmds(message):
	if not check_profile(message) or not 'cmd_list' in users[make_mention(message)] or len(users[make_mention(message)]['cmd_list'])<1:
		bot.reply_to(message,'no commands added yet!')
	else:
		bot.reply_to(message,'\n'.join(users[make_mention(message)]['cmd_list']))

@bot.message_handler(commands=['clear_cmds'])
def delete_cmds(message):
	if 'cmd_list' in users[make_mention(message)]:
		users[make_mention(message)]['cmd_list'].clear()
		bot.reply_to(message,'cmd list cleared')
		save_users()
	else:
		bot.reply_to(message,'cmd list was already empty')

@bot.message_handler(commands=['tutorial'])
def see_cmds(message):
	bot.reply_to(message,"""\
		Here's how to use this bot:
			if you want to use the default configs, simply hit /run !
			----
			in order to add your custom commands:
			
				1. type /add_server and wait for the bot to get informations from you

				2. now that you have a server, type /add_cmd and again, let the bot instruct you
				-- optional: you can now run /clear_cmds before this step, to make me forget the current script

				3. now you have one command, you can hit /run and let me do my job!
	""")

# ---------------------------- general handlers
@bot.message_handler(commands=['cancel'])
def canecl_current_request(message):
	reset_state(message)
	bot.reply_to(message,'canceled!')

@bot.message_handler(commands=['start','help'])
def greet_user(message):
	reset_state(message)
	bot.reply_to(message,"""\
		Welcome To tel_ssh_bot, I can send your scripts to your servers using your ssh configs
		if you want to know how to use me, type /tutorial this will show you all the details
		here's an overview of the orders you can give me:

		/tutorial : find out how to use this bot

		/add_server : add a new server to your list

		/see_servers : see your servers list

		/delete_server : delete a server

		/add_cmd :	add a new command to run

		/see_cmds : see your commands list

		/clear_cmds : clear the list of your commands

		/run : run your saved commands

		/cancel : the current process

		/see_domains : see your domains list

		/add_domain : add a new domain

		/delete_domain: delete a domain

		/edit_domain_name: replace a domain's name

		/edit_domain_ip: replace a domain's ip

		enjoy!
""")

@bot.message_handler(func=lambda msg: True)
def default_handler(message):
	""" gets current user's state of answering and """

	init_user(message) # just to be sure

	# if state not initialized, just ask for help
	if not make_mention(message) in states:
		bot.reply_to(message,'how can I /help you?')
		return
	
	# "match case" not used for compatibility with pyth <3.10
	current_state=states[make_mention(message)]
	print(current_state)

	# server settings
	if current_state=='should_set_port':
		get_port(message)
	elif current_state=='should_set_uname':
		get_uname(message)
	elif current_state=='should_set_passwd':
		get_passwd(message)
	elif current_state=='should_confirm_server':
		get_server_confirm(message)
	elif current_state=='server_confirm_pending':
		check_server_confirm(message)
	elif current_state=='got_del_server':
		del_server(message)
	
	# commands
	elif current_state=='adding_cmd':
		cmd_add(messaeg)
	elif current_state=='cmd_added':
		cmd_added(message)

	# managing authentication when /run is hit
	elif current_state=='should_authenticate':
		authenticate_user(message)
	
	# domain CRUD
	elif current_state=='should_get_domain_name':
		get_domain_name(message)
	elif current_state=='should_get_domain_ip':
		get_domain_ip(message)
	elif current_state=='should_update_domain_ip':
		update_domain_ip(message)
	elif current_state=='should_update_domain_name':
		update_domain_name(message)
	elif current_state=='should_get_domain_to_delete':
		delete_domain(message)

# ---------------------------- methods to set and get user state
def get_server(message):
	update_state(message,'should_set_port') # what to do next
	bot.reply_to(message,'enter server ip :') # inform user

def get_port(message):
	update_state(message,'should_set_uname')

	# from prev call
	mention=make_mention(message)
	users[mention]['current']['host']=message.text # from previous call
	init_user(message)
	for s in users[mention]['servers']:
		if s['host'] == message.text:
			reset_state(message)
			bot.reply_to(message,'you already have the host, maybe you want to /delete_server and initialize the /server again? or /add_cmd to your commands list?')
			return
	
	bot.reply_to(message,'enter port (enter 22 for default):')

def get_uname(message):
	users[make_mention(message)]['current']['port']=message.text
	update_state(message,'should_set_passwd')
	bot.reply_to(message,'enter username :')

def get_passwd(message):
	users[make_mention(message)]['current']['uname']=message.text
	update_state(message,'should_confirm_server')
	bot.reply_to(message,'enter password :')

def get_server_confirm(message):
	users[make_mention(message)]['current']['passwd']=message.text
	update_state(message,'server_confirm_pending')
	bot.reply_to(message,'please confirm the following setting: (y/n)\n'+json_dumps(users[make_mention(message)]['current']))

def check_server_confirm(message):
	if message.text=='n' or message.text=='no':
		bot.reply_to(message,'server configs lost, to configure a new server type /server')
	elif message.text=='y' or message.text=='yes':
		new_server=users[make_mention(message)]['current']
		users[make_mention(message)]['servers'].append(copy.deepcopy(new_server))
		bot.reply_to(message,'server saved. you can add commands to run with /cmd or /add_cmd')
		logging.info('user "'+make_mention(message)+'" added the server : '+json_dumps(new_server))

	# forget the state and current server
	reset_state(message)
	del users[make_mention(message)]['current']
	save_users()# dump user states to json file 

def get_del_server(message):
	update_state(message,'got_del_server')
	bot.reply_to(message,'enter server ip to delete:')

def del_server(message):
	reset_state(message)
	mention=make_mention(message)
	for s in users[mention]['servers']:
		if s['host']==message.text:
			users[mention]['servers'].remove(s)
			bot.reply_to(message,''+s['host']+' was deleted successfully')
			save_users()
			return
	 
	bot.reply_to(message,''+s['host']+' was not in your servers list')

# ---------------------------- methods to add run and see commands
def cmd_add(message):
	update_state(message,'cmd_added')
	bot.reply_to(message,'type the cmd as you would type it in linux terminal:')

def cmd_added(message):
	users[make_mention(message)]['cmd_list'].append(message.text) # from previous call
	save_users()
	reset_state(message)
	bot.reply_to(message,'cmd added. would you like to /see_cmds ( /cmds ) ?')

# ---------------------------- methods to run cmds
def authenticate_user(message):
	passwd=json_get('default_user.json')['passwd']
	if message.text != passwd:
		bot.reply_to(message,'wrong password, please try again:')
	else:
		users[make_mention(message)]['auth']=True
		reset_state(message)
		save_users()
		bot.reply_to(message,'authentication complete. running cmds...')
		cmd_runall(message)

def cmd_runall(message):
	user=users[make_mention(message)]
	if not check_profile(message) or not 'cmd_list' in user or not 'servers' in user:
		reset_state(message)
		bot.reply_to(message,'you have not set your parameters yet, type /servers or /cmds to list them')
		return
	if not 'last_res' in user:
		user['last_res']=dict()
	ssh_client=None

	# main functionality of this whole program : run all the cmds in all the servers and let the user know about them
	for server in user['servers']:
		bot.reply_to(message,server['host'])
		for cmd in user['cmd_list']:
			bot.reply_to(message,server['uname']+'@'+server['host']+'$ '+cmd+' ...')
			try:
				if not ssh_client:
					(res,ssh_client)=ssh_op.exec_cmd(server,cmd)
				else:
					(res,_)=ssh_op.exec_cmd(server,cmd,ssh_client)
				user['last_res']=copy.deepcopy(res)
				if res['type']=='err':
					ssh_client.close()
					update_state(message,'cmd_runall_failure')
					logging.error('user "'+make_mention(message)+'" failed to run "'+cmd+'" on "'+server['host']+'"')
				bot.reply_to(message,res['msg'])
			except Exception as e:
				bot.reply_to(message,'coud not connect to server. do you want to check your /servers config?')
				logging.error('"'+cmd+'" on "'+server['host']+' failed')
				print(e)
		if ssh_client:
			ssh_client.close()
			ssh_client=None
	bot.reply_to(message,'done! is there anything else I can /help you with?')

# ---------------------------- methods to crud domains
def list_domains(message):
	dude=users[make_mention(message)]['domains']
	if not dude:
		bot.reply_to(message,'you have no domains yet you may want to /add_domain')
		reset_state(message)
		return False
	bot.reply_to(message,json_dumps(dude))
	return True

def get_domain_name(message):
	uname=make_mention(message)
	users[uname]['current']['domain_name']=message.text
	current_operation=users[uname]['current']['operation']

	if current_operation == 'add_domain':
		update_state(message,'should_get_domain_ip')
		bot.reply_to(message,'enter the ip:')

	elif current_operation == 'edit_domain_name':
		if not message.text in users[uname]['domains']:
			bot.reply_to(message,'no such domain, try again:')
			return
		update_state(message,'should_update_domain_name')
		bot.reply_to(message,'enter the new domain name:')

	elif current_operation == 'edit_domain_ip':
		if not message.text in users[uname]['domains']:
			bot.reply_to(message,'no such domain, try again:')
			return
		update_state(message,'should_update_domain_ip')
		bot.reply_to(message,'enter new domain ip:')

	elif current_operation == 'delete_domain': # call it directly
		if not message.text in users[uname]['domains']:
			bot.reply_to(message,'no such domain, try again:')
			return
		delete_domain(message)

def update_domain_name(message):
	uname=make_mention(message)
	selected=users[uname]['current']['domain_name']
	if selected in users[uname]['domains']:
		selected_ip=users[uname]['domains'][selected]
		del users[uname]['domains'][selected]
		users[uname]['domains'][message.text]=selected_ip
		reset_state(message)
		save_users()
		bot.reply_to(message,'domain name changed. /see_domains')
	else:
		bot.reply_to(message,'domain name '+selected+' not found. /see_domains')
		
def get_domain_ip(message): # works fine with both edit and update
	if not regex_ip(message.text):
		bot.reply_to(message,'incorrect ipv4 format, try again:')
		return
	uname=make_mention(message)
	domain_name=users[uname]['current']['domain_name']
	users[uname]['domains'][domain_name]=message.text # domain : ip
	reset_state(message)
	save_users()

	bot.reply_to(message,'domain added. /see_domains')

def update_domain_ip(message):

	uname=make_mention(message)

	# ip not correct
	if not regex_ip(message.text):
		bot.reply_to(message,'incorrect ipv4 format, try again:')
		return
	
	domain_name=users[uname]['current']['domain_name']
	users[uname]['domains'][domain_name]=message.text # domain : ip
	reset_state(message)
	save_users()
	bot.reply_to(message,'domain ip changed. /see_domains ')

def delete_domain(message):
	uname=make_mention(message)
	domain_name=users[uname]['current']['domain_name']
	del users[uname]['domains'][domain_name]
	reset_state(message)
	save_users()
	bot.reply_to(message,'domain deleted')

# ---------------------------- call this method to get the bot started
def run_bot():
	""" call this method in main module to start the bot """
	print('ssh_bot running...')
	bot.infinity_polling()
