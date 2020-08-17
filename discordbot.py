import discord
from discord.ext import tasks
import redis

import os
import datetime
from dateutil.relativedelta import relativedelta

TOKEN = os.environ.get('BOT_TOKEN')
GUILD_ID = int(os.environ.get('KADAI_GUILD_ID'))

conn = redis.from_url(
    url = os.environ.get('REDIS_URL'),
    decode_responses = True
)

client = discord.Client()

async def man(message):
    print('!help called')
    ret = 'ヘルプ\n'
    for command in COMMANDS:
        ret += '------------------------\n'
        ret += '{}: {}\n'.format('!' + command, COMMANDS[command]['description'])
        ret += '    使い方: {}\n'.format(COMMANDS[command]['use'])
        ret += '    省略形: {}\n'.format(COMMANDS[command]['alias'])
        ret += '------------------------'
    await message.channel.send(ret)


async def add(message):
    print('!add called')
    msg = message.content.split()

    if len(msg) == 4:
        title, deadline, memo = msg[1:]
        user = message.author.mention
        conn.hset(user, title, deadline + ',' + memo)
        print(f'add assignment {message.content}')
        await message.channel.send('課題を追加しました！: ' + title)

    else:
        print(f'failed to add assignment: {message.content}')
        await message.channel.send('入力形式が間違っています。')


async def delete(message):
    msg = message.content.split()
    if len(msg)==2:
        req_title = msg[1]
        user = message.author.mention
        for title in conn.hkeys(user):
            if req_title==title:
                conn.delete(user, title)
                print(f'delete assignment: {title}')
                await message.channel.send('課題を削除しました！: ' + title)
                break
        else:
            print(f'failed to delete assignment: {message.content}')
            await message.channel.send('そのような課題はありません: ' + req_title)

    else:
        print(f'failed to delete assignment: {message.content}')
        await message.channel.send('入力形式が間違っています。')


async def ls(message):
    print('!ls called')
    user = message.author.mention
    cnt = 0
    ret = '課題一覧\n'
    for i, title in enumerate(conn.hkeys(user)):
        deadline, memo = conn.hget(user, title).split(',')
        ret += '------------------------\n'
        ret += '{}. {}\n'.format(cnt + 1, title)
        ret += '締切: {}\n'.format(deadline)
        ret += '備考: {}\n'.format(memo)
        ret += '------------------------\n'
        cnt += 1
    ret += '現在、{}個の課題が出されています。'.format(cnt)
    print('sent list')
    await message.channel.send(ret)


async def close(message):
    print('I\'ll be back')
    await client.close()


COMMANDS = {
    'help': {
        'description': 'このリストを表示します。',
        'use': '!help',
        'alias': '!h',
        'func': man
    },
    'add': {
        'description': '新しい課題を追加します。',
        'use': '!add \{課題名\} \{締切\} \{備考\} \{課題対象の生徒\}',
        'alias': '!a',
        'func': add
    },
    'delete': {
        'description': '課題削除',
        'use': '!delete \{課題名\}',
        'alias': '!del',
        'func': delete
    },
    'list': {
        'description': '登録されている課題一覧を表示します。',
        'use': '!list',
        'alias': '!ls',
        'func': ls
    },
    'exit': {
        'description': 'Botを終了します。',
        'use': '!exit',
        'alias': '!ex',
        'func': close
    },
}


@client.event
async def on_ready():
    print('I\'m ready')
    await loop.start()


@client.event
async def on_message(message):
    msg = message.content.split(' ')

    if message.author.bot:
        return

    for command in COMMANDS:
        if msg[0] in ['!' + command, COMMANDS[command]['alias']]:
            await COMMANDS[command]['func'](message)
            break
    else:
        if msg[0][0]=='!':
            await message.channel.send('そのようなコマンドはありません')


@tasks.loop(hours=5)
async def loop():
    print('In loop!')
    today = datetime.datetime.now() + relativedelta(hours=9)
    tommorow = today + relativedelta(days=1)
    three_days_later = today + relativedelta(days=3)
    remain_1day = []
    remain_3day = []

    guild = client.get_guild(GUILD_ID)
    for user in guild.members:
        for title in conn.hkeys(user):
            deadline, memo = conn.hget(user, title)
            deadline_str = str(tommorow.year) + '/' + deadline
            deadline = datetime.datetime.strptime(deadline_str, '%Y/%m/%d')
            
            if deadline < today:
                conn.delete(user, title)
                continue
            elif deadline <= tommorow:
                remain_1day.append(title)
            elif deadline <= three_days_later:
                remain_3day.append(title)

        ret = '{}個の課題の提出期限が迫っています！\n'.format(len(remain_1day)+len(remain_3day))
        for i, title in enumerate(remain_3day):
            deadline, memo = conn.hget(user, title)
            ret += '------------------------\n'
            ret += '{}. {}\n'.format(i + 1, title)
            ret += '締切: {}\n'.format(deadline)
            ret += '備考: {}\n'.format(memo)
            ret += '------------------------\n'

        if remain_1day:
            ret += '↓↓↓あと1日もないよ↓↓↓\n'
        for i, title in enumerate(remain_1day):
            deadline, memo = conn.hget(user, title)
            ret += '------------------------\n'
            ret += '{}. {}\n'.format(i + 1, title)
            ret += '締切: {}\n'.format(deadline)
            ret += '備考: {}\n'.format(memo)
            ret += '------------------------\n'

        await user.send(ret)
    print('notificaton sent')


client.run(TOKEN)
