import discord
from discord.ext import tasks
import redis

import os
import datetime
from dateutil.relativedelta import relativedelta

TOKEN = "NzE1OTQ0OTQ4MTMzNzg5ODYz.XtEmQg.mzTOYnLkmWggbsbPIDeHPBmW4mI"
CHANNEL_ID = 715947254782885951

conn = redis.from_url(
    url = os.environ.get('REDIS_URL'),
    decode_responses = True
)

client = discord.Client()

async def man(message):
    print('sending help')
    ret = 'ヘルプ\n'
    for command in COMMANDS:
        ret += '------------------------\n'
        ret += '{}: {}\n'.format('!' + command, COMMANDS[command]['description'])
        ret += '    使い方: {}\n'.format(COMMANDS[command]['use'])
        ret += '    省略形: {}\n'.format(COMMANDS[command]['alias'])
        ret += '------------------------'
    await message.channel.send(ret)

async def add(message):
    print('add assignment')
    msg = message.content.split(' ')
    try:
        title, deadline, memo = msg[1:]

        conn.hset(title, 'title', title)
        conn.hset(title, 'deadline', deadline)
        conn.hset(title, 'memo',  memo)

        await message.channel.send('課題を追加しました！')
    except:
        await message.channel.send('入力形式が間違っています。')

async def delete(message):
    print('delete assignment')
    try:
        title = message.content.split(' ')[1]
        if conn.exists(title):
            conn.delete(title)
            await message.channel.send('課題を削除しました')
        else:
            await message.channel.send('そのような課題はありません')
    except:
        await message.channel.send('入力形式が間違っています。')

async def ls(message):
    print('sending list')
    ret = '課題一覧\n'
    for i, title in enumerate(conn.keys()):
        ret += '------------------------\n'
        ret += '{}. {}\n'.format(i + 1, title)
        ret += '締切: {}\n'.format(conn.hget(title, 'deadline'))
        ret += '備考: {}\n'.format(conn.hget(title, 'memo'))
        ret += '------------------------\n'

    ret += '現在、{}個の課題が出されています。'.format(len(conn.keys()))
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
        'use': '!add \{課題名\} \{締切\} \{備考\}',
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
    }
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


@tasks.loop(hours=5)
async def loop():
    print("sending notification")
    today = datetime.datetime.now()
    tommorow = today + relativedelta(days=1)
    three_days_later = tommorow + relativedelta(days=2)
    remain_1day = []
    remain_3day = []

    for title in conn.keys():
        deadline_str = str(tommorow.year) + '/' + conn.hget(title, 'deadline')
        deadline = datetime.datetime.strptime(deadline_str, '%Y/%m/%d')
        if deadline < today:
            conn.hdel(title)
        elif deadline <= tommorow:
            remain_1day.append(title)
        elif deadline <= three_days_later:
            remain_3day.append(title)

    if len(remain_1day)+len(remain_3day)==0:
        return

    ret = '{}個の課題の提出期限が迫っています！\n'.format(len(remain_1day)+len(remain_3day))
    for i, title in enumerate(remain_3day):
        ret += '------------------------\n'
        ret += '{}. {}\n'.format(i + 1, title)
        ret += '締切: {}\n'.format(conn.hget(title, 'deadline'))
        ret += '備考: {}\n'.format(conn.hget(title, 'memo'))
        ret += '------------------------\n'
    if remain_1day:
        ret += '↓↓↓あと1日もないよ↓↓↓\n'
    for i, title in enumerate(remain_1day):
        ret += '------------------------\n'
        ret += '{}. {}\n'.format(i + 1, title)
        ret += '締切: {}\n'.format(conn.hget(title, 'deadline'))
        ret += '備考: {}\n'.format(conn.hget(title, 'memo'))
        ret += '------------------------\n'
        

    channel = client.get_channel(CHANNEL_ID)
    await channel.send(ret)



client.run(TOKEN)
