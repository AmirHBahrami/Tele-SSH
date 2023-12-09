SSH-Bot for Telegram

It utilizes Telegram's pyTelegramBotAPI ( https://pytba.readthedocs.io/en/latest/ )
and paramiko ( https://www.paramiko.org ) to let users control and run commands
on their servers via telegram

One of the advantages here is that you can access telegram from anywhere and
you can also run this Bot as a process on your Personal Pc! (currently only linux 
version is supported)

The bot has a default set of commands to send via ssh to your servers. you need 
to first add some server ssh credentials in default_user.json

Just take a look at the file and you'll understand
----
How to run this bot:
	python .
or
	python3 .
----
how to use this bot:
in your Telegram application, go to the Id, which is assigned to this bot,
hit /start or /help

and it'll give you a brief tutorial
----
Also the bot is programmed in a manner that a 'state' is saved for 
each active user of it at the time being. you need to set a password 
as well, this'll make it a private bot, so make sure to set a password!
----
this isn't an actively supported bot, so feel free to contact me at
amirhesam.bahrami@yahoo.com if you had any questions or whatever

CHEERS!