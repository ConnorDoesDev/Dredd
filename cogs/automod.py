"""
Dredd, discord bot
Copyright (C) 2021 Moksej
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published
by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import discord
import difflib

from discord.ext import commands
from db.cache import CacheManager as cm
from utils.checks import moderator, admin, AutomodGlobalStates, AutomodValues
from utils.default import automod_values
from utils.paginator import Pages


class Automod(commands.Cog, name='Automoderation'):
    def __init__(self, bot):
        self.bot = bot
        self.help_icon = '<:channeldelete:687008899517513766>'
        self.big_icon = 'https://media.discordapp.net/attachments/679643465407266817/701055848788787300/channeldeletee.png?width=115&height=115'

    def automod_settings(self, guild):
        automod = cm.get(self.bot, 'automod', guild.id)

        if not automod:
            raise commands.BadArgument(_("Automod is disabled in this server, enable it by using `automod toggle` command"))

        raidmode = cm.get(self.bot, 'raidmode', guild.id)
        antispam = cm.get(self.bot, 'spam', guild.id)
        anticaps = cm.get(self.bot, 'masscaps', guild.id)
        antiinvite = cm.get(self.bot, 'invites', guild.id)
        antimentions = cm.get(self.bot, 'massmention', guild.id)
        antilinks = cm.get(self.bot, 'links', guild.id)

        raidaction, spamaction, capsaction, inviteaction, mentionsaction, linksaction, raidchannel = None, None, None, None, None, None, None
        time, limit, perc, dms = None, None, None, _('No')
        if raidmode:
            raidaction = _("Kick Member") if raidmode['action'] == 1 else _("Ban Member") if raidmode['action'] == 2 else _("Kick All Members") if raidmode['action'] == 3 else _("Ban All Members")
            raidchannel = self.bot.get_channel(raidmode['channel'])
            if raidmode['dm']:
                dms = _('Yes')
        if antispam:
            lvl = antispam['level']
            spamaction = _("Mute Member") if lvl == 1 else _("Temp-Mute Member ({0})").format(antispam['time']) if lvl == 2 else _("Kick Member") if lvl == 3 else _("Ban Member") if lvl == 4 else _("Temp-Ban Member ({0})").format(antispam['time'])
        if anticaps:
            lvl = anticaps['level']
            perc = f"{anticaps['percentage']}%"
            capsaction = _("Mute Member") if lvl == 1 else _("Temp-Mute Member ({0})").format(anticaps['time']) if lvl == 2 else _("Kick Member") if lvl == 3 else _("Ban Member") if lvl == 4 else _("Temp-Ban Member ({0})").format(anticaps['time'])
        if antiinvite:
            lvl = antiinvite['level']
            inviteaction = _("Mute Member") if lvl == 1 else _("Temp-Mute Member ({0})").format(antiinvite['time']) if lvl == 2 else _("Kick Member") if lvl == 3 else _("Ban Member") if lvl == 4 else _("Temp-Ban Member ({0})").format(antiinvite['time'])
        if antimentions:
            lvl = antimentions['level']
            limit = antimentions['limit']
            mentionsaction = _("Mute Member") if lvl == 1 else _("Temp-Mute Member ({0})").format(antimentions['time']) if lvl == 2 else _("Kick Member") if lvl == 3 else _("Ban Member") if lvl == 4 else _("Temp-Ban Member ({0})").format(antimentions['time'])
        if antilinks:
            lvl = antilinks['level']
            linksaction = _("Mute Member") if lvl == 1 else _("Temp-Mute Member ({0})").format(antilinks['time']) if lvl == 2 else _("Kick Member") if lvl == 3 else _("Ban Member") if lvl == 4 else _("Temp-Ban Member ({0})").format(antilinks['time'])
        channel = self.bot.get_channel(automod['channel'])
        raidchannel = _("\n**Anti-Raid Logging Channel:** {0}").format(raidchannel.mention) if raidchannel else ""

        message = _("""```
1. Anti Spam        -       {0}
2. Anti Mass Caps   -       {1}
3. Anti Invites     -       {2}
4. Anti Mention     -       {3}
5. Anti Links       -       {4}
--- Other ---
6. Raid Mode        -       {5}```
**Automod Logging Channel:** {6}{7}
**Ignore Moderators:** {8}
**Delete Messages:** {9}
**DM people during raid:** {10}{11}{12}""").format(
            spamaction if spamaction else _('Disabled'), capsaction if capsaction else _('Disabled'), inviteaction if inviteaction else _('Disabled'),
            mentionsaction if mentionsaction else _('Disabled'), linksaction if linksaction else _('Disabled'), raidaction if raidaction else _('Disabled'),
            channel if not channel else channel.mention, raidchannel, _('Yes') if automod['ignore_admins'] else _('No'), _('Yes') if automod['delete_messages'] else _('No'),
            dms, _("\n**Mentions Limit:** {0}").format(limit) if limit else '', _("\n**Caps Percentage:** {0}").format(perc) if perc else ''
        )

        return message

    @commands.group(invoke_without_command=True, brief="Manage automod state in the server")
    @commands.cooldown(1, 5, commands.BucketType.member)
    @moderator(manage_messages=True)
    @commands.guild_only()
    async def automod(self, ctx):
        """ Manage automod in the server """
        values = self.automod_settings(ctx.guild)

        e = discord.Embed(color=self.bot.settings['colors']['embed_color'], title=_("{0} Automod Settings").format(ctx.guild))
        e.description = values
        await ctx.send(embed=e)

    @automod.command(name='toggle', brief="Toggle automod")
    @commands.cooldown(1, 5, commands.BucketType.member)
    @admin(manage_guild=True)
    @commands.guild_only()
    async def automod_toggle(self, ctx, channel: discord.TextChannel = None):
        """ Toggle automod """
        automod = cm.get(self.bot, 'automod', ctx.guild.id)

        if not automod and channel:
            if not channel.can_send or not channel.permissions_for(ctx.guild.me).embed_links:
                return await ctx.send(_("{0} I'm missing permissions in that channel. Make sure you have given me the correct permissions!").format(self.bot.settings['emojis']['misc']['warn']))

            await self.bot.db.execute("INSERT INTO automod(guild_id, channel_id) VALUES($1, $2)", ctx.guild.id, channel.id)
            self.bot.automod[ctx.guild.id] = {'channel': channel.id, 'ignore_admins': True, 'delete_messages': False}
            await ctx.send(_("{0} Automod was successfully enabled in this server.").format(self.bot.settings['emojis']['misc']['white-mark']))
        elif automod and not channel:
            await self.bot.db.execute("DELETE FROM automod WHERE guild_id = $1", ctx.guild.id)
            self.bot.automod.pop(ctx.guild.id)
            self.bot.raidmode.pop(ctx.guild.id, None)
            self.bot.spam.pop(ctx.guild.id, None)
            self.bot.masscaps.pop(ctx.guild.id, None)
            self.bot.invites.pop(ctx.guild.id, None)
            self.bot.links.pop(ctx.guild.id, None)
            self.bot.massmention.pop(ctx.guild.id, None)
            await ctx.send(_("{0} Automod was successfully disabled in this server.").format(self.bot.settings['emojis']['misc']['white-mark']))
        elif not automod and not channel:
            raise commands.MissingRequiredArgument(self.automod_toggle.params['channel'])
        elif automod and channel:
            if not channel.can_send or not channel.permissions_for(ctx.guild.me).embed_links:
                return await ctx.send(_("{0} I'm missing permissions in that channel. Make sure you have given me the correct permissions!").format(self.bot.settings['emojis']['misc']['warn']))

            await self.bot.db.execute("UPDATE automod SET channel_id = $1 WHERE guild_id = $2", channel.id, ctx.guild.id)
            self.bot.automod[ctx.guild.id]['channel'] = channel.id
            await ctx.send(_("{0} Automod was successfully enabled in this server.").format(self.bot.settings['emojis']['misc']['white-mark']))

    @automod.command(name='set', brief="Set global automod value")
    @commands.cooldown(1, 5, commands.BucketType.member)
    @admin(manage_guild=True)
    @commands.guild_only()
    async def automod_set(self, ctx, state: AutomodGlobalStates):
        """ Automtically set the automod values """
        automod = cm.get(self.bot, 'automod', ctx.guild.id)

        if not automod:
            raise commands.BadArgument(_("Automod is disabled in this server, enable it by using `{0}automod toggle` command").format(ctx.prefix))

        antispam = cm.get(self.bot, 'spam', ctx.guild.id)
        anticaps = cm.get(self.bot, 'masscaps', ctx.guild.id)
        antiinvite = cm.get(self.bot, 'invites', ctx.guild.id)
        antimentions = cm.get(self.bot, 'massmention', ctx.guild.id)
        antilinks = cm.get(self.bot, 'links', ctx.guild.id)
        value = _('chill') if state['time'] == '12h' else _('strict')

        if not antispam:
            await self.bot.db.execute("INSERT INTO antispam(guild_id, level, time) VALUES($1, $2, $3)", ctx.guild.id, state['spam'], state['time'])
            self.bot.spam[ctx.guild.id] = {'level': state['spam'], 'time': state['time']}
        elif antispam:
            await self.bot.db.execute("UPDATE antispam SET level = $1, time = $2 WHERE guild_id = $3", state['spam'], state['time'], ctx.guild.id)
            self.bot.spam[ctx.guild.id] = {'level': state['spam'], 'time': state['time']}

        if not anticaps:
            await self.bot.db.execute("INSERT INTO masscaps(guild_id, level, percentage, time) VALUES($1, $2, $3, $4)", ctx.guild.id, state['masscaps'], 75, state['time'])
            self.bot.masscaps[ctx.guild.id] = {'level': state['masscaps'], 'percentage': 75, 'time': state['time']}
        elif anticaps:
            await self.bot.db.execute("UPDATE masscaps SET level = $1, time = $2 WHERE guild_id = $3", state['masscaps'], state['time'], ctx.guild.id)
            self.bot.masscaps[ctx.guild.id] = {'level': state['masscaps'], 'percentage': 75, 'time': state['time']}

        if not antiinvite:
            await self.bot.db.execute("INSERT INTO invites(guild_id, level, time) VALUES($1, $2, $3)", ctx.guild.id, state['invites'], state['time'])
            self.bot.invites[ctx.guild.id] = {'level': state['invites'], 'time': state['time']}
        elif antiinvite:
            await self.bot.db.execute("UPDATE invites SET level = $1, time = $2 WHERE guild_id = $3", state['invites'], state['time'], ctx.guild.id)
            self.bot.invites[ctx.guild.id] = {'level': state['invites'], 'time': state['time']}

        if not antimentions:
            await self.bot.db.execute("INSERT INTO massmention(guild_id, level, mentions_limit, time) VALUES($1, $2, $3, $4)", ctx.guild.id, state['massmention'], 5, state['time'])
            self.bot.massmention[ctx.guild.id] = {'level': state['massmention'], 'limit': 5, 'time': state['time']}
        elif antimentions:
            await self.bot.db.execute("UPDATE massmention SET level = $1, time = $2 WHERE guild_id = $3", state['massmention'], state['time'], ctx.guild.id)
            self.bot.massmention[ctx.guild.id] = {'level': state['massmention'], 'limit': 5, 'time': state['time']}

        if not antilinks:
            await self.bot.db.execute("INSERT INTO links(guild_id, level, time) VALUES($1, $2, $3)", ctx.guild.id, state['links'], state['time'])
            self.bot.links[ctx.guild.id] = {'level': state['links'], 'time': state['time']}
        elif antilinks:
            await self.bot.db.execute("UPDATE links SET level = $1, time = $2 WHERE guild_id = $3", state['links'], state['time'], ctx.guild.id)
            self.bot.links[ctx.guild.id] = {'level': state['links'], 'time': state['time']}

        await ctx.send(_("{0} Successfully set the automod value to **{1}**").format(self.bot.settings['emojis']['misc']['white-mark'], value))

    @automod.command(name='anti-links', aliases=['antilinks', 'links', 'al'], brief='Toggle anti links')
    @commands.cooldown(1, 5, commands.BucketType.member)
    @admin(manage_guild=True)
    @commands.guild_only()
    async def automod_anti_links(self, ctx, value: AutomodValues):
        """" Set the automod value for anti links """

        automod = cm.get(self.bot, 'automod', ctx.guild.id)

        if not automod:
            raise commands.BadArgument(_("Automod is disabled in this server, enable it by using `{0}automod toggle` command").format(ctx.prefix))

        antilinks = cm.get(self.bot, 'links', ctx.guild.id)
        if not antilinks and value['action'] != 0:
            await self.bot.db.execute("INSERT INTO links(guild_id, level, time) VALUES($1, $2, $3)", ctx.guild.id, value['action'], value['time'])
            self.bot.links[ctx.guild.id] = {'level': value['action'], 'time': value['time']}
        elif antilinks and value['action'] != 0:
            await self.bot.db.execute("UPDATE links SET level = $1, time = $2 WHERE guild_id = $3", value['action'], value['time'], ctx.guild.id)
            self.bot.links[ctx.guild.id] = {'level': value['action'], 'time': value['time']}
        elif antilinks and value['action'] == 0:
            await self.bot.db.execute("DELETE FROM links WHERE guild_id = $1", ctx.guild.id)
            self.bot.links.pop(ctx.guild.id)
            return await ctx.send(_("{0} Successfuly disabled anti link in this server").format(self.bot.settings['emojis']['misc']['white-mark']))
        elif not antilinks and value['action'] == 0:
            raise commands.BadArgument(_("Anti link is already disabled in this server."))

        the_value = value['action']
        await ctx.send(_("{0} Successfully set anti links punishment type to **{1}** members.{2}").format(
            self.bot.settings['emojis']['misc']['white-mark'], automod_values(the_value), _(" They will be muted/banned for 12 hours by default.") if value['action'] in [5, 2] else ''
        ))

    @automod.command(name='anti-invites', aliases=['antiinvites', 'invites', 'ai'], brief="Toggle anti invites")
    @commands.cooldown(1, 5, commands.BucketType.member)
    @admin(manage_guild=True)
    @commands.guild_only()
    async def automod_anti_invites(self, ctx, value: AutomodValues):
        """" Set the automod value for anti invites """

        automod = cm.get(self.bot, 'automod', ctx.guild.id)

        if not automod:
            raise commands.BadArgument(_("Automod is disabled in this server, enable it by using `{0}automod toggle` command").format(ctx.prefix))

        antilinks = cm.get(self.bot, 'invites', ctx.guild.id)
        if not antilinks and value['action'] != 0:
            await self.bot.db.execute("INSERT INTO invites(guild_id, level, time) VALUES($1, $2, $3)", ctx.guild.id, value['action'], value['time'])
            self.bot.invites[ctx.guild.id] = {'level': value['action'], 'time': value['time']}
        elif antilinks and value['action'] != 0:
            await self.bot.db.execute("UPDATE invites SET level = $1, time = $2 WHERE guild_id = $3", value['action'], value['time'], ctx.guild.id)
            self.bot.invites[ctx.guild.id] = {'level': value['action'], 'time': value['time']}
        elif antilinks and value['action'] == 0:
            await self.bot.db.execute("DELETE FROM invites WHERE guild_id = $1", ctx.guild.id)
            self.bot.invites.pop(ctx.guild.id)
            return await ctx.send(_("{0} Successfuly disabled anti invites in this server").format(self.bot.settings['emojis']['misc']['white-mark']))
        elif not antilinks and value['action'] == 0:
            raise commands.BadArgument(_("Anti invite is already disabled in this server."))

        the_value = value['action']
        await ctx.send(_("{0} Successfully set anti invites punishment type to **{1}** members.{2}").format(
            self.bot.settings['emojis']['misc']['white-mark'], automod_values(the_value), _(" They will be muted/banned for 12 hours by default.") if value['action'] in [5, 2] else ''
        ))

    @automod.command(name='anti-mass-mention', aliases=['antimentions', 'massmentions', 'amm'], brief='Toggle anti mass mention')
    @commands.cooldown(1, 5, commands.BucketType.member)
    @admin(manage_guild=True)
    @commands.guild_only()
    async def automod_mass_mention(self, ctx, value: AutomodValues, count: int = None):
        """" Set the automod value for anti mass mention and set the mentions limit """

        automod = cm.get(self.bot, 'automod', ctx.guild.id)

        if not automod:
            raise commands.BadArgument(_("Automod is disabled in this server, enable it by using `{0}automod toggle` command").format(ctx.prefix))

        # if value['action'] != 0:
        #     raise commands.MissingRequiredArgument(self.automod_mass_mention.params['count'])

        if count and not 1 < count < 16:
            raise commands.BadArgument(_("Mentions limit must be between 2 and 15"))

        antimentions = cm.get(self.bot, 'massmention', ctx.guild.id)
        if not antimentions and value['action'] != 0:
            await self.bot.db.execute("INSERT INTO massmention(guild_id, level, mentions_limit, time) VALUES($1, $2, $3, $4)", ctx.guild.id, value['action'], count, value['time'])
            self.bot.massmention[ctx.guild.id] = {'level': value['action'], 'time': value['time'], 'limit': count}
        elif antimentions and value['action'] != 0:
            await self.bot.db.execute("UPDATE massmention SET level = $1, time = $2, mentions_limit = $3 WHERE guild_id = $4", value['action'], value['time'], count, ctx.guild.id)
            self.bot.massmention[ctx.guild.id] = {'level': value['action'], 'time': value['time'], 'limit': count}
        elif antimentions and value['action'] == 0:
            await self.bot.db.execute("DELETE FROM massmention WHERE guild_id = $1", ctx.guild.id)
            self.bot.massmention.pop(ctx.guild.id)
            return await ctx.send(_("{0} Successfuly disabled anti mass mention in this server").format(self.bot.settings['emojis']['misc']['white-mark']))
        elif not antimentions and value['action'] == 0:
            raise commands.BadArgument(_("Anti mass mentions are already disabled in this server."))

        the_value = value['action']
        await ctx.send(_("{0} Successfully set anti mass mentions punishment type to **{1}** members. Mentions limit - `{2}`.{3}").format(
            self.bot.settings['emojis']['misc']['white-mark'], automod_values(the_value), count, _(" They will be muted/banned for 12 hours by default.") if value['action'] in [5, 2] else ''
        ))

    @automod.command(name='anti-mass-caps', aliases=['anticaps', 'masscaps', 'amc'], brief="Toggle anti mass caps")
    @commands.cooldown(1, 5, commands.BucketType.member)
    @admin(manage_guild=True)
    @commands.guild_only()
    async def automod_mass_caps(self, ctx, value: AutomodValues, percentage: int = None):
        """" Set the automod value for anti mass caps and set the caps percentege limit """

        automod = cm.get(self.bot, 'automod', ctx.guild.id)

        if not automod:
            raise commands.BadArgument(_("Automod is disabled in this server, enable it by using `{0}automod toggle` command").format(ctx.prefix))

        if value['action'] != 0:
            raise commands.MissingRequiredArgument(self.automod_mass_caps.params['percentage'])

        if percentage and not 25 < percentage < 100:
            raise commands.BadArgument(_("Percentage limit must be between 25 and 100"))

        anticaps = cm.get(self.bot, 'masscaps', ctx.guild.id)
        if not anticaps and value['action'] != 0:
            await self.bot.db.execute("INSERT INTO masscaps(guild_id, level, percentage, time) VALUES($1, $2, $3, $4)", ctx.guild.id, value['action'], percentage, value['time'])
            self.bot.masscaps[ctx.guild.id] = {'level': value['action'], 'time': value['time'], 'percentage': percentage}
        elif anticaps and value['action'] != 0:
            await self.bot.db.execute("UPDATE masscaps SET level = $1, time = $2, percentage = $3 WHERE guild_id = $4", value['action'], value['time'], percentage, ctx.guild.id)
            self.bot.masscaps[ctx.guild.id] = {'level': value['action'], 'time': value['time'], 'percentage': percentage}
        elif anticaps and value['action'] == 0:
            await self.bot.db.execute("DELETE FROM masscaps WHERE guild_id = $1", ctx.guild.id)
            self.bot.masscaps.pop(ctx.guild.id)
            return await ctx.send(_("{0} Successfuly disabled anti mass caps in this server").format(self.bot.settings['emojis']['misc']['white-mark']))
        elif not anticaps and value['action'] == 0:
            raise commands.BadArgument(_("Anti caps are already disabled in this server."))

        the_value = value['action']
        await ctx.send(_("{0} Successfully set anti mass caps punishment type to **{1}** members. Percentage set to - `{2}`.{3}").format(
            self.bot.settings['emojis']['misc']['white-mark'], automod_values(the_value), percentage, _(" They will be muted/banned for 12 hours by default.") if value['action'] in [5, 2] else ''
        ))

    @automod.command(name='anti-spam', aliases=['antispam', 'spam', 'as'], brief="Toggle anti spam")
    @commands.cooldown(1, 5, commands.BucketType.member)
    @admin(manage_guild=True)
    @commands.guild_only()
    async def automod_anti_spam(self, ctx, value: AutomodValues):
        """" Set the automod value for anti spam """

        automod = cm.get(self.bot, 'automod', ctx.guild.id)

        if not automod:
            raise commands.BadArgument(_("Automod is disabled in this server, enable it by using `{0}automod toggle` command").format(ctx.prefix))

        antispam = cm.get(self.bot, 'spam', ctx.guild.id)
        if not antispam and value['action'] != 0:
            await self.bot.db.execute("INSERT INTO antispam(guild_id, level, time) VALUES($1, $2, $3)", ctx.guild.id, value['action'], value['time'])
            self.bot.spam[ctx.guild.id] = {'level': value['action'], 'time': value['time']}
        elif antispam and value['action'] != 0:
            await self.bot.db.execute("UPDATE antispam SET level = $1, time = $2 WHERE guild_id = $3", value['action'], value['time'], ctx.guild.id)
            self.bot.spam[ctx.guild.id] = {'level': value['action'], 'time': value['time']}
        elif antispam and value['action'] == 0:
            await self.bot.db.execute("DELETE FROM antispam WHERE guild_id = $1", ctx.guild.id)
            self.bot.spam.pop(ctx.guild.id)
            return await ctx.send(_("{0} Successfuly disabled anti spam in this server").format(self.bot.settings['emojis']['misc']['white-mark']))
        elif not antispam and value['action'] == 0:
            raise commands.BadArgument(_("Anti spam is already disabled in this server."))

        the_value = value['action']
        await ctx.send(_("{0} Successfully set anti spam punishment type to **{1}** members.{2}").format(
            self.bot.settings['emojis']['misc']['white-mark'], automod_values(the_value), _(" They will be muted/banned for 12 hours by default.") if value['action'] in [5, 2] else ''
        ))

    @automod.command(name='ignore-moderators', aliases=['ignoremoderators', 'ignoremods'], breif="Toggle if automod should ignore server moderators")
    @admin(manage_guild=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def automod_ignore_mods(self, ctx):
        """ Toggle whether or not bot should ignore members with manage messages permissions (moderators) """
        automod = cm.get(self.bot, 'automod', ctx.guild.id)

        if not automod:
            raise commands.BadArgument(_("Automod is disabled in this server, enable it by using `{0}automod toggle` command").format(ctx.prefix))

        if automod['ignore_admins']:
            await self.bot.db.execute("UPDATE automod SET ignore_admins = $1 WHERE guild_id = $2", False, ctx.guild.id)
            self.bot.automod[ctx.guild.id]['ignore_admins'] = False
            return await ctx.send(_("{0} I will not be ignoring people with manage messages permissions (moderators) from now on.").format(self.bot.settings['emojis']['misc']['white-mark']))
        else:
            await self.bot.db.execute("UPDATE automod SET ignore_admins = $1 WHERE guild_id = $2", True, ctx.guild.id)
            self.bot.automod[ctx.guild.id]['ignore_admins'] = True
            return await ctx.send(_("{0} I will be ignoring people with manage messages permissions (moderators) from now on.").format(self.bot.settings['emojis']['misc']['white-mark']))

    @automod.command(name='delete-messages', aliases=['deletemessages', 'deletemsgs', 'delmsgs'], brief="Toggle if automod should delete messages when punishing the user")
    @admin(manage_guild=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def automod_delete_msgs(self, ctx):
        """ Toggle whether or not bot should delete the messages """
        automod = cm.get(self.bot, 'automod', ctx.guild.id)

        if not automod:
            raise commands.BadArgument(_("Automod is disabled in this server, enable it by using `{0}automod toggle` command").format(ctx.prefix))

        if automod['delete_messages']:
            await self.bot.db.execute("UPDATE automod SET delete_messages = $1 WHERE guild_id = $2", False, ctx.guild.id)
            self.bot.automod[ctx.guild.id]['delete_messages'] = False
            return await ctx.send(_("{0} I will not be deleting messages from now on.").format(self.bot.settings['emojis']['misc']['white-mark']))
        else:
            await self.bot.db.execute("UPDATE automod SET delete_messages = $1 WHERE guild_id = $2", True, ctx.guild.id)
            self.bot.automod[ctx.guild.id]['delete_messages'] = True
            return await ctx.send(_("{0} I will now be deleting messages from now on.").format(self.bot.settings['emojis']['misc']['white-mark']))

    @commands.group(name='raid-mode', aliases=['raidmode', 'antiraid'], invoke_without_command=True, brief='Manage anti raid mode in the server')
    @admin(manage_guild=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def raid_mode(self, ctx):
        """ Main command for raid mode managing """
        await ctx.send_help(ctx.command)

    @raid_mode.command(name='toggle', brief="Toggle raid mode")
    @admin(manage_guild=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def raid_mode_toggle(self, ctx, value: str = None, channel: discord.TextChannel = None):
        """ Toggle raid mode status

        **Values:**
        `kick` - kick new members that only have their account created less than 30 days ago
        `ban` - ban new members that only have their account created less than 30 days ago
        `kickall` - kick all new members, account age doesn't matter
        `banall` - ban all new members, account age doesn't matter"""
        automod = cm.get(self.bot, 'automod', ctx.guild.id)
        raidmode = cm.get(self.bot, 'raidmode', ctx.guild.id)

        if not automod:
            raise commands.BadArgument(_("Automod is disabled in this server, enable it by using `{0}automod toggle` command").format(ctx.prefix))

        if value and value not in ['kick', 'ban', 'kickall', 'banall']:
            raise commands.BadArgument(_("Allowed values are `kick`, `ban`, `kickall` and `banall`, if you're trying to disable the raid mode, don't provide any arguments"))
        action = {
            'kick': _('kick'),
            'ban': _('ban'),
            'kickall': _('kick all'),
            'banall': _('ban all')
        }

        the_value = 1 if value == 'kick' else 2 if value == 'ban' else 3 if value == 'kickall' else 4

        if not raidmode and channel:
            if not channel.can_send or not channel.permissions_for(ctx.guild.me).embed_links:
                return await ctx.send(_("{0} I'm missing permissions in that channel. Make sure you have given me the correct permissions!").format(self.bot.settings['emojis']['misc']['warn']))
            await self.bot.db.execute("INSERT INTO raidmode(guild_id, channel_id, dm, action) VALUES($1, $2, $3, $4)", ctx.guild.id, channel.id, False, the_value)
            self.bot.raidmode[ctx.guild.id] = {'channel': channel.id, 'dm': False, 'action': the_value}
            await ctx.send(_("{0} Successfully enabled raidmode, will {1} new members {2}").format(self.bot.settings['emojis']['misc']['white-mark'], action[value], _('who have their accounts created less than 30 days ago.') if value in ['kick', 'ban'] else ''))
        elif not raidmode and not channel:
            raise commands.MissingRequiredArgument(self.raid_mode_toggle.params['channel'])
        elif raidmode and not value and not channel:
            await self.bot.db.execute("DELETE FROM raidmode WHERE guild_id = $1", ctx.guild.id)
            self.bot.raidmode.pop(ctx.guild.id)
            await ctx.send(_("{0} Successfully disabled raidmode").format(self.bot.settings['emojis']['misc']['white-mark']))
        elif raidmode and channel:
            if not channel.can_send or not channel.permissions_for(ctx.guild.me).embed_links:
                return await ctx.send(_("{0} I'm missing permissions in that channel. Make sure you have given me the correct permissions!").format(self.bot.settings['emojis']['misc']['warn']))
            await self.bot.db.execute("UPDATE raidmode SET channel_id = $1 WHERE guild_id = $2", channel.id, ctx.guild.id)
            self.bot.raidmode[ctx.guild.id]['channel'] = channel.id
            await ctx.send(_("{0} Set the new raidmode logging channel to {1}").format(self.bot.settings['emojis']['misc']['white-mark'], channel.mention))
        elif raidmode and value:
            await self.bot.db.execute("UPDATE raidmode SET action = $1 WHERE guild_id = $2", the_value, ctx.guild.id)
            self.bot.raidmode[ctx.guild.id]['action'] = the_value
            await ctx.send(_("{0} Set the raidmode action to {1} new members {2}").format(
                self.bot.settings['emojis']['misc']['white-mark'], action[value], _('who have their account created less than 30 days ago.') if value in ['kick', 'ban'] else ''
            ))

    @raid_mode.command(name='direct-message', aliases=['dm'])
    @admin(manage_guild=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def raid_mode_dm(self, ctx):
        """ Toggle if new members should get a DM from bot when getting kicked or banned """
        automod = cm.get(self.bot, 'automod', ctx.guild.id)
        raidmode = cm.get(self.bot, 'raidmode', ctx.guild.id)

        if not automod:
            raise commands.BadArgument(_("Automod is disabled in this server, enable it by using `{0}automod toggle` command").format(ctx.prefix))
        if not raidmode:
            raise commands.BadArgument(_("Raid mode is disabled in this server, enable it by using `{0}raid-mode toggle` command").format(ctx.prefix))

        if raidmode['dm']:
            await self.bot.db.execute("UPDATE raidmode SET dm = $1 WHERE guild_id = $2", False, ctx.guild.id)
            self.bot.raidmode[ctx.guild.id]['dm'] = False
            return await ctx.send(_("{0} I will not be DMing people when kicking or banning them anymore on raid.").format(self.bot.settings['emojis']['misc']['white-mark']))
        else:
            await self.bot.db.execute("UPDATE raidmode SET dm = $1 WHERE guild_id = $2", True, ctx.guild.id)
            self.bot.raidmode[ctx.guild.id]['dm'] = True
            return await ctx.send(_("{0} I will now be DMing people when kicking or banning them on raid.").format(self.bot.settings['emojis']['misc']['white-mark']))

    @commands.group(brief='Manage automod whitelist', invoke_without_command=True)
    @moderator(manage_messages=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def whitelist(self, ctx):
        await ctx.send_help(ctx.command)

    @whitelist.command(name='list', brief='A list of whitelisted stuff in this server')
    @moderator(manage_messages=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def whitelist_list(self, ctx, what: str):
        """ See a list of whitelisted roles/channels for automod
        Types: `roles`, `channels`"""

        automod = cm.get(self.bot, 'automod', ctx.guild.id)

        if not automod:
            raise commands.BadArgument(_("Automod is disabled in this server, enable it by using `{0}automod toggle` command").format(ctx.prefix))

        whitelist_list = []
        if what == 'channels':
            channels_list = cm.get(self.bot, 'channels_whitelist', ctx.guild.id)
            if not channels_list:
                return await ctx.send(_("{0} There are no whitelisted channels in the server."))

            embed_title = _("List of whitelisted channels")
            for num, channel in enumerate(channels_list, start=1):
                whitelist_list.append(f"`[{num}]` {self.bot.get_channel(channel)} ({channel})")
        elif what == 'roles':
            roles_list = cm.get(self.bot, 'channels_whitelist', ctx.guild.id)
            if not roles_list:
                return await ctx.send(_("{0} There are no whitelisted roles in the server."))

            embed_title = _("List of whitelisted roles")
            for num, role in enumerate(roles_list, start=1):
                whitelist_list.append(f"`[{num}]` {ctx.guild.get_role(role)} ({role})")

        paginator = Pages(ctx,
                          title=embed_title,
                          entries=whitelist_list,
                          thumbnail=None,
                          per_page=10,
                          embed_color=self.bot.settings['colors']['embed_color'],
                          author=ctx.author)
        await paginator.paginate()

    @whitelist.command(name='add-channel', aliases=['addchannel', 'achannel', 'channeladd'])
    @moderator(manage_channels=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def whitelist_add_channel(self, ctx, *, channel: discord.TextChannel):
        """ Add a channel to automod whitelist """
        automod = cm.get(self.bot, 'automod', ctx.guild.id)
        check = cm.get(self.bot, 'channels_whitelist', ctx.guild.id)

        if not automod:
            raise commands.BadArgument(_("Automod is disabled in this server, enable it by using `{0}automod toggle` command").format(ctx.prefix))

        if not check:
            await self.bot.db.execute("INSERT INTO whitelist(guild_id, type, _id) VALUES($1, $2, $3)", ctx.guild.id, 1, channel.id)
            self.bot.channels_whitelist[ctx.guild.id] = [channel.id]
            await ctx.send(_("{0} Added {1} to the channels whitelist.").format(self.bot.settings['emojis']['misc']['white-mark'], channel.mention))
        elif check:
            if channel.id in check:
                raise commands.BadArgument(_("Channel {0} is already added to the whitelist.").format(channel.mention))

            await self.bot.db.execute("INSERT INTO whitelist(guild_id, type, _id) VALUES($1, $2, $3)", ctx.guild.id, 1, channel.id)
            self.bot.channels_whitelist[ctx.guild.id].append(channel.id)
            await ctx.send(_("{0} Added {1} to the channels whitelist.").format(self.bot.settings['emojis']['misc']['white-mark'], channel.mention))

    @whitelist.command(name='add-role', aliases=['addrole', 'arole', 'roleadd'])
    @moderator(manage_roles=True)
    @commands.guild_only()
    @commands.cooldown(1, 5, commands.BucketType.member)
    async def whitelist_add_role(self, ctx, *, role: discord.Role):
        """ Add a channel to automod whitelist """
        automod = cm.get(self.bot, 'automod', ctx.guild.id)
        check = cm.get(self.bot, 'roles_whitelist', ctx.guild.id)

        if not automod:
            raise commands.BadArgument(_("Automod is disabled in this server, enable it by using `{0}automod toggle` command").format(ctx.prefix))

        if not check:
            await self.bot.db.execute("INSERT INTO whitelist(guild_id, type, _id) VALUES($1, $2, $3)", ctx.guild.id, 2, role.id)
            self.bot.roles_whitelist[ctx.guild.id] = [role.id]
            await ctx.send(_("{0} Added {1} to the roles whitelist.").format(self.bot.settings['emojis']['misc']['white-mark'], role.mention))
        elif check:
            if role.id in check:
                raise commands.BadArgument(_("Role **{0}** is already added to the whitelist.").format(role))

            await self.bot.db.execute("INSERT INTO whitelist(guild_id, type, _id) VALUES($1, $2, $3)", ctx.guild.id, 2, role.id)
            self.bot.roles_whitelist[ctx.guild.id].append(channel.id)
            await ctx.send(_("{0} Added {1} to the roles whitelist.").format(self.bot.settings['emojis']['misc']['white-mark'], role.mention))


def setup(bot):
    bot.add_cog(Automod(bot))
