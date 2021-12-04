# QQ官方频道机器人SDK

- 自用, 只实现了部分API
- 添加[onebot11](https://11.onebot.dev/)支持(半成品, 而且api差距过大, 很难做到完全兼容)
- 暂未添加图片消息相关支持
- 暂未添加`ark`消息支持



# 作为SDK使用

- 参考`main_bot.py`

```python
import bot_api

bot = bot_api.BotApp(你的appid, 你的token, 你的app_secret,
                     is_sandbox=True, debug=True, api_return_pydantic=True,
                     inters=[bot_api.Intents.GUILDS, bot_api.Intents.AT_MESSAGES, bot_api.Intents.GUILD_MEMBERS])


@bot.receiver(bot_api.structs.Codes.SeverCode.BotGroupAtMessage)
def get_at_message(chain: bot_api.structs.Message):  # 注册一个艾特消息处理器
    bot.logger(f"收到来自频道:{chain.guild_id} 子频道: {chain.channel_id} "
               f"内用户: {chain.author.username}({chain.author.id}) 的消息: {chain.content} ({chain.id})")

    if "你好" in chain.content:
        bot.api_send_reply_message(chain.channel_id, chain.id, "hello world!")
    elif "test" in chain.content:
        bot.api_send_reply_message(chain.channel_id, chain.id, "chieri在哟~")
    elif "/echo" in chain.content:
        reply = chain.content[chain.content.find("/echo") + len("/echo"):].strip()

        bot.api_send_reply_message(chain.channel_id, chain.id, reply)


bot.start()  # 启动bot

```





# 作为HTTP API使用

- 参考`main.py`

```python
import bot_api
import server

bot = bot_api.BotApp(你的appid, 你的token, 你的app_secret,
                     is_sandbox=True, debug=True, api_return_pydantic=True,
                     inters=[bot_api.Intents.GUILDS, bot_api.Intents.AT_MESSAGES, bot_api.Intents.GUILD_MEMBERS])


app = server.BotServer(bot, ip_call="127.0.0.1", port_call=11415, ip_listen="127.0.0.1", port_listen=1988,
                       allow_push=False)  # 此处填写你的地址
app.reg_bot_at_message()


app.listening_server_start()  # 启动HTTP API服务器
app.bot.start()  # 启动bot

```

------

   #### 目前实现的API(基本同`onebot`):

- 特别注意: 所有`用户ID`, `频道号`, `子频道号`, `消息ID`字段均为`string`

| 接口                   | 描述         | 备注                                                         |
| ---------------------- | ------------ | ------------------------------------------------------------ |
| /send_group_msg        | 发送群消息   | `group_id`字段请填写`channel_id`<br>不支持`auto_escape`字段  |
| /get_group_member_info | 获取成员信息 | `group_id`请填写`guild_id`<br>仅`user_id`,`nickname`,`role`有效<br>增加字段: `avatar` |




------


#### 目前实现的API(与`onebot`不同)

##### 获取自身信息

- 接口: `/get_self_info`

| 参数  | 类型 | 默认值 | 说明               |
| ----- | ---- | ------ | ------------------ |
| cache | bool | false  | 是否使用缓存(可选) |

- 返回参数
| 参数   | 类型 | 说明         |
| ------ | ------ | ------------ |
| avatar | string | 头像url |
| id | string | BotID |
| username | string | Bot名 |



##### 获取自身加入频道列表

- 接口: `/get_self_guild_list`

| 参数   | 类型   | 默认值 | 说明                                               |
| ------ | ------ | ------ | -------------------------------------------------- |
| cache  | bool   | false  | 是否使用缓存(可选)                                 |
| before | string | -      | 读此id之前的数据(可选, `before`/`after`只能二选一) |
| after  | string | -      | 读此id之后的数据(可选, `before`/`after`只能二选一) |
| limit  | int    | 100    | 每次拉取多少条数据(可选)                           |

- 返回参数

见: https://bot.q.qq.com/wiki/develop/api/openapi/channel/get_channel.html



##### 获取频道信息

- 接口: `/get_guild_info`

| 参数     | 类型   | 默认值 | 说明   |
| -------- | ------ | ------ | ------ |
| guild_id | string | -      | 频道id |

- 返回参数

见: https://bot.q.qq.com/wiki/develop/api/openapi/guild/get_guild.html



##### 获取子频道信息

- 接口: `/get_channel_info`

| 参数       | 类型   | 默认值 | 说明     |
| ---------- | ------ | ------ | -------- |
| channel_id | string | -      | 子频道id |

- 返回参数

见: https://bot.q.qq.com/wiki/develop/api/openapi/channel/get_channel.html



##### 获取子频道列表

- 接口: `/get_channel_list`

| 参数     | 类型   | 默认值 | 说明   |
| -------- | ------ | ------ | ------ |
| guild_id | string | -      | 频道id |

- 返回参数

见: https://bot.q.qq.com/wiki/develop/api/openapi/channel/get_channels.html



##### 获取指定消息

- 接口: `/get_message`

| 参数       | 类型   | 默认值 | 说明   |
| ---------- | ------ | ------ | ------ |
| message_id | string | -      | 消息id |
| channel_id | string | -      | 频道id |

- 返回参数

见: https://bot.q.qq.com/wiki/develop/api/openapi/message/get_message_of_id.html

