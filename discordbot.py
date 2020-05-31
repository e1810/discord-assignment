import discord
from discord.ext import tasks
import redis

import os
import datetime
from dateutil.relativedelta import relativedelta

TOKEN = "NzE1OTQ0OTQ4MTMzNzg5ODYz.XtIRiA.MVya_72oPtVODEGze6jxBNYhR68"
GUILD_ID = 715947254782885948
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
    msg = message.content.split(' ')

    if len(msg) == 4:
        title, deadline, memo = msg[1:]
        key = title + message.author.mention
        conn.hset(key, 'title', title)
        conn.hset(key, 'deadline', deadline)
        conn.hset(key, 'memo',  memo)
        conn.hset(key, 'target', message.author.mention)
        print('add assignment {}'.format(key))
        await message.channel.send('課題を追加しました！')
    elif len(msg) == 5:
        title, deadline, memo, target = msg[1:]
        key = title + target
        conn.hset(key, 'title', title)
        conn.hset(key, 'deadline', deadline)
        conn.hset(key, 'memo', memo)
        conn.hset(key, 'target', target)
        print('add assignment {}'.format(key))
        await message.channel.send('課題を追加しました！')
    else:
        print('failed to add assignment: {}'.format(message.content))
        await message.channel.send('入力形式が間違っています。')


async def delete(message):
    try:
        title = message.content.split(' ')[1]
        key = title.message.author.mention
        if conn.exists(key):
            conn.delete(key)
            print('delete assignment: {}'.format(key))
            await message.channel.send('課題を削除しました')
        elif conn.exists(title+'@everyone'):
            conn.delete(title+'@everyone')
            print('delete assignment: {}'.format(title+'@everyone'))
            await message.channel.send('課題を削除しました')
        else:
            print('failed to delete assignment: {}'.format(message.content))
            await message.channel.send('そのような課題はありません')
    except:
        print('failed to delete assignment: {}'.format(message.content))
        await message.channel.send('入力形式が間違っています。')


async def ls(message):
    print('sending list')
    cnt = 0
    ret = '課題一覧\n'
    for i, key in enumerate(conn.keys()):
        if conn.hget(key, 'target') in (message.author.mention, '@everyone'):
            ret += '------------------------\n'
            ret += '{}. {}\n'.format(cnt + 1, conn.hget(key, 'title'))
            ret += '締切: {}\n'.format(conn.hget(key, 'deadline'))
            ret += '備考: {}\n'.format(conn.hget(key, 'memo'))
            ret += '------------------------\n'
            cnt += 1
    ret += '現在、{}個の課題が出されています。'.format(cnt)
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


@tasks.loop(hours=5)
async def loop():
    print("sending notification")
    today = datetime.datetime.now() + relativedelta(hours=9)
    tommorow = today + relativedelta(days=1)
    three_days_later = tommorow + relativedelta(days=2)
    remain_1day = []
    remain_3day = []
    guild = client.get_guild(GUILD_ID)

    for key in conn.keys():
        target = conn.hget(key, 'target')
        exist = (target == '@everyone')
        for mem in guild.members:
            if target==mem.mention:
                exist = True
        if not exist:
            print('delete {} because of undefined mention'.format(key))
            conn.delete(key)
            continue

        deadline_str = str(tommorow.year) + '/' + conn.hget(key, 'deadline')
        deadline = datetime.datetime.strptime(deadline_str, '%Y/%m/%d')
        if deadline < today:
            conn.delete(key)
            print('delete {} because of deadline'.format(key)) 
        elif deadline <= tommorow:
            remain_1day.append(key)
        elif deadline <= three_days_later:
            remain_3day.append(key)

    if len(remain_1day)+len(remain_3day)==0:
        return

    ret = '{}個の課題の提出期限が迫っています！\n'.format(len(remain_1day)+len(remain_3day))
    for i, key in enumerate(remain_3day):
        ret += '------------------------\n'
        ret += '{}. {}\n'.format(i + 1, key)
        ret += '締切: {}\n'.format(conn.hget(key, 'deadline'))
        ret += '備考: {}\n'.format(conn.hget(key, 'memo'))
        ret += '------------------------\n'

    if remain_1day:
        ret += '↓↓↓あと1日もないよ↓↓↓\n'
    for i, key in enumerate(remain_1day):
        ret += '------------------------\n'
        ret += '{}. {}\n'.format(i + 1, key)
        ret += '締切: {}\n'.format(conn.hget(key, 'deadline'))
        ret += '備考: {}\n'.format(conn.hget(key, 'memo'))
        ret += '------------------------\n'
        

    channel = client.get_channel(CHANNEL_ID)
    await channel.send(ret)



client.run(TOKEN)
