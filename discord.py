import psutil
import discord
from discord.ext import commands, tasks
import asyncio

# Initialize the Discord bot
BOT_TOKEN = 'YOUR_BOT_TOKEN'
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Thresholds
CPU_THRESHOLD = 80
MEMORY_THRESHOLD = 80
DISK_THRESHOLD = 80
DDOS_THRESHOLD = 200

# Set to store channel IDs for alerts
alert_channels = set()

def get_resource_usage():
    try:
        cpu = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory().percent
        disk = psutil.disk_usage('/').percent
        connections = len(psutil.net_connections())
        return cpu, memory, disk, connections
    except Exception as e:
        print(f"Failed to get resource usage: {e}")
        return None, None, None, None

async def send_alert(channel, cpu_usage=None, memory_usage=None, disk_usage=None, connections=None):
    message = "⚠️ Alert!"
    if cpu_usage is not None:
        message += f"\nCPU Usage: {cpu_usage}%"
    if memory_usage is not None:
        message += f"\nMemory Usage: {memory_usage}%"
    if disk_usage is not None:
        message += f"\nDisk Usage: {disk_usage}%"
    if connections is not None:
        message += f"\nDDoS Alert: {connections} connections detected!"

    await channel.send(message)

@tasks.loop(minutes=1)
async def check_resource_usage():
    cpu_usage, memory_usage, disk_usage, connections = get_resource_usage()
    print(f"CPU: {cpu_usage}%, Memory: {memory_usage}%, Disk: {disk_usage}%, Connections: {connections}")

    for channel_id in alert_channels:
        channel = bot.get_channel(channel_id)
        if channel:
            if cpu_usage is not None and cpu_usage > CPU_THRESHOLD:
                await send_alert(channel, cpu_usage=cpu_usage)
            if memory_usage is not None and memory_usage > MEMORY_THRESHOLD:
                await send_alert(channel, memory_usage=memory_usage)
            if disk_usage is not None and disk_usage > DISK_THRESHOLD:
                await send_alert(channel, disk_usage=disk_usage)
            if connections is not None and connections > DDOS_THRESHOLD:
                await send_alert(channel, connections=connections)

@bot.command()
async def start(ctx):
    alert_channels.add(ctx.channel.id)
    await ctx.send("Bot monitoring active! You will receive notifications.")

    # Send current resource usage info
    cpu, memory, disk, connections = get_resource_usage()
    if cpu is None:
        await ctx.send("❌ Server is DOWN! Unable to retrieve information.")
    else:
        await ctx.send(f"🖥️ CPU Usage: {cpu}%\n💾 Memory Usage: {memory}%\n📀 Disk Usage: {disk}%\n🌐 Connections: {connections}")

@bot.command()
async def monitor(ctx):
    cpu, memory, disk, connections = get_resource_usage()
    if cpu is None:
        await ctx.send("❌ Server is DOWN! Unable to retrieve information.")
    else:
        await ctx.send(f"✅ Server is UP!\n🖥️ CPU Usage: {cpu}%\n💾 Memory Usage: {memory}%\n📀 Disk Usage: {disk}%\n🌐 Connections: {connections}")

# Start the resource monitoring task and run the bot
@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')
    check_resource_usage.start()

bot.run(BOT_TOKEN)
