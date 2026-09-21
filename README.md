# iitk minecraft bot

discord bot and automation setup for the iit kanpur minecraft community and smp server.

## files

- `main.py` - bot entry point, discord views, whitelist management, and keepalive server
- `requirements.txt` - dependencies (discord.py, aiohttp)
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

## features

- automatic category, channel, and permission setup
- interactive hostel / hall selection dropdown for campus halls (hall 1 to 14, gh)
- role selection buttons for java/bedrock edition and playstyles
- whitelist applications modal with staff review buttons
- support ticket launcher for grief reports and bug tracking
- http keepalive server for cloud deployment
