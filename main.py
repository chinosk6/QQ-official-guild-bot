import bot_api
import server

bot = bot_api.BotApp(123456, "你的bot token", "你的bot secret",
                     is_sandbox=True, debug=True, api_return_pydantic=True,
                     inters=[bot_api.Intents.GUILDS, bot_api.Intents.AT_MESSAGES, bot_api.Intents.GUILD_MEMBERS])


app = server.BotServer(bot, ip_call="127.0.0.1", port_call=11415, ip_listen="127.0.0.1", port_listen=1988,
                       allow_push=False)

# 开始注册事件, 可以选择需要的进行注册
app.reg_bot_at_message()  # 艾特消息事件
app.reg_guild_member_add()  # 成员增加事件
app.reg_guild_member_remove()  # 成员减少事件

# 以下事件与onebot差别较大
app.reg_guild_create()  # Bot加入频道事件
app.reg_guild_update()  # 频道信息更新事件
app.reg_guild_delete()  # Bot离开频道/频道被解散事件
app.reg_channel_create()  # 子频道创建事件
app.reg_channel_update()  # 子频道信息更新事件
app.reg_channel_delete()  # 子频道删除事件

@app.bot.receiver(bot_api.structs.Codes.SeverCode.image_to_url)  # 注册一个图片转url方法
def img_to_url(img_path: str):
    # 用处: 发送图片时, 使用图片cq码[CQ:image,file=]或[CQ:image,url=]
    # 装饰器作用为: 解析cq码中图片的路径(网络图片则下载到本地), 将绝对路径传给本函数, 自行操作后, 返回图片url, sdk将使用此url发送图片
    # 若不注册此方法, 则无法发送图片。
    print(img_path)
    return "https://你的图片url"

# 注册事件结束


app.listening_server_start()  # HTTP API 服务器启动
app.bot.start()  # Bot启动
