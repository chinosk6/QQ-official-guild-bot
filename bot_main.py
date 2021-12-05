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


@bot.receiver(bot_api.structs.Codes.SeverCode.image_to_url)  # 注册一个图片转url方法
def img_to_url(img_path: str):
    # 用处: 发送图片时, 使用图片cq码[CQ:image,file=]或[CQ:image,url=]
    # 装饰器作用为: 解析cq码中图片的路径(网络图片则下载到本地), 将绝对路径传给本函数, 自行操作后, 返回图片url, sdk将使用此url发送图片
    # 若不注册此方法, 则无法发送图片。
    print(img_path)
    return "https://你的图片url"

# 注册事件结束


bot.start()
