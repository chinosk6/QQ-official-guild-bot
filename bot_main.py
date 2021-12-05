import bot_api

bot = bot_api.BotApp(123456, "你的bot token", "你的bot secret",
                     is_sandbox=True, debug=True, api_return_pydantic=True,
                     inters=[bot_api.Intents.GUILDS, bot_api.Intents.AT_MESSAGES, bot_api.Intents.GUILD_MEMBERS])


@bot.receiver(bot_api.structs.Codes.SeverCode.BotGroupAtMessage)
def get_at_message(chain: bot_api.structs.Message):
    bot.logger(f"收到来自频道:{chain.guild_id} 子频道: {chain.channel_id} "
               f"内用户: {chain.author.username}({chain.author.id}) 的消息: {chain.content} ({chain.id})")

    if "你好" in chain.content:
        bot.api_send_reply_message(chain.channel_id, chain.id, "hello world!")
    elif "test" in chain.content:
        bot.api_send_reply_message(chain.channel_id, chain.id, "chieri在哟~")
    elif "/echo" in chain.content:
        reply = chain.content[chain.content.find("/echo") + len("/echo"):].strip()

        bot.api_send_reply_message(chain.channel_id, chain.id, reply)



bot.start()
