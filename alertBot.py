import os
import csv
import discord
import asyncio

from itertools import islice
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all(), help_command=None)
client = discord.Client()

channels = []
msg_check_strings = ['@everyone']


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.send("You do not have the correct role for this command.")


@bot.command(name='add')
async def add(ctx, address):
    with open('walletAlertBotWallets.txt', 'r') as f:
        reader = csv.reader(f)
        wallets = {rows[0]: rows[1] for rows in reader}

    with open('walletAlertBotWallets.txt', 'a') as f:
        if address in wallets:
            await ctx.send("Wallet is already registered.")
        else:
            f.write(f"{address},{ctx.message.author.id}\n")
            await ctx.send(f"Address added: {address}")


@bot.command(name='remove')
async def remove(ctx, address):
    with open('walletAlertBotWallets.txt', 'r') as f:
        lines = f.readlines()

    address_registered = False

    for line in lines:
        if line.split(',', 1)[0] == address:
            address_registered = True
            break

    if address_registered:
        with open('walletAlertBotWallets.txt', 'w') as f:
            for line in lines:
                if line.strip('\n') != f'{address},{ctx.message.author.id}':
                    f.write(line)
        await ctx.send(f"Address removed: {address}")

    elif not address_registered:
        await ctx.send(f"Address: {address} is not a registered address.")


@bot.command(name='check')
async def check(ctx):
    with open('walletAlertBotWallets.txt', 'r') as f:
        reader = csv.reader(f)
        wallets = {rows[0]: rows[1] for rows in reader}
        my_wallets = []
        await ctx.send("The following wallets are registered to you:")
        for key in wallets:
            if wallets[key] == str(ctx.message.author.id):
                my_wallets.append(key)
                await ctx.send(key)


@bot.command(name='admin_add_wallet')
@commands.has_role('alert_bot_admin')
async def admin_add_wallet(ctx, address, userid):
    with open('walletAlertBotWallets.txt', 'r') as f:
        reader = csv.reader(f)
        wallets = {rows[0]: rows[1] for rows in reader}

    with open('walletAlertBotWallets.txt', 'a') as f:
        if address in wallets:
            await ctx.send("Wallet is already registered.")
        else:
            f.write(f'{address},{userid}\n')

            await ctx.send(f"Address added: {address}\n\n"
                           f"To userID: {userid}")

            await bot.get_user(int(userid)).send(f"The following address was registered to "
                                                 f"your discord account by an admin:\n"
                                                 f"{address}")


@bot.command(name='admin_remove_wallet')
@commands.has_role('alert_bot_admin')
async def admin_remove_wallet(ctx, address):
    with open('walletAlertBotWallets.txt', 'r') as f:
        lines = f.readlines()

    address_registered = False

    for line in lines:
        if line.split(',', 1)[0] == address:
            address_registered = True
            break

    if address_registered:
        with open('walletAlertBotWallets.txt', 'w') as f:
            for line in lines:
                if line.split(',', 1)[0] != address:
                    f.write(line)
                removed_id = line.split(',', 1)[1]
        await ctx.send((f"Address removed: {address}\n\n"
                        f"Address was registered to userID: {removed_id}"))
        await bot.get_user(int(removed_id)).send(f"The following address was deregistered from "
                                                 f"your discord account by an admin:\n"
                                                 f"{address}")
    elif not address_registered:
        await ctx.send(f"Address: {address} is not a registered address.")


@bot.command(name='admin_check_wallets')
@commands.has_role('alert_bot_admin')
async def admin_check_wallets(ctx):
    with open('walletAlertBotWallets.txt', 'r') as f:
        reader = csv.reader(f)
        wallets = {rows[0]: rows[1] for rows in reader}

        await ctx.send("Discord messages are limited to 2,000 characters "
                       "which means this command will return every wallet "
                       "- owner pair registered 29 items per message.\n"
                       "If a large quantity of addresses are registered this "
                       "may take a minute to finish sending.\n\n"
                       "Messages will begin sending in a few seconds.")

        await asyncio.sleep(10)

        for item in admin_check_splitter(wallets, 29):
            await ctx.send(item)

        await ctx.send("It is recommended you copy and paste the data into "
                       "another programme such as notepad++ if you want it "
                       "to be more readable.")


@bot.command(name='admin_add_channel')
@commands.has_role('alert_bot_admin')
async def admin_add_channel(ctx, channel_id):
    if channel_id.isdigit():
        with open('walletAlertChannels.txt', 'r') as f:
            saved_channels = f.readlines()

        with open('walletAlertChannels.txt', 'a') as f:
            if (channel_id + '\n') in saved_channels:
                await ctx.send(f"Channel: {bot.get_channel(int(channel_id))} ({channel_id}) is already registered.")
            else:
                f.write(f'{channel_id}\n')
                await ctx.send(f"Channel: {bot.get_channel(int(channel_id))} ({channel_id}) has been registered.")
        load_channels()
    else:
        await ctx.send("The channel id you have entered appears to contain letters or symbols. "
                       "Discord channel id's should only contain numbers.")


@bot.command(name='admin_remove_channel')
@commands.has_role('alert_bot_admin')
async def admin_remove_channel(ctx, channel_id):
    with open('walletAlertChannels.txt', 'r') as f:
        saved_channels = f.readlines()

    channel_registered = False

    for ch in saved_channels:
        if ch.strip('\n') == channel_id:
            channel_registered = True
            break

    if channel_registered:
        with open('walletAlertChannels.txt', 'w') as f:
            for ch in saved_channels:
                if int(ch) != int(channel_id):
                    f.write(ch)
            await ctx.send(f"Channel: {bot.get_channel(int(channel_id))} ({channel_id}) has been deregistered.")
    elif not channel_registered:
        await ctx.send(f"{channel_id} is not a registered channel.")
        if not channel_id.isdigit():
            await ctx.send("The channel id you have entered appears to contain letters or symbols. "
                           "Discord channel id's should only contain numbers.")

    load_channels()


@bot.command(name='admin_check_channels')
@commands.has_role('alert_bot_admin')
async def admin_check_channels(ctx):
    with open('walletAlertChannels.txt', 'r') as f:
        saved_channels = f.readlines()

    for ch in saved_channels:
        await ctx.send(f"{bot.get_channel(int(ch))} id: {ch}")


@bot.event
async def on_message(message):
    if message.channel.id in channels:
        for item in msg_check_strings:
            if message.content.startswith(item):
                with open('walletAlertBotWallets.txt', 'r') as f:
                    reader = csv.reader(f)
                    wallets = {rows[0]: rows[1] for rows in reader}

                words = str(message.content).split()
                for word in words:
                    if word in wallets:
                        user = message.guild.get_member(int(wallets[word]))
                        await user.send(f"Your wallet: {word} has been mentioned in {message.channel.name} "
                                        f"at {str(message.created_at)[:16]}.")

    await bot.process_commands(message)


@bot.command()
async def help(ctx):
    await ctx.send("Thanks for using the Wallet Alert Bot!\n\n"
                   "When a wallet you register is mentioned in the announcements channel \n"
                   "you will receive a message from the Wallet Alert Bot to notify you of this.\n\n"
                   "The commands are as follows:\n\n"
                   "!add <wallet address> to register a wallet for alerts.\n\n"
                   "!remove <wallet address> to deregister a wallet for alerts.\n\n"
                   "!check to see all the wallets you have registered for alerts.\n\n"
                   "Do not include the < > around your wallet address.\n\n"
                   "You can register as many wallets as you want however, \n"
                   "a wallet can only be registered to one owner.\n\n"
                   "If you are trying to register a wallet you own and it is already \n"
                   "registered message: Samuel13 or D3f3ctiv3 for help.")


@bot.command()
@commands.has_role('bot_admin')
async def admin_help(ctx):
    await ctx.send("Admin commands are as follows:\n\n"
                   "!admin_add_wallet <wallet_address> <discord_id>\n"
                   "Registers a wallet address to a particular discord ID.\n\n"
                   "!admin_remove_wallet <wallet address>\n"
                   "Deregisters a wallet without the need for the associated discord ID.\n\n"
                   "!admin_check_wallets\n"
                   "Returns a list of all wallet address - discord ID pairs.\n\n"
                   "!admin_add_channel <channel id>\n"
                   "Adds a discord channel to check for wallet mentions.\n\n"
                   "!admin_remove_channel <channel id>\n"
                   "Removes a discord channel to check for wallet mentions.\n\n"
                   "!admin_check_channels\n"
                   "Returns a list of channels that are registered to check for wallet mentions.\n")


def admin_check_splitter(data, size=10000):
    it = iter(data)
    for i in range(0, len(data), size):
        yield {k: data[k] for k in islice(it, size)}


def load_channels():
    with open('walletAlertChannels.txt', 'r') as f:
        saved_channels = f.readlines()

        channels.clear()

        for channel in saved_channels:
            channels.append(channel.strip('\n'))


load_channels()
bot.run(TOKEN)
