## snakebot
A basic discord.py bot that tries to do everything

<img src="https://img.shields.io/github/languages/code-size/Singularitat/snakebot.svg" alt="Code size"/> <img src="https://img.shields.io/github/repo-size/Singularitat/snakebot.svg" alt="GitHub repo size"/> <img src="https://tokei.rs/b1/github/Singularitat/snakebot?category=code" alt="Lines of Code"/>

## Running

1. **Python 3.9 or higher**

You should be able to run it on earlier versions but I haven't tried

2. **Install dependencies**

<details>
<summary><span>Windows</span></summary>

```bash
pip install -U -r requirements.txt
```

On windows you will also need plyvel-win32

```shell
pip install plyvel-win32
```

</details>

<details>

<summary><span>Linux</span></summary>

Note: you might need to use pip3 rather than pip
```shell
pip install -U -r requirements.txt
```

On linux you will need plyvel

```shell
pip install plyvel
```

If it fails to install on Debian or Ubuntu try
```shell
apt-get install libleveldb1v5 libleveldb-dev
```

</details>

3. **Setup configuration**

The next step is just to create a file named `config.py` in the root directory where
the [bot.py](/bot.py) file is with the following template:

```py
token = ''  # your bot's token
```

&nbsp;

**Notes:**

You will probably want to remove my discord id from the owner_ids in [bot.py](/bot.py#L30) and replace it with your own

If you want the downvote command to work you should change the downvote emoji in [events.py](/cogs/events.py) and you might want to disable auto downvoting on ghost pings in the on_message_delete event

If you want the music cog to work you will need [ffmpeg](https://ffmpeg.org/download.html) either on your PATH or in the root directory where
the [bot.py](/bot.py) file is

&nbsp;

## Requirements

- [Python 3.9+](https://www.python.org/downloads/)
- [discord-ext-menus](https://github.com/Rapptz/discord-ext-menus)
- [discord.py](https://github.com/Rapptz/discord.py/)
- [lxml](https://github.com/lxml/lxml)
- [psutil](https://github.com/giampaolo/psutil)
- [orjson](https://github.com/ijl/orjson)
- [youtube_dl](https://github.com/ytdl-org/youtube-dl)
- [plyvel](https://github.com/wbolster/plyvel)
- [pillow](https://github.com/python-pillow/Pillow)
