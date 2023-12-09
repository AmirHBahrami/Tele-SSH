from json import load as json_load
import os
import logging
import telebot
import bot_api
from utils import json_get

# main module initalizes and runs the bot from the settings

# TODO add windows configs too
settings=json_get('./settings.json')

if not os.path.exists(settings['logs_file']):
	os.mknod(settings['logs_file'])

if not os.path.exists(settings['users_file']):
	os.mknod(settings['users_file'])

logging.basicConfig(filename=settings['logs_file'], 
	filemode='a+',
	format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
del settings # clear from memory

# hit the bot start
bot_api.run_bot()
