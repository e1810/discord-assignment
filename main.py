import discord

TOKEN = "NzE1OTQ0OTQ4MTMzNzg5ODYz.XtEmQg.mzTOYnLkmWggbsbPIDeHPBmW4mI"

client =  discord.Client()

subjects = {
    "実験": [
        ["直列共振","6/6"]
    ]
}

async def ls():
    ret = "kadai\n"
    for subname, kadais in subjects.items():
        ret += subname + "\n"
        for name, deadline in kadais:
            ret += "    " + name + " : ~" + deadline + "\n"
    await message.channel.send(ret)

async def add(sub, hw, dl):
    subjects[sub].append([hw, dl])
    await message.channel.send(f"add: {hw} {sub}\n")


@client.event
async def on_message(message):
    if message.author.bot: return
    msg = message.content.split()
    
    if msg[0]=='!ls':
        ls()

    if msg[0]=='!add':
        if len(msg)!=4:
            await message.channel.send("add: 3 args required")
        add(*msg[1:])    


client.run(TOKEN)
