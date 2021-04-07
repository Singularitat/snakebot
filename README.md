## snakebot
A basic discord.py bot that tries to do everything

## Running

1. **Python 3.9 or higher**

You should be able to run it on earlier versions but I haven't tried

2. **Install dependencies**

On windows

`pip install -U -r requirements.txt`
or
`poetry install`

On linux

If you are running linux plyvel-win32 won't install so you will have to replace it with plyvel

`pip install -U -r requirements.txt`/`pip3 install -U -r requirements.txt`

If it fails to install on Debian or Ubuntu try `apt-get install libleveldb1v5 libleveldb-dev`


3. **Setup configuration**

The next step is just to create a `config.py` file in the root directory where
the bot is with the following template:

```py
token = '' # your bot's token
tenor = '' # tenor key for the hug command from https://tenor.com/developer/dashboard
coinmarketcap = '' # coinmarketcap key for crypto command from https://pro.coinmarketcap.com/
client_id = '' # The client id of your bot for the invite command
```

## Requirements

- Python 3.9+
- discord-ext-menus @ git+https://github.com/Rapptz/discord-ext-menus@master
- discord.py
- lxml
- psutil
- ujson
- youtube_dl
- plyvel
