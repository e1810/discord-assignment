import discord
import redis
import os

TOKEN = "NzE1OTQ0OTQ4MTMzNzg5ODYz.XtEmQg.mzTOYnLkmWggbsbPIDeHPBmW4mI"

conn = redis.from_url(
    url = os.environ.get('REDIS_URL')
    decode_responses = True
)

client = discord.Client()

async def kadaihelp(message):
    string = 'コマンドリスト\n'
    for command in COMMANDS:
        string += '------------------------\n'
        string += '{}: {}\n'.format('!' + command, COMMANDS[command]['description'])
        string += '    使い方: {}\n'.format(COMMANDS[command]['use'])
        string += '    省略形: {}\n'.format(COMMANDS[command]['alias'])
        string += '------------------------'

    await message.channel.send(string)

async def newkadai(message):
    msg = message.content.split(' ')
    try:
        title, deadline, memo = msg[1:]

        conn.hset(title, 'title', title)
        conn.hset(title, 'deadline', deadline)
        conn.hset(title, 'memo',  memo)

        await message.channel.send('課題を追加しました！')
    except:
        await message.channel.send('入力形式が間違っています。')

async def deletekadai(message):
    try:
        title = message.content.split(' ')[1]
        if conn.exists(title):
            conn.delete(title)
            await message.channel.send('課題を削除しました')
        else:
            await message.channel.send('そのような課題はありません')
    except:
        await message.channel.send('入力形式が間違っています。')

async def kadailist(message):
    string = '課題一覧\n'
    for i, title in enumerate(conn.keys()):
        string += '------------------------\n'
        string += '{}. {}\n'.format(i + 1, title)
        string += '締切: {}\n'.format(conn.hget(title, 'deadline'))
        string += '備考: {}\n'.format(conn.hget(title, 'memo'))
        string += '------------------------\n'

    string += '現在、{}個の課題が出されています。'.format(len(conn.keys()))
    await message.channel.send(string)

async def close(message):
    await client.close()

COMMANDS = {
    'kadaihelp': {
        'description': 'このリストを表示します。',
        'use': '!kadaihelp',
        'alias': '!kh',
        'func': kadaihelp
    },
    'newkadai': {
        'description': '新しい課題を追加します。',
        'use': '!newkadai \{タイトル\} \{締切\} \{備考\}',
        'alias': '!nk',
        'func': newkadai
    },
    'deletekadai': {
        'description': '課題削除',
        'use': '!deletekadai \{課題名\}',
        'alias': '!dk',
        'func': deletekadai
    },
    'kadailist': {
        'description': '登録されている課題一覧を表示します。',
        'use': '!kadailist',
        'alias': '!kl',
        'func': kadailist
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
    print('KadaiShosu起動')

@client.event
async def on_message(message):
    msg = message.content.split(' ')

    if message.author.bot:
        return

    for command in COMMANDS:
        if msg[0] in ['!' + command, COMMANDS[command]['alias']]:
            await COMMANDS[command]['func'](message)

client.run(TOKEN)
