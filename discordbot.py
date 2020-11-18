import discord
from discord.ext import tasks, commands
import logging
import redis

import os
import datetime
from dateutil.relativedelta import relativedelta


TOKEN = os.environ.get('BOT_TOKEN')
GUILD_ID = int(os.environ.get('KADAI_GUILD_ID'))
LOOP_DURATION = int(os.environ.get('KADAI_LOOP_DURATION'))


conn = redis.from_url(
	url = os.environ.get('REDIS_URL'),
	decode_responses = True
)

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents=intents)
logging.basicConfig(level=logging.ERROR)
bot.remove_command('help')


# (コマンド名, 説明, 呼び出し例, エイリアス)
COMMANDS = [
	('help', 'このリストを表示します。', '!help', '!h'),
	('add', '新しい課題を追加します。\n\t締切年省略可(課題を追加した年になります)', '!add \{課題名\} \{締切(年/月/日)\} \{備考(任意)\}', '!a'),
	('delete',  '課題を削除します。', '!delete \{課題名\}', '!del'),
	('list', '登録されている課題一覧を表示します。', '!list', '!ls'),
	('\_\_exit', 'Botを終了します。(非推奨)', '!\_\_exit', '!\_\_ex')
]


# member.mention の '!','&','#' などの特殊文字を除外したものを返す
def get_id(member):
	ret = list(member.mention)
	if ret[2] in ('!', '&'):
		del ret[2]
	return "".join(ret)


@bot.command(aliases=['h'])
async def help(ctx):
	print('!help called')
	ret = 'ヘルプ\n'
	for command, description, use, alias in COMMANDS:
		ret += '------------------------\n'
		ret += f'!{command}: {description}\n'
		ret += f'	使い方: {use}\n'
		ret += f'	省略形: {alias}\n'
		ret += '------------------------'
	await ctx.send(ret)


@bot.command(aliases=['a'])
async def add(ctx, title, deadline, *memo):
	print('!add called')
	memo = " ".join(memo)

	if deadline.count('/')==1:
		deadline = str(datetime.datetime.now().year) + '/' + deadline
	try:
		datetime.datetime.strptime(deadline, '%Y/%m/%d')
	except:
		print(f'failed to add assignment: {ctx.message.content}')
		await ctx.send(f'無効な日付です。: {ctx.message.content}')
		return
	
	user = get_id(ctx.author)
	conn.hset(user, title, deadline + ',' + memo)
	print(f'add assignment: {title} {deadline} {memo}')
	await ctx.send('課題を追加しました！: ' + title)

@add.error
async def add_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		print(f'failed to add assignment: {ctx.message.content}')
		await ctx.send('入力形式が間違っています。')


@bot.command(aliases=['del'])
async def delete(ctx, req_title):
	user = get_id(ctx.author)
	for title in conn.hkeys(user):
		if req_title==title:
			conn.hdel(user, title)
			print(f'delete assignment: {title}')
			await ctx.send('課題を削除しました！: ' + title)
			break
	else:
		print(f'failed to delete assignment: {req_title}')
		await ctx.send('そのような課題はありません: ' + req_title)

@delete.error
async def delete_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		print(f'failed to delete assignment: {ctx.message.content}')
		await ctx.send('入力形式が間違っています。')


@bot.command(aliases=['list'])
async def ls(ctx):
	print('!ls called')
	user = get_id(ctx.author)
	cnt = 0
	ret = '課題一覧\n'
	for i, title in enumerate(conn.hkeys(user)):
		deadline, memo = conn.hget(user, title).split(',')
		ret += '------------------------\n'
		ret += f'{cnt+1}. {title}\n'
		ret += f'締切: {deadline}\n'
		ret += f'備考: {memo}\n'
		ret += '------------------------\n'
		cnt += 1
	ret += f'現在、{cnt}個の課題が出されています。'
	print('sent list')
	await ctx.send(ret)


@bot.command(name='__exit', aliases=['__ex'])
async def close_client(ctx):
	print('I\'ll be back')
	await bot.close()



@bot.event
async def on_ready():
	print('I\'m ready')
	await loop.start()


@tasks.loop(hours=LOOP_DURATION)
async def loop():
	today = datetime.datetime.now() # + relativedelta(hours=9)
	tommorow = today + relativedelta(days=1)
	three_days_later = today + relativedelta(days=3)
	print('In loop! at', today.strftime('%Y/%m/%d %H:%M'))

	guild_members = set()
	for guild in bot.guilds:
		guild_members.update(guild.members)

	for mem in guild_members:
		if mem.bot:
			continue

		remain_1day = []
		remain_3day = []
		user = get_id(mem)
		
		for title in conn.hkeys(user):
			deadline, memo = conn.hget(user, title).split(',')
			deadline = datetime.datetime.strptime(deadline, '%Y/%m/%d')

			if deadline < today:
				conn.hdel(user, title)
				print(f'delete assignment because of its deadline is over: {title}')
				continue
			elif deadline <= tommorow:
				remain_1day.append(title)
			elif deadline <= three_days_later:
				remain_3day.append(title)

		count = len(remain_1day) + len(remain_3day)
		if count==0:
			print(f'No notification sent to {mem.name}')
			continue

		ret = '{}個の課題の提出期限が迫っています！\n'.format(count)
		for i, title in enumerate(remain_3day):
			deadline, memo = conn.hget(user, title).split(',')
			ret += '------------------------\n'
			ret += f'{i+1}. {title}\n'
			ret += f'締切: {deadline}\n'
			ret += f'備考: {memo}\n'
			ret += '------------------------\n'

		if remain_1day:
			ret += '↓↓↓あと1日もないよ↓↓↓\n'
		for i, title in enumerate(remain_1day):
			deadline, memo = conn.hget(user, title).split(',')
			ret += '------------------------\n'
			ret += f'{i+1}. {title}\n'
			ret += f'締切: {deadline}\n'
			ret += f'備考: {memo}\n'
			ret += '------------------------\n'

		if mem.dm_channel==None:
			await mem.create_dm()
		print(f'{count} notification sent to {mem.name}')
		await mem.dm_channel.send(ret)
	print('done sending notificaton')


bot.run(TOKEN)
