## snakebot
A discord.py bot that tries to do everything

<img src="https://img.shields.io/github/languages/code-size/Singularitat/snakebot.svg" alt="Code size"/> <img src="https://img.shields.io/github/repo-size/Singularitat/snakebot.svg" alt="GitHub repo size"/> <img src="https://tokei.rs/b1/github/Singularitat/snakebot?category=code" alt="Lines of Code"/>

## Running

1. **Python 3.10 or higher**

2. **Install dependencies**

```bash
pip install -U -r requirements.txt
```

If plyvel fails to install on Windows install Visual Studio Build Tools 2019

If plyvel fails to install on Debian or Ubuntu try
```bash
apt-get install libleveldb1v5 libleveldb-dev
```

3. **Setup configuration**

The next step is just to create a file named `config.py` in the root directory where
the [bot.py](/bot.py) file is with the following template:

```py
token = ''  # your bot's token
```

&nbsp;

**Notes:**

You will probably want to remove my discord id from the owner_ids in [bot.py](/bot.py#L30) and replace it with your own

If you want the downvote command to work you should change the downvote emoji in [events.py](/cogs/events.py)

If you want the music cog to work you will need [ffmpeg](https://ffmpeg.org/download.html) either on your PATH or in the root directory where
the [bot.py](/bot.py) file is

&nbsp;

## Requirements

- [Python 3.10+](https://www.python.org/downloads)
- [pycord](https://github.com/Pycord-Development/pycord)
- [lxml](https://github.com/lxml/lxml)
- [psutil](https://github.com/giampaolo/psutil)
- [orjson](https://github.com/ijl/orjson)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp)
- [plyvel](https://github.com/wbolster/plyvel)
- [pillow](https://github.com/python-pillow/Pillow)
