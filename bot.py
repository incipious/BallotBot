import discord
from discord.ext import commands
from pymongo import MongoClient
import os

cluster = MongoClient('mongoclient_key')
db = cluster["EasyBallot"]
vote_db = db["Votes"]

intents = discord.Intents.all()
client = commands.Bot(command_prefix = 'ez!', intents=intents)

# activation procedure
@client.event
async def on_ready():
    print('Activated!')

@client.command()
async def ping(ctx):
    await ctx.send(f'**Returned at:** {round(client.latency * 1000)}ms')

@client.command()
@commands.is_owner()
async def cleardb(ctx):
    print(vote_db.delete_many({}))
    await ctx.send("All clear, boss! See you next election.")

@client.command(hidden=True)
@commands.is_owner()
async def load(ctx, extension):
    client.load_extension(f"cogs.{extension}")

@client.command(hidden=True)
@commands.is_owner()
async def unload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")

@client.command(hidden=True)
@commands.is_owner()
async def reload(ctx, extension):
    client.unload_extension(f"cogs.{extension}")
    client.load_extension(f"cogs.{extension}")

for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        client.load_extension(f"cogs.{filename[:-3]}")

client.run('TOKEN')
