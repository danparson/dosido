# Dosido - A Solresol-related Discord bot
# Project website: https://www.sidosi.org/dosido
# Copyright (C) 2018 Dan Parson (https://www.danparson.com)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import asyncio
import logging
import os
import pickle
from textwrap import dedent

import discord
import requests
from discord.ext.commands import Bot

import config

RELEASE_VERSION = '0.1.0'
BOT_PREFIX = '!'
ANNOUNCED_POSTS_FILE = 'announced_posts.pkl'

bot = Bot(command_prefix=BOT_PREFIX)

logging.basicConfig(filename='dosido.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')


# Check if there are new unannounced Reddit posts. If so, announce them.
async def get_new_posts():
    await bot.wait_until_ready()
    while not bot.is_closed:
        logging.info('Checking for new posts')
        channel = discord.Object(id=config.REDDIT_CHANNEL_ID)

        # Create announced posts file if it doesn't exist
        if not os.path.isfile(ANNOUNCED_POSTS_FILE):
            open(ANNOUNCED_POSTS_FILE, 'x').close()

        with open(ANNOUNCED_POSTS_FILE, 'rb+') as fp:

            # Try to load announced posts
            try:
                announced_posts = pickle.load(fp)
            except EOFError:
                announced_posts = []

            url = 'https://www.reddit.com/r/sidosisolresol.json'
            response = requests.get(url, headers={'User-agent': 'Dosido Discord Bot'})
            value = response.json()['data']['children']
            posts = sorted(value, key=lambda k: k['data']['created'])

            for post in posts:
                logging.debug('Checking if {post_id} is in {announced_posts}'.format(post_id=post['data']['id'],
                                                                                     announced_posts=announced_posts))

                # Build message and announce post
                if post['data']['id'] not in announced_posts:
                    comments_url = 'https://redd.it/{post_id}'.format(post_id=post['data']['id'])
                    message = '**{title}** submitted by {author}\n'.format(title=post['data']['title'],
                                                                           author=post['data']['author'])
                    logging.info('New post: {post_url}'.format(post_url=comments_url))

                    # Hide link for self (text) posts
                    if not post['data']['is_self']:
                        message += 'Link: {post_url}\n'.format(post_url=post['data']['url'])

                    message += 'Comments: {comments_url}\n'.format(comments_url=comments_url)
                    await bot.send_message(channel, message)
                    announced_posts.append(post['data']['id'])

            # Save newly announced posts
            pickle.dump(announced_posts, fp)

        await asyncio.sleep(60)


@bot.event
async def on_ready():
    print('Logged in as {bot_user_name} ({bot_user_id})'.format(bot_user_name=bot.user.name, bot_user_id=bot.user.id))
    bot.loop.create_task(get_new_posts())


# Replies "Pong!"
@bot.command()
async def ping():
    logging.info('Received command: ping')
    await bot.say('Pong!')


# Greets the user in Solresol
@bot.command(pass_context=True)
async def simi(ctx):
    logging.info('Received command: simi')
    await bot.say('Simi, {author}! Redofafa?'.format(author=ctx.message.author.mention))


# Shows info about the bot
@bot.command()
async def about():
    logging.info('Received command about')
    await bot.say(dedent('''\
        Dosido v{version}, official bot of La Lasîrela (The Solresol Network)
        Licensed by Dan Parson under the terms of the GNU AGPLv3
        Project website: https://www.sidosi.org/dosido
        ''').format(version=RELEASE_VERSION))


bot.run(config.DISCORD_TOKEN)
