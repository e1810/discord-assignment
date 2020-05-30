import discord
import redis
import os

TOKEN = "NzE1OTQ0OTQ4MTMzNzg5ODYz.XtEmQg.mzTOYnLkmWggbsbPIDeHPBmW4mI"

conn = redis.from_url(
    url = os.environ.get('REDIS_URL'),
    decode_responses = True
)

client = discord.Client()

async def man(message):
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
    try:
        title, deadline, memo = msg[1:]

        conn.hset(title, 'title', title)
        conn.hset(title, 'deadline', deadline)
        conn.hset(title, 'memo',  memo)

        await message.channel.send('課題を追加しました！')
    except:
        await message.channel.send('入力形式が間違っています。')

async def delete(message):
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

@client.event
async def on_message(message):
    msg = message.content.split(' ')

    if message.author.bot:
        return

    for command in COMMANDS:
        if msg[0] in ['!' + command, COMMANDS[command]['alias']]:
            await COMMANDS[command]['func'](message)

client.run(TOKEN)
