import discord
from discord.ext import commands
from pymongo import MongoClient
import datetime
import matplotlib.pyplot as plt
import numpy as np
plt.rcParams['font.size'] = 8.0 # Change the font size of the graph

cluster = MongoClient() # Insert MongoClient key into parantheses 
db = cluster["EasyBallot"] # Add the name of the cluster to store vote data
vote_db = db["Votes"] # Add collection name

intents = discord.Intents.all()
client = commands.Bot(command_prefix = 'ez!', intents=intents) # Tweak the command_prefix at will

# activation procedure
@client.event
async def on_ready():
    print('Activated!')

@client.command()
async def ping(ctx):
    await ctx.send(f'**Returned at:** {round(client.latency * 1000)}ms')

# Election Information
candidates={
        "A":"Name 1", # Use this format to add candidates. Use leters from A-Z as keys and values will be names of candidates.
        "B":"Name 2"
    }
election_year = "2016" # Year of election or name of election.

@client.command()
@commands.dm_only()
async def vote(ctx):
    self_check = vote_db.find_one({"userid":int(ctx.author.id)})
    vote_registered_role = client.get_guild("guild_id").get_role("role_id") # Set a voter registration channel (optional)
    member_object = client.get_guild("guild_id").get_member(ctx.author.id) # Specify a member object. 

    if vote_registered_role not in member_object.roles: # IF YOU ARE NOT USING A VOTER REGISTRATION ROLE, PLEASE REMOVE THIS BLOCK STARTING HERE ...
        embed = discord.Embed(
            title="There has been an error.",
            description="You are not registered to vote. "
                        "You will not be able to vote in this election without having proper authorization.",
            color=discord.Colour.red()
        )
        embed.set_thumbnail(url=client.user.avatar_url_as(static_format="png"))
        await ctx.send(embed=embed)
    else: # ... AND ENDING HERE
        if self_check is not None:
            embed = discord.Embed(
                title="There has been an error.",
                description="It appears you have already voted. "
                            "Please wait until the next election to vote.",
                color=discord.Colour.red()
            )
            embed.set_thumbnail(url=client.user.avatar_url_as(static_format="png"))
            await ctx.send(embed=embed)
        else:
            embed = discord.Embed(
                title="Vote",
                description="**Please follow these instructions carefully so as to not make mistakes.**",
                color=discord.Colour.green()
            )
            embed.add_field(name="Instructions", value='Please message me with the letter corresponding to your preffered candidate to vote.', inline=False)
            embed.set_thumbnail(url=client.user.avatar_url_as(static_format="png"))
            for x, y in candidates.items():
                embed.add_field(name=f'Candidate {str(x)}', value=f'{str(y)}', inline=False)

            await ctx.send(embed=embed)

            def voted_check(m):
                return m.guild is None and m.author == ctx.author

            voted_for = await client.wait_for('message', check=voted_check)

            if str(voted_for.content.upper()) in candidates.keys():
                print(vote_db.insert_one({"userid":int(ctx.author.id), "name":str(ctx.author), "vote":str(candidates[str(voted_for.content.upper())]), "ts":str(datetime.datetime.utcnow())}))

                embed = discord.Embed(
                    title="Thank you casting your ballot!",
                    description=f"Your ballot for **{str(candidates[str(voted_for.content.upper())])}** has been successfully cast! "
                                f"Here's a sticker!",
                    color=discord.Colour.green()
                )
                embed.set_thumbnail(url=client.user.avatar_url_as(static_format="png"))
                embed.set_image(url="https://c.tenor.com/zpSMW5Ecm74AAAAC/i-voted-joe-biden.gif") # Sends a nice lil gif. dw, it's not actually Joe Biden (depending on political prefence)
                await ctx.send(embed=embed)

            else:
                embed = discord.Embed(
                    title="There has been an error.",
                    description="Improper entry, please retry.",
                    color=discord.Colour.red()
                )
                embed.set_thumbnail(url=client.user.avatar_url_as(static_format="png"))
                await ctx.send(embed=embed)

# Clean the database for next election.
@client.command()
@commands.is_owner()
async def cleardb(ctx):
    print(vote_db.delete_many({}))
    await ctx.send("All clear, boss! See you next election.")

# Tabulation is still very roughly finished but will likely see some tweaks in the coming months.
@client.command()
@commands.is_owner()
async def tabulate(ctx):
    a_votes = int(vote_db.count_documents({"vote":str(candidates["A"])}))
    b_votes = int(vote_db.count_documents({"vote":str(candidates["B"])})) 
    # Add more varables for more candidates. It is currently not automatic. Follow the same layout to add more variables.
    total_votes = int(vote_db.count_documents({}))

    y = np.array([int(a_votes), int(b_votes)])
    election_candidates = [
        f'{candidates["A"]}, {round(float(a_votes / total_votes) * 100, 2)}%',
        f'{candidates["B"]}, {round(float(b_votes / total_votes) * 100, 2)}%'
        # Add more varables for more candidates. It is currently not automatic. Follow the same layout to add more variables.
    ]
    candidate_colors = ["blue", "red"]

    plt.pie(y, labels=election_candidates, colors=candidate_colors)
    plt.savefig(f'C:/Users/NAME/Desktop/FOLDER/EasyVote/election data/{election_year}.png') # Add a location to save pie charts of votes.

    pie_chart = discord.File(f'C:/Users/NAME/Desktop/FOLDER/EasyVote/election data/{election_year}.png', filename=f"{election_year}.png") # Pull file location
    vote_registered_role = client.get_guild("guild_id").get_role("role_id") # Specify a voter registered role (OPTIONAL)

    embed = discord.Embed(
        title=f"{election_year} Presidential Election Results", # Tweak the title of your election data.
        color=0x4287f5
    )
    embed.add_field(name="Election Turnout", value=f'{round(float(total_votes / len(vote_registered_role.members)) * 100, 2)}%', inline=False) # OPTIONAL COMMAND TO SPECIFY VOTER TURNOUT

    embed.add_field(name=f'{candidates["A"]} Total Votes', value=str(a_votes))
    embed.add_field(name=f'{candidates["B"]} Total Votes', value=str(b_votes))
    # Add more varables for more candidates. It is currently not automatic. Follow the same layout to add more variables.

    embed.add_field(name=f'{candidates["A"]} Percentage', value=f'{round(float(a_votes / total_votes) * 100, 2)}%', inline=False)
    embed.add_field(name=f'{candidates["B"]} Percentage', value=f'{round(float(b_votes / total_votes) * 100, 2)}%', inline=False)
    # Add more varables for more candidates. It is currently not automatic. Follow the same layout to add more variables.

    embed.set_image(url=f"attachment://{election_year}.png")
    embed.set_thumbnail(url=client.user.avatar_url_as(static_format="png"))

    await ctx.send(file=pie_chart, embed=embed)

client.run('INSERT A BOT TOKEN HERE')
