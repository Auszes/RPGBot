import datetime
import asyncio
import json
from collections import defaultdict

import discord
from discord.ext import commands

from .utils import data, checks
from .utils.translation import _


class Salary(object):
    """Salary commands"""
    def __init__(self, bot):
        self.bot = bot
        self.first = True
        self.guilds = defaultdict(dict)
        try:
            with open("salaries.json", "r") as gf:
                self.guilds.update(json.loads(gf.read()))
        except FileNotFoundError:
            pass
        self.bot.shutdowns.append(self.shutdown)

    async def shutdown(self):
        with open("salaries.json", "w") as gf:
            gf.write(json.dumps(self.guilds, indent=4))

    async def on_ready(self):
        self.bot.loop.create_task(self.run_salaries())

    async def run_salaries(self):
        if self.first:
            self.first = False
            _today = datetime.datetime(*datetime.datetime.utcnow().timetuple()[:3])
            time_until = 86400 - (_today + datetime.timedelta(days=1)).timestamp() - datetime.datetime.utcnow().timestamp()
            await asyncio.sleep(time_until)
            while True:
                dels = []
                await self.shutdown()
                for guild, roles in self.guilds.items():
                    try:
                        gob = self.bot.get_guild(guild)
                        if gob:
                            for role, amount in roles.items():
                                rob = discord.utils.get(gob.roles, id=role)
                                for member in rob.members:
                                    await self.bot.di.add_eco(member, amount)
                        else:
                            dels.append(guild)
                    except:
                        pass
                try:
                    for guild in dels:
                        del self.guilds[guild]
                except:
                    pass
                await asyncio.sleep(86400)

    @commands.command()
    @checks.no_pm()
    async def salaries(self, ctx):
        """See guild salaries"""
        embed = discord.Embed()
        if not self.guilds[ctx.guild.id]:
            await ctx.send(await _(ctx, "There are no current salaries on this server"))
        else:
            dels = []
            for role, amount in self.guilds[ctx.guild.id].items():
                try:
                    embed.add_field(name=discord.utils.get(ctx.guild.roles, id=role).name, value=f"${amount}")
                except:
                    dels.append(role)
            for d in dels:
                del self.guilds[ctx.guild.id][d]
            embed.set_author(name=await _(ctx, "Guild Salaries"), icon_url=ctx.guild.icon_url)
            await ctx.send(embed=embed)

    @commands.group(invoke_without_command=True, aliases=["sal"])
    @checks.no_pm()
    async def salary(self, ctx, role: discord.Role):
        """Get a role's salary. Also includes salary subcommands"""
        salary = self.guilds[ctx.guild.id].get(role.id, None)
        if salary is None:
            await ctx.send(await _(ctx, "That role does not have a salary!"))
        else:
            await ctx.send((await _(ctx, "{} has a daily salary of {}")).format(role, salary))

    @salary.command()
    @checks.no_pm()
    @checks.mod_or_permissions()
    async def create(self, ctx, amount: data.NumberConverter, role: discord.Role):
        """Create a daily salary for a user with the given role.
         Roles are paid every day at 24:00, every user with the role will receive the amount specified.
         If a role with a salary is deleted, the salary will also be deleted."""
        self.guilds[ctx.guild.id][role.id] = amount
        await ctx.send((await _(ctx, "Successfully created a daily salary of {} for {}")).format(amount, role))

    @salary.command()
    @checks.no_pm()
    @checks.mod_or_permissions()
    async def delete(self, ctx, *, role: discord.Role):
        """Remove a created salary"""
        del self.guilds[ctx.guild.id][role.id]
        await ctx.send((await _(ctx, "Successfully deleted the daily salary for {}")).format(role))

