# iitk minecraft bot

discord bot and automation setup for the iit kanpur minecraft community and smp server.

## files

- `main.py` - bot entry point, discord views, whitelist management, and keepalive server
- `requirements.txt` - dependencies (discord.py, aiohttp, certifi)
- `render.yaml` - cloud service configuration
- `.env.example` - environment variable template

## setup and install

1. clone the repository:
```bash
git clone https://github.com/gvbytes/IITK-minecraft-bot.git
cd IITK-minecraft-bot
```

2. install dependencies:
```bash
pip install -r requirements.txt
```

3. configure environment:
```bash
cp .env.example .env
```

## how to run

start the bot:
```bash
python main.py
```

## environment variables

- `DISCORD_BOT_TOKEN` : bot token from discord developer portal
- `MINECRAFT_SERVER_IP` : server ip shown by /ip command
- `PORT` : port for the http health check server (default: 10000)

## commands

- `!iitk ip` / `/ip` - server address and ports
- `!iitk coords` / `/coords` - community coordinates
- `!iitk rules` / `/rules` - server rules summary
- `!iitk ping` / `/ping` - bot latency
- `!iitk help` / `/help` - command guide

## features

- automatic category, channel, and permission setup
- interactive hostel / hall selection dropdown for campus halls (hall 1 to 14, gh)
- role selection buttons for java/bedrock edition and playstyles
- whitelist applications modal with staff review buttons
- duplicate prevention checking ign, roll number, and existing roles
- support ticket launcher for grief reports and bug tracking
- persistent whitelist registry saved to json
- http keepalive server for cloud deployment
