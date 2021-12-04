from bot_api import structs as msgs
import dateutil.parser
from . import tooles
import re


def time2timestamp(time_iso8601: str):
    d = dateutil.parser.parse(time_iso8601).timestamp()
    return int(d)


def cq_to_guild_text(msg: str):
    rmsg = msg[:]
    reply = re.findall("\\[CQ:reply,id=\\w*\\]", msg)
    if reply:  # 替换回复
        reply_id = tooles.gettext_between(rmsg, "[CQ:reply,id=", "]")
        rmsg = rmsg.replace(reply[0], "")
    else:
        reply_id = ""

    at = re.findall("\\[CQ:at,qq=\\w*\\]", msg)
    for _a in at:  # 替换艾特
        rmsg = rmsg.replace(_a, f"<@!{tooles.gettext_between(_a, '[CQ:at,qq=', ']')}>")

    return (rmsg, reply_id)


def guild_at_msg_to_groupmsg(msg: msgs.Message, selfid) -> dict:
    """
    频道艾特消息转onebot 11
    新增了一些字段: guild_id, channel_id
    :param msg: 原信息
    :param selfid: 自身id
    :return:
    """

    def cq_code_convert(msgcontent: str):
        retmsg = msgcontent[:]
        at_msgs = re.findall("<@!\\d*>", msgcontent)
        for _at in at_msgs:
            retmsg = retmsg.replace(_at, f"[CQ:at,qq={tooles.gettext_between(retmsg, '<@!', '>')}]", 1)

        return retmsg

    if msgs.Codes.QBot.UserRole.owner in msg.member.roles:
        userRole = "owner"
    elif msgs.Codes.QBot.UserRole.admin in msg.member.roles:
        userRole = "admin"
    elif msgs.Codes.QBot.UserRole.sub_admin in msg.member.roles:
        userRole = "admin"
    else:
        userRole = "member"

    retdata = {
        "time": time2timestamp(msg.timestamp),
        "self_id": selfid,
        "post_type": "message",
        "message_type": "group",
        "sub_type": "normal",
        "message_id": msg.id,
        "group_id": msg.channel_id,
        "channel_id": msg.channel_id,
        "guild_id": msg.guild_id,
        "self_tiny_id": selfid,
        "userguildid": msg.author.id,
        "user_id": msg.author.id,
        "anonymous": None,
        "message": cq_code_convert(msg.content),
        "raw_message": msg.content,
        "font": -1,
        "sender": {
            "user_id": msg.author.id,
            "nickname": msg.author.username,
            "card": msg.author.username,
            "sex": "Unknown",
            "age": 0,
            "area": "Unknown",
            "level": "",
            "role": userRole,
            "title": ""
        }
    }
    return retdata


def self_info_convert_to_json(info: msgs.User):
    retdata = {
        "id": info.id,
        "username": info.username,
        "avatar": info.avatar
    }
    return retdata

def guild_member_info_convert(info: msgs.Member, group_id):
    try:
        if msgs.Codes.QBot.UserRole.owner in info.roles:
            userRole = "owner"
        elif msgs.Codes.QBot.UserRole.admin in info.roles:
            userRole = "admin"
        elif msgs.Codes.QBot.UserRole.sub_admin in info.roles:
            userRole = "admin"
        else:
            userRole = "member"

        retdata = {
            "group_id": group_id,
            "user_id": info.user.id,
            "nickname": info.nick,
            "card": info.nick,
            "sex": "Unknown",
            "age": 0,
            "area": "",
            "join_time": 0,
            "last_sent_time": 0,
            "role": userRole,
            "unfriendly": False,
            "title": "",
            "title_expire_time": -1,
            "card_changeable": True,
            "avatar": info.user.avatar
        }
        return retdata

    except:
        retdata = str(info)
        return retdata
