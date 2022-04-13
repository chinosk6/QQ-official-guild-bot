from pydantic import BaseModel
import typing as t


class Codes:
    class QBot:
        class OPCode:  # see: https://bot.q.qq.com/wiki/develop/api/gateway/opcode.html
            Dispatch = 0
            Heartbeat = 1
            Identify = 2
            Resume = 6
            Reconnect = 7
            Invalid_Session = 9
            Hello = 10
            Heartbeat_Ack = 11

        class GatewayEventName:
            READY = "READY"
            RESUMED = "RESUMED"
            AT_MESSAGE_CREATE = "AT_MESSAGE_CREATE"  # 收到艾特消息
            MESSAGE_CREATE = "MESSAGE_CREATE"  # 收到消息, 仅私域机器人有效
            DIRECT_MESSAGE_CREATE = "DIRECT_MESSAGE_CREATE"  # 收到私聊消息
            GUILD_CREATE = "GUILD_CREATE"  # bot加入频道
            GUILD_UPDATE = "GUILD_UPDATE"  # 频道信息更新
            GUILD_DELETE = "GUILD_DELETE"  # 频道解散/bot被移除
            CHANNEL_CREATE = "CHANNEL_CREATE"  # 子频道被创建
            CHANNEL_UPDATE = "CHANNEL_UPDATE"  # 子频道信息变更
            CHANNEL_DELETE = "CHANNEL_DELETE"  # 子频道被删除
            GUILD_MEMBER_ADD = "GUILD_MEMBER_ADD"  # 新用户加入频道
            GUILD_MEMBER_UPDATE = "GUILD_MEMBER_UPDATE"  # TODO - TX: 暂无
            GUILD_MEMBER_REMOVE = "GUILD_MEMBER_REMOVE"  # 用户离开频道
            AUDIO_START = "AUDIO_START"  # 音频开始播放
            AUDIO_FINISH = "AUDIO_FINISH"  # 音频结束
            AUDIO_ON_MIC = "AUDIO_ON_MIC"  # 机器人上麦
            AUDIO_OFF_MIC = "AUDIO_OFF_MIC"  # 机器人下麦
            MESSAGE_REACTION_ADD = "MESSAGE_REACTION_ADD"  # 添加表情表态
            MESSAGE_REACTION_REMOVE = "MESSAGE_REACTION_REMOVE"  # 删除表情表态
            THREAD_CREATE = "THREAD_CREATE"  # 当用户创建主题时
            THREAD_UPDATE = "THREAD_UPDATE"  # 当用户更新主题时
            THREAD_DELETE = "THREAD_DELETE"  # 当用户删除主题时
            POST_CREATE = "POST_CREATE"  # 当用户创建帖子时
            POST_DELETE = "POST_DELETE"  # 当用户删除帖子时
            REPLY_CREATE = "REPLY_CREATE"  # 当用户回复评论时
            REPLY_DELETE = "REPLY_DELETE"  # 当用户回复评论时
            MESSAGE_AUDIT_PASS = "MESSAGE_AUDIT_PASS"  # 消息审核通过
            MESSAGE_AUDIT_REJECT = "MESSAGE_AUDIT_REJECT"  # 消息审核不通过

            PUBLIC_MESSAGE_DELETE = "PUBLIC_MESSAGE_DELETE"  # 消息撤回(公域)
            MESSAGE_DELETE = "MESSAGE_DELETE"  # 消息撤回(私域)
            DIRECT_MESSAGE_DELETE = "DIRECT_MESSAGE_DELETE"  # 消息撤回(私聊)

        class UserRole:
            member = "1"  # 全体成员
            admin = "2"  # 管理员
            sub_admin = "5"  # 子频道管理员
            owner = "4"  # 创建者

    class SeverCode(QBot.GatewayEventName):
        BotGroupAtMessage = "AT_MESSAGE_CREATE"
        Module = "Module"
        image_to_url = "image_to_url"
        # FUNC_CALL_BEFORE_BOT_LOAD = "FUNC_CALL_BEFORE_BOT_LOAD"
        FUNC_CALL_AFTER_BOT_LOAD = "FUNC_CALL_AFTER_BOT_LOAD"


class User(BaseModel):  # 用户对象
    id: str
    username: t.Optional[str]
    avatar: t.Optional[str]
    bot: t.Optional[bool]
    union_openid: t.Optional[str]
    union_user_account: t.Optional[str]


class Member(BaseModel):
    user: t.Optional[User]
    nick: t.Optional[str]
    roles: t.Optional[t.List[str]]
    joined_at: t.Optional[str]
    deaf: t.Optional[bool]
    mute: t.Optional[bool]
    pending: t.Optional[bool]


class MessageAttachment(BaseModel):
    url: str
    content_type: t.Optional[str]
    filename: t.Optional[str]
    height: t.Optional[int]
    width: t.Optional[int]
    id: t.Optional[str]
    size: t.Optional[int]


class MessageEmbedField(BaseModel):
    name: t.Optional[str]
    value: t.Optional[str]


class MessageEmbed(BaseModel):
    title: t.Optional[str]
    description: t.Optional[str]
    prompt: t.Optional[str]
    timestamp: t.Optional[str]
    fields: t.List[MessageEmbedField]


class MessageArkObjKv(BaseModel):
    key: str
    value: str


class MessageArkObj(BaseModel):
    obj_kv: t.List[MessageArkObjKv]


class MessageArkKv(BaseModel):
    key: str
    value: str
    obj: t.List[MessageArkObj]


class MessageArk(BaseModel):
    template_id: int
    kv: t.List[MessageArkKv]

class MessageReference(BaseModel):
    message_id: str
    ignore_get_message_error: t.Optional[bool]

class Message(BaseModel):  # 消息对象
    id: str  # 消息id
    channel_id: str
    guild_id: str
    content: t.Optional[str]
    timestamp: str
    edited_timestamp: t.Optional[str]
    mention_everyone: t.Optional[bool]
    author: User
    attachments: t.Optional[t.List[MessageAttachment]]
    embeds: t.Optional[t.List[MessageEmbed]]
    mentions: t.Optional[t.List[User]]
    member: t.Optional[Member]
    ark: t.Optional[MessageArk]
    seq: t.Optional[int]
    seq_in_channel: t.Optional[str]
    message_reference: t.Optional[MessageReference]
    message_type_sdk: t.Optional[str]


class Guild(BaseModel):  # 频道对象
    id: t.Optional[str]  # GUILD_DELETE 事件为 None
    name: t.Optional[str]  # GUILD_DELETE 事件为 None
    icon: t.Optional[str]
    owner_id: t.Optional[str]  # GUILD_DELETE 事件为 None
    owner: t.Optional[bool]
    member_count: t.Optional[int]  # GUILD_DELETE 事件为 None
    max_members: t.Optional[int]  # GUILD_DELETE 事件为 None
    description: t.Optional[str]  # GUILD_DELETE 事件为 None
    joined_at: t.Optional[str]


class Channel(BaseModel):  # 子频道对象
    id: t.Optional[str]
    guild_id: t.Optional[str]
    name: t.Optional[str]
    type: t.Optional[int]
    sub_type: t.Optional[int]
    position: t.Optional[int]
    parent_id: t.Optional[str]
    owner_id: t.Optional[str]
    last_message_id: t.Optional[str]
    nsfw: t.Optional[bool]  # 这个字段, 可能为True吗?
    private_type: t.Optional[int]
    speak_permission: t.Optional[int]
    application_id: t.Optional[str]
    permissions: t.Optional[str]
    rate_limit_per_user: t.Optional[int]


class MemberWithGuildID(BaseModel):
    guild_id: str
    user: t.Optional[User]
    nick: str
    roles: t.Optional[t.List[str]]
    joined_at: str


class AudioControl(BaseModel):
    audio_url: str
    text: str
    status: int

class AudioControlSTATUS:
    START = 0
    PAUSE = 1
    RESUME = 2
    STOP = 3

class AudioAction(BaseModel):
    guild_id: str
    channel_id: str
    audio_url: t.Optional[str]
    text: t.Optional[str]

class ReactionTarget(BaseModel):
    id: str
    type: int

class Emoji(BaseModel):
    id: str
    type: int

class MessageReaction(BaseModel):
    user_id: str
    guild_id: str
    channel_id: str
    target: ReactionTarget
    emoji: Emoji


class Schedule(BaseModel):
    id: str
    name: str
    description: str
    start_timestamp: str
    end_timestamp: str
    creator: Member
    jump_channel_id: str
    remind_type: str


class Role(BaseModel):  # 身份组对象
    id: str  # 身份组ID
    name: str  # 名称
    color: int  # ARGB的HEX十六进制颜色值转换后的十进制数值
    hoist: int  # 是否在成员列表中单独展示: 0-否, 1-是
    number: int  # 人数
    member_limit: int  # 成员上限


class MessageAudited(BaseModel):  # 消息审核对象
    audit_id: str
    message_id: str
    guild_id: str
    channel_id: str
    audit_time: str
    create_time: str
    seq_in_channel: t.Optional[str]


class RecommendChannel(BaseModel):
    channel_id: t.Optional[str]
    introduce: t.Optional[str]

class Announces(BaseModel):  # 公告
    guild_id: str
    channel_id: str
    message_id: str
    announces_type: t.Optional[int]
    recommend_channels: t.Optional[RecommendChannel]


class ChannelPermissions(BaseModel):  # 子频道权限对象
    channel_id: str
    user_id: t.Optional[str]
    role_id: t.Optional[str]
    permissions: str  # https://bot.q.qq.com/wiki/develop/api/openapi/channel_permissions/model.html#permissions


class RetModel:
    class GetGuildRole(BaseModel):
        guild_id: str
        roles: t.List[Role]
        role_num_limit: str

    class CreateGuildRole(BaseModel):
        role_id: str
        role: Role

    class ChangeGuildRole(BaseModel):
        guild_id: str
        role_id: str
        role: Role


class APIPermission(BaseModel):
    path: str
    method: str
    desc: str
    auth_status: int


class APIPermissionDemandIdentify(BaseModel):
    path: str
    method: str


class APIPermissionDemand(BaseModel):
    guild_id: str
    channel_id: str
    api_identify: APIPermissionDemandIdentify
    title: str
    desc: str


class DMS(BaseModel):
    guild_id: t.Optional[str]
    channel_id: t.Optional[str]
    create_time: t.Optional[str]

class PinsMessage(BaseModel):
    guild_id: t.Optional[str]
    channel_id: t.Optional[str]
    message_ids: t.Optional[t.List[str]]

class MessageDelete(BaseModel):
    class DeletedMessage(BaseModel):
        author: t.Optional[User]
        channel_id: t.Optional[str]
        guild_id: t.Optional[str]
        id: t.Optional[str]
        direct_message: t.Optional[bool]

    class OpUser(BaseModel):
        id: t.Optional[str]

    message: t.Optional[DeletedMessage]
    op_user: t.Optional[OpUser]
