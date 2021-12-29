# QQ官方频道机器人SDK

- 只实现了部分API
- 添加[onebot11](https://11.onebot.dev/)支持(api差距过大, 很难做到完全兼容)



# 直接使用SDK

- 参考`bot_main.py`
- 没有文档, 代码补全很完善了

```python
import bot_api
from bot_api.models import Ark, Embed


bot = bot_api.BotApp(123456, "你的bot token", "你的bot secret",
                     is_sandbox=True, debug=True, api_return_pydantic=True,
                     ignore_at_self=False,  # 过滤消息正文中艾特Bot自身的内容, 默认为False
                     inters=[bot_api.Intents.GUILDS, bot_api.Intents.AT_MESSAGES, bot_api.Intents.GUILD_MEMBERS])  # 事件订阅


@bot.receiver(bot_api.structs.Codes.SeverCode.BotGroupAtMessage)  # 填入对应的参数实现处理对应事件
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
        
    elif "/embed" in chain.content:  # 发送embed, 需要Ark权限
        send_embed = Embed("标题", ["文本1", "文本2", "文本3"], image_url=None)
        bot.api_send_reply_message(chain.channel_id, chain.id, embed=send_embed)

    elif "/ark" in chain.content:  # 发送ark消息, 需要Ark权限
        send_ark = Ark.LinkWithText("描述", "提示信息", [["纯文本1"], ["纯文本2"], ["链接文本1", "http://baidu.com"]])
        bot.api_send_reply_message(chain.channel_id, chain.id, ark=send_ark)


bot.start()  # 启动bot

```



### 自行组合消息

`api_send_reply_message`方法提供了极高的自由度。您可以按照本文档提供的方法发送消息, 也可以使用`others_parameter`参数自行组合。

使用`others_parameter`, 您需要按照 [QQ机器人文档 - 发送消息](https://bot.q.qq.com/wiki/develop/api/openapi/message/post_messages.html) 提供的参数发送消息, 若有此SDK没有支持的消息类型, 您依旧可以自行组合参数进行发送。

下面是发送一条文本+图片消息的例子

-----

  - 一般情况下, 您可以:

```python
bot.api_send_reply_message(chain.channel_id, chain.id, "这是消息", "http://您的图片")
```

  - 您也可以:

```python
bot.api_send_reply_message(chain.channel_id, chain.id, others_parameter={"content": "这是消息", "image": "https://您的图片"})
```





## Ark消息说明

- 注意: 发送Ark消息需要向官方申请Ark权限, 否则无法发送

### 引用: 

```python
from bot_api.models import Ark, Embed
```

### 发送[Embed](https://bot.q.qq.com/wiki/develop/api/openapi/message/template/embed_message.html)消息

```python
send_embed = Embed("标题", ["文本1", "文本2", "文本3"], image_url="http://你的图片")
"image_url"参数可选, 若没有图片, 则不填

bot.api_send_reply_message(channel_id, message_id, embed=send_embed)
```

### 发送[Ark](https://bot.q.qq.com/wiki/develop/api/openapi/message/message_template.html)消息

- `Ark`类中目前有`LinkWithText`, `TextAndThumbnail`, `BigImage`三个子类, 分别对应 [23 链接+文本列表模板](https://bot.q.qq.com/wiki/develop/api/openapi/message/template/template_23.html), [24 文本+缩略图模板](https://bot.q.qq.com/wiki/develop/api/openapi/message/template/template_24.html), [37 大图模板](https://bot.q.qq.com/wiki/develop/api/openapi/message/template/template_37.html), 下面以构造相对复杂的 [23 链接+文本列表模板 ](https://bot.q.qq.com/wiki/develop/api/openapi/message/template/template_23.html)为例

```python
send_ark = Ark.LinkWithText("描述", "提示信息", [["纯文本1"], ["纯文本2"], ["链接文本1", "http://baidu.com"], ["链接文本2", "http://google.com"]])

bot.api_send_reply_message(channel_id, message_id, ark=send_ark)
```



## 目前支持的事件/API

#### 事件

- `事件代号`: 注册函数时, 输入对应事件代号, 在触发相应事件时, 所有被注册函数将被调用。

  - 位于: 类`bot_api.structs.Codes.SeverCode`, 继承自`GatewayEventName`

- `传入参数`指被注册函数的参数
  - 位于: 类`bot_api.structs`

| 事件代号                | 传入参数          | 事件描述                   |
| ----------------------- | ----------------- | -------------------------- |
| AT_MESSAGE_CREATE       | Message           | 收到艾特消息               |
| MESSAGE_CREATE          | Message           | 收到消息(仅私域机器人可用) |
| DIRECT_MESSAGE_CREATE   | 暂不支持          | 收到私聊消息               |
| GUILD_CREATE            | Guild             | bot加入频道                |
| GUILD_UPDATE            | Guild             | 频道信息更新               |
| GUILD_DELETE            | Guild             | 频道解散/bot被移除         |
| CHANNEL_CREATE          | Channel           | 子频道被创建               |
| CHANNEL_UPDATE          | Channel           | 子频道信息变更             |
| CHANNEL_DELETE          | Channel           | 子频道被删除               |
| GUILD_MEMBER_ADD        | MemberWithGuildID | 新用户加入频道             |
| GUILD_MEMBER_UPDATE     | -                 | TX: 暂无                   |
| GUILD_MEMBER_REMOVE     | MemberWithGuildID | 用户离开频道               |
| AUDIO_START             | AudioAction       | 音频开始播放               |
| AUDIO_FINISH            | AudioAction       | 音频结束                   |
| AUDIO_ON_MIC            | AudioAction       | 上麦                       |
| AUDIO_OFF_MIC           | AudioAction       | 下麦                       |
| MESSAGE_REACTION_ADD    | MessageReaction   | 添加表情表态               |
| MESSAGE_REACTION_REMOVE | MessageReaction   | 删除表情表态               |
| THREAD_CREATE           | 暂不支持          | 用户创建主题               |
| THREAD_UPDATE           | 暂不支持          | 用户更新主题               |
| THREAD_DELETE           | 暂不支持          | 用户删除主题               |
| POST_CREATE             | 暂不支持          | 用户创建帖子               |
| POST_DELETE             | 暂不支持          | 用户删除帖子               |
| REPLY_CREATE            | 暂不支持          | 用户回复评论               |
| REPLY_DELETE            | 暂不支持          | 用户回复评论               |



- 例: 注册一个`添加表情表态`处理函数

```python
@bot.receiver(bot_api.structs.Codes.SeverCode.MESSAGE_REACTION_ADD)  # 填入事件代号
def get_at_message(event: bot_api.structs.MessageReaction):  # 函数参数类型为上表对应的传入参数
    pass
```




------

#### API

- 初始化Bot实例后, 输入`bot.api_`, 即可根据代码补全进行使用

```python
api_send_reply_message()  # 发送消息
api_mute_guiid()  # 全频道禁言
api_mute_member()  # 指定用户禁言
api_get_self_guilds()  # 获取Bot加入的频道列表
api_get_self_info()  # 获取Bot自身信息
api_get_message()  # 获取指定消息
api_get_guild_channel_list()  # 获取频道内子频道列表
api_get_channel_info()  # 获取子频道信息
api_get_guild_user_info()  # 获取频道用户信息
api_get_guild_info()  # 获取频道信息
api_get_schedule_list()  # 获取子频道日程列表
api_get_schedule()  # 获取单个日程信息
api_schedule_create()  # 创建日程
api_schedule_change()  # 修改日程
api_schedule_delete()  # 删除日程
api_message_recall()  # 撤回消息
api_pv_get_member_list()  # 仅私域机器人可用 - 取频道成员列表
api_pv_kick_member()  # 仅私域机器人可用 - 踢出指定成员
api_pv_create_channel()  # 仅私域机器人可用 - 创建子频道
api_pv_change_channel()  # 仅私域机器人可用 - 创建子频道
api_pv_delete_channel()  # 仅私域机器人可用 - 删除子频道
```

------

<br>

<br>

<br>

# 作为HTTP API使用

- 一个人同时更新两套SDK显然是非常困难的。因此HTTP API部分的更新进度会慢于SDK本体。欢迎有能之士前来Pr~

- 参考`main.py`

```python
import bot_api
import server

bot = bot_api.BotApp(123456, "你的bot token", "你的bot secret",
                     is_sandbox=True, debug=True, api_return_pydantic=True,
                     inters=[bot_api.Intents.GUILDS, bot_api.Intents.AT_MESSAGES, bot_api.Intents.GUILD_MEMBERS])  # 事件订阅


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
```

------

### 目前实现的CQ码

| CQ码                                      | 功能     | 备注                                                         |
| ----------------------------------------- | -------- | ------------------------------------------------------------ |
| [CQ:reply,id=abc123]                      | 回复消息 | 被动回复请务必带上此CQ码, 否则会被视为主动推送消息           |
| [CQ:at,qq=123456]                         | 艾特用户 | 与官方<@!123456>对应                                         |
| [CQ:image,file=...]<br>[CQ:image,url=...] | 发送图片 | 发送图片可以使用这两个CQ码<br>由于API限制, 发送图片仅支持一张, 并且需要自行配置图床(见上方代码示例)<br>接收到图片时, 目前仅会返回[CQ:image,url=...] |



------



   ### 目前实现的API(基本同`onebot`):

- 特别注意: 所有`用户ID`, `频道号`, `子频道号`, `消息ID`字段均为`string`

| 接口                                                         | 描述         | 备注                                                         |
| ------------------------------------------------------------ | ------------ | ------------------------------------------------------------ |
| [/send_group_msg](https://github.com/botuniverse/onebot-11/blob/master/api/public.md#send_group_msg-%E5%8F%91%E9%80%81%E7%BE%A4%E6%B6%88%E6%81%AF) | 发送群消息   | `group_id`请填写`channel_id`<br>`auto_escape`为true时, 依然会解析[CQ:reply] |
| [/get_group_member_info](https://github.com/botuniverse/onebot-11/blob/master/api/public.md#get_group_member_info-%E8%8E%B7%E5%8F%96%E7%BE%A4%E6%88%90%E5%91%98%E4%BF%A1%E6%81%AF) | 获取成员信息 | `group_id`请填写`guild_id`<br>仅`user_id`,`nickname`,`role`有效<br>额外增加头像URL: `avatar` |




------



### 目前实现的API(与`onebot`不同)

#### 获取自身信息

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



#### 获取自身加入频道列表

- 接口: `/get_self_guild_list`

| 参数   | 类型   | 默认值 | 说明                                               |
| ------ | ------ | ------ | -------------------------------------------------- |
| cache  | bool   | false  | 是否使用缓存(可选)                                 |
| before | string | -      | 读此id之前的数据(可选, `before`/`after`只能二选一) |
| after  | string | -      | 读此id之后的数据(可选, `before`/`after`只能二选一) |
| limit  | int    | 100    | 每次拉取多少条数据(可选)                           |

- 返回参数

见: https://bot.q.qq.com/wiki/develop/api/openapi/channel/get_channel.html



#### 获取频道信息

- 接口: `/get_guild_info`

| 参数     | 类型   | 默认值 | 说明   |
| -------- | ------ | ------ | ------ |
| guild_id | string | -      | 频道id |

- 返回参数

见: https://bot.q.qq.com/wiki/develop/api/openapi/guild/get_guild.html



#### 获取子频道信息

- 接口: `/get_channel_info`

| 参数       | 类型   | 默认值 | 说明     |
| ---------- | ------ | ------ | -------- |
| channel_id | string | -      | 子频道id |

- 返回参数

见: https://bot.q.qq.com/wiki/develop/api/openapi/channel/get_channel.html



#### 获取子频道列表

- 接口: `/get_channel_list`

| 参数     | 类型   | 默认值 | 说明   |
| -------- | ------ | ------ | ------ |
| guild_id | string | -      | 频道id |

- 返回参数

见: https://bot.q.qq.com/wiki/develop/api/openapi/channel/get_channels.html



#### 获取指定消息

- 接口: `/get_message`

| 参数       | 类型   | 默认值 | 说明   |
| ---------- | ------ | ------ | ------ |
| message_id | string | -      | 消息id |
| channel_id | string | -      | 频道id |

- 返回参数

见: https://bot.q.qq.com/wiki/develop/api/openapi/message/get_message_of_id.html



------

### 目前实现的Event(基本同`onebot`)

- 特别注意: 所有`用户ID`, `频道号`, `子频道号`, `消息ID`字段均为`string`

#### 收到艾特消息

- 见: https://github.com/botuniverse/onebot-11/blob/master/event/message.md#%E7%BE%A4%E6%B6%88%E6%81%AF

- 注意:

  - 注意上面的`特别注意`
  - `anonymous`字段恒为`null`
  - `sender`字段中仅`user_id`, `nickname`, `role`有效




#### 成员增加事件

- 见: https://github.com/botuniverse/onebot-11/blob/master/event/notice.md#%E7%BE%A4%E6%88%90%E5%91%98%E5%A2%9E%E5%8A%A0
- 注意: 
  - 注意上面的`特别注意`
  
  - `sub_type`恒为`approve`
  
    


#### 成员减少事件

- 见: https://github.com/botuniverse/onebot-11/blob/master/event/notice.md#%E7%BE%A4%E6%88%90%E5%91%98%E5%87%8F%E5%B0%91
- 注意: 
  - 注意上面的`特别注意`
  - `sub_type`恒为`leave`

------



### 目前实现的Event(与`onebot`差别较大)

- 通用字段

| 参数        | 类型   | 默认值   | 说明                           |
| ----------- | ------ | -------- | ------------------------------ |
| time        | int    | -        | 消息接收时间戳                 |
| self_id     | string | -        | 自身id                         |
| post_type   | string | `notice` | 上报类型                       |
| notice_type | string | -        | 通知类型                       |
| sub_type    | string | -        | 通知子类型                     |
| user_id     | string | 空字符串 | 触发者ID, 仅在对应事件有值     |
| guiid_id    | string | 空字符串 | 触发频道ID, 仅在对应事件有值   |
| channel_id  | string | 空字符串 | 触发子频道ID, 仅在对应事件有值 |
| data        | -      | -        | 每个事件均不同, 见下方文档     |



#### Bot加入频道事件

| 参数        | 类型                                                         | 值                                                           |
| ----------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| post_type   | string                                                       | `notice`                                                     |
| notice_type | string                                                       | `guild_create`                                               |
| sub_type    | string                                                       | `guild_create`                                               |
| guiid_id    | string                                                       | 频道ID                                                       |
| data        | [Guild](https://bot.q.qq.com/wiki/develop/api/openapi/guild/model.html#guild) | 见: [腾讯机器人文档](https://bot.q.qq.com/wiki/develop/api/gateway/guild.html#guild-create) |


#### 频道信息更新事件

| 参数      | 类型                                                         | 值                                                           |
| --------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| post_type | string                                                       | `notice`                                                     |
| sub_type  | string                                                       | `guild_update`                                               |
| guiid_id  | string                                                       | 频道ID                                                       |
| data      | [Guild](https://bot.q.qq.com/wiki/develop/api/openapi/guild/model.html#guild) | 见: [腾讯机器人文档](https://bot.q.qq.com/wiki/develop/api/gateway/guild.html#guild-update) |

#### 机器人离开频道/频道被解散事件

| 参数        | 类型                                                         | 值                                                           |
| ----------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| post_type   | string                                                       | `notice`                                                     |
| notice_type | string                                                       | `guild_update`                                               |
| sub_type    | string                                                       | `guild_update`                                               |
| guiid_id    | string                                                       | 频道ID                                                       |
| data        | [Guild](https://bot.q.qq.com/wiki/develop/api/openapi/guild/model.html#guild) | 见: [腾讯机器人文档](https://bot.q.qq.com/wiki/develop/api/gateway/guild.html#guild-delete) |

#### 子频道创建事件

| 参数        | 类型                                                         | 值                                                           |
| ----------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| post_type   | string                                                       | `notice`                                                     |
| notice_type | string                                                       | `channel_create`                                             |
| sub_type    | string                                                       | `channel_create`                                             |
| guiid_id    | string                                                       | 频道ID                                                       |
| channel_id  | string                                                       | 子频道ID                                                     |
| data        | [Channel](https://bot.q.qq.com/wiki/develop/api/openapi/channel/model.html#channel) | 见: [腾讯机器人文档](https://bot.q.qq.com/wiki/develop/api/gateway/channel.html#channel-create) |

#### 子频道信息更新事件

| 参数        | 类型                                                         | 值                                                           |
| ----------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| post_type   | string                                                       | `notice`                                                     |
| notice_type | string                                                       | `channel_update`                                             |
| sub_type    | string                                                       | `channel_update`                                             |
| guiid_id    | string                                                       | 频道ID                                                       |
| channel_id  | string                                                       | 子频道ID                                                     |
| data        | [Channel](https://bot.q.qq.com/wiki/develop/api/openapi/channel/model.html#channel) | 见: [腾讯机器人文档](https://bot.q.qq.com/wiki/develop/api/gateway/channel.html#channel-update) |

#### 子频道被删除事件

| 参数        | 类型                                                         | 值                                                           |
| ----------- | ------------------------------------------------------------ | ------------------------------------------------------------ |
| post_type   | string                                                       | `notice`                                                     |
| notice_type | string                                                       | `channel_delete`                                             |
| sub_type    | string                                                       | `channel_delete`                                             |
| guiid_id    | string                                                       | 频道ID                                                       |
| channel_id  | string                                                       | 子频道ID                                                     |
| data        | [Channel](https://bot.q.qq.com/wiki/develop/api/openapi/channel/model.html#channel) | 见: [腾讯机器人文档](https://bot.q.qq.com/wiki/develop/api/gateway/channel.html#channel-delete) |

