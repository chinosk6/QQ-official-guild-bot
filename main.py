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
# 注册事件结束


app.listening_server_start()  # HTTP API 服务器启动
app.bot.start()  # Bot启动
