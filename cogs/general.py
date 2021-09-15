import discord
from discord.ext import commands, tasks
from pymongo import MongoClient
import datetime
import matplotlib.pyplot as plt
import numpy as np

plt.rcParams['font.size'] = 8.0

cluster = MongoClient('INSERT MONGOCLIENT KEY') # INSERT MONGOCLIENT KEY
db = cluster["EasyBallot"] # INSERT DATABASE NAME
vote_db = db["Votes"] # INSERT COLLECTION NAME

# Modify keys and values to represent candidates. (KEY:VALUE). Add/remove at need.
candidates = {
            "D": "No Candidate",
            "R": "No Candidate",
            "C": "No Candidate",
        }
election_year = "2020"
poll_name = f"{election_year} Presidential Election"

class General(commands.Cog):

    def __init__(self, client):
        self.client = client
        self.live_election_results.start()

    # Command to notify entire server + ping a voter registered role. (OPTIONAL) 
    @commands.Cog.listener()
    async def on_ready(self):
        ann_channel = self.client.get_guild("GUILD_ID").get_channel("CHANNEL_ID") # Specify an announcement channel. (OPTIONAL)
        vote_registered_role = self.client.get_guild("GUILD_ID").get_role("ROLE_ID") # Specify a voter registered role. (OPTIONAL)
        
        embed = discord.Embed(
            title=poll_name,
            description=f"The polls for the {poll_name} are officially open.",
            color=discord.Colour.green()
        )
        embed.add_field(name="Instructions", value="1) Please DM **me** with the command: `ez!vote` to be able to vote in the Presidential election."
                                                   "\n\n2) Please follow the instructions given to you by me."
        embed.set_thumbnail(url=self.client.user.avatar_url_as(static_format="png"))

        await ann_channel.send(embed=embed)
        await ann_channel.send(vote_registered_role.mention) # Mentions a specific role. (OPTIONAL)

    @commands.command()
    @commands.dm_only()
    async def vote(self, ctx):
        self_check = vote_db.find_one({"userid": int(ctx.author.id)}) # Checks to see if voter has already voted. 
        vote_registered_role = self.client.get_guild("GUILD_ID").get_role("ROLE_ID") # Specify a voter registered role. (OPTIONAL)
        member_object = self.client.get_guild("GUILD_ID").get_member(ctx.author.id) # Pull member object.

        # IF YOU ARE NOT USING A VOTE REGISTERED ROLE, DELETE THIS BLOCK AND FIX INDENTS STARTING HERE... 
        if vote_registered_role not in member_object.roles:
            embed = discord.Embed(
                title="There has been an error.",
                description="You are not registered to vote. "
                            "You will not be able to vote in this election without having proper authorization.",
                color=discord.Colour.red()
            )
            embed.set_thumbnail(url=self.client.user.avatar_url_as(static_format="png"))
            await ctx.send(embed=embed)
        else:
        # ... AND ENDING HERE
            if self_check is not None:
                embed = discord.Embed(
                    title="There has been an error.",
                    description="It appears you have already voted. "
                                "Please wait until the next election to vote.",
                    color=discord.Colour.red()
                )
                embed.set_thumbnail(url=self.client.user.avatar_url_as(static_format="png"))
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="Vote",
                    description="**Please message me with the letter corresponding to your preferred candidate to vote.**",
                    color=discord.Colour.green()
                )
                embed.set_thumbnail(url=self.client.user.avatar_url_as(static_format="png"))

                for x, y in candidates.items():
                    embed.add_field(name=f'Candidate Letter "{str(x)}"', value=f'{str(y)}', inline=False)

                await ctx.send(embed=embed)

                def voted_check(m):
                    return m.guild is None and m.author == ctx.author

                voted_for = await self.client.wait_for('message', check=voted_check)

                if str(voted_for.content.upper()) in candidates.keys():
                    print(vote_db.insert_one({"userid": int(ctx.author.id),
                                              "name": str(ctx.author),
                                              "vote": str(candidates[str(voted_for.content.upper())]),
                                              "ts": str(datetime.datetime.utcnow())}))

                    embed = discord.Embed(
                        title="Thank you casting your ballot!",
                        description=f"Your ballot for **{str(candidates[str(voted_for.content.upper())])}** has been successfully cast! "
                                    f"Here's a sticker!",
                        color=discord.Colour.green()
                    )
                    embed.set_thumbnail(url=self.client.user.avatar_url_as(static_format="png"))
                    embed.set_image(url="https://c.tenor.com/zpSMW5Ecm74AAAAC/i-voted-joe-biden.gif")
                    await ctx.send(embed=embed)

                else:
                    embed = discord.Embed(
                        title="There has been an error.",
                        description="Improper entry, please retry.",
                        color=discord.Colour.red()
                    )
                    embed.set_thumbnail(url=self.client.user.avatar_url_as(static_format="png"))
                    await ctx.send(embed=embed)

    @commands.command()
    @commands.is_owner()
    async def tabulate(self, ctx):
        candidate_votes = [int(vote_db.count_documents({"vote": str(candidate)})) for candidate in candidates.values()]
        election_candidates = [str(x) for x in candidates.values()]
        vote_registered_role = self.client.get_guild("GUILD_ID").get_role("ROLE_ID") # Specify a voter registered role. (OPTIONAL)
        total_votes = int(vote_db.count_documents({}))

        y = np.array(candidate_votes)
        candidate_colors = ["blue", "red", "orange"] # Change colors to your liking but REMEMBER THAT THEY ARE CONSECUTIVE WITH THE CANDIDATES. 

        fig, ax = plt.subplots(figsize=(6, 6))
        ax.pie(y, labels=election_candidates, colors=candidate_colors, autopct='%.2f%%')
        ax.set_title(poll_name)
        plt.tight_layout()
        plt.savefig(f'C:/Users/NAME/Desktop/BallotBot/graphs/{election_year}.png') # Set a destination where you want pie charts to be saved to.

        pie_chart = discord.File(
            f'C:/Users/NAME/Desktop/BallotBot/graphs/{election_year}.png', # Pull destination.
            filename=f"{election_year}.png")

        embed = discord.Embed(
            title=f"{poll_name} Results",
            color=0x4287f5
        )
        
        # Specify election turnout (OPTIONAL).
        embed.add_field(name="Election Turnout",
                        value=f'{round(float(total_votes / len(vote_registered_role.members)) * 100, 2)}%',
                        inline=False)

        for x in candidates.values():
            embed.add_field(name=f'{str(x)} Total Votes & Percentage',
                            value=f'{int(vote_db.count_documents({"vote": str(x)}))}, {round(float(int(vote_db.count_documents({"vote": str(x)})) / total_votes) * 100, 2)}%',
                            inline=False)

        embed.set_image(url=f"attachment://{election_year}.png")
        embed.set_thumbnail(url=self.client.user.avatar_url_as(static_format="png"))

        await ctx.send(file=pie_chart, embed=embed)

    # Sends live results of the election.
    @tasks.loop(minutes=30.0) # Tweak the amount of minutes you want the bot to automatically send 
    async def live_election_results(self):
        await self.client.wait_until_ready()
        total_votes = int(vote_db.count_documents({}))
        vote_registered_role = self.client.get_guild("GUILD_ID").get_role("ROLE_ID") # Specify a voter registered role. (OPTIONAL)

        embed = discord.Embed(
            title=f"{poll_name} Results",
            color=0xffffff
        )
        
        # Specify election turnout (OPTIONAL).
        embed.add_field(name="Election Turnout",
                        value=f'{round(float(total_votes / len(vote_registered_role.members)) * 100, 2)}%',
                        inline=False)

        for x in candidates.values():
            if int(vote_db.count_documents({"vote": str(x)})) == 0:
                pass
            else:
                embed.add_field(name=f'{str(x)} Total Votes & Percentage',
                                value=f'{int(vote_db.count_documents({"vote": str(x)}))}, {round(float(int(vote_db.count_documents({"vote": str(x)})) / total_votes) * 100, 2)}%',
                                inline=False)

        embed.set_thumbnail(url=self.client.user.avatar_url_as(static_format="png"))

        live_results_channel = self.client.get_guild("GUILD_ID").get_channel("CHANNEL_ID") # specify where you want bot to post live results.
        await live_results_channel.send(embed=embed)

def setup(client):
    client.add_cog(General(client))
