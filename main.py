import bot_api
import server

bot = bot_api.BotApp(123456, "", "",
                     is_sandbox=True, debug=True, api_return_pydantic=True,
                     inters=[bot_api.Intents.GUILDS, bot_api.Intents.AT_MESSAGES, bot_api.Intents.GUILD_MEMBERS])


app = server.BotServer(bot, ip_call="127.0.0.1", port_call=11415, ip_listen="127.0.0.1", port_listen=1988,
                       allow_push=False)
app.reg_bot_at_message()


app.listening_server_start()
app.bot.start()
