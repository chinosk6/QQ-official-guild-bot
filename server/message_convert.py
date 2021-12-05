import time
from bot_api import structs as msgs
import dateutil.parser
from . import tools
import re
from pydantic import BaseModel
import os
import requests


def time2timestamp(time_iso8601: str):
    d = dateutil.parser.parse(time_iso8601).timestamp()
    return int(d)


def cq_to_guild_text(msg: str, func_img_to_url, auto_escape=False):
    rmsg = msg[:]
    reply = re.findall("\\[CQ:reply,id=\\w*]", msg)
    if reply:  # 替换回复
        reply_id = tools.gettext_between(rmsg, "[CQ:reply,id=", "]")
        rmsg = rmsg.replace(reply[0], "")
    else:
        reply_id = ""

    if auto_escape:
        return (rmsg, reply_id, "")

    at = re.findall("\\[CQ:at,qq=\\w*]", msg)
    for _a in at:  # 替换艾特
        rmsg = rmsg.replace(_a, f"<@!{tools.gettext_between(_a, '[CQ:at,qq=', ']')}>")


    ret_img_url = ""
    spath = os.path.split(__file__)[0]
    img = re.findall("\\[CQ:image,[^]]*]", rmsg)
    img_url = ""
    img_path = ""
    for im in img:
        ps = tools.gettext_between(im, "[CQ:image,", "]")
        _file = re.findall("file=[^,]*", ps)  # 查找file参数
        if _file:
            img_path = _file[0][len("file="):-1 if _file[0].endswith(',') else None]
            if img_path.startswith("http"):
                img_url = img_path

        _url = re.findall("url=[^,]*", ps)  # 查找url参数
        if _url:
            img_url = _url[0][len("url="):-1 if _url[0].endswith(',') else None]
        break  # 仅支持一张图

    for im in img:
        rmsg = rmsg.replace(im, "", 1)  # 清除图片cq码

    if callable(func_img_to_url):
        if img_url != "":  # 参数为url
            save_name = tools.generate_randstring() + ".jpg"
            if not os.path.isdir(f"{spath}/temp"):
                os.mkdir(f"{spath}/temp")
            with open(f"{spath}/temp/{save_name}", "wb") as f:
                f.write(requests.get(img_url).content)
            ret_img_url = func_img_to_url(f"{spath}/temp/{save_name}")

        elif img_path != "":  # 参数为path
            ret_img_url = func_img_to_url(img_path)

    others_cq = re.findall("\\[CQ:[^]]*]", rmsg)
    for ocq in others_cq:
        rmsg = rmsg.replace(ocq, "", 1)  # 去除其它不受支持的CQ码

    return (rmsg, reply_id, ret_img_url)


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
            retmsg = retmsg.replace(_at, f"[CQ:at,qq={tools.gettext_between(retmsg, '<@!', '>')}]", 1)

        return retmsg

    img_cq = ""
    if msg.attachments is not None:  # 判断图片
        for _im in msg.attachments:
            if _im.content_type is not None:
                if "image" in _im.content_type:
                    msg_url = _im.url
                    if not msg_url.startswith("http"):
                        msg_url = f"http://{msg_url}"
                    img_cq += f"[CQ:image,url={msg_url}]"

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
        "message": cq_code_convert(msg.content) + img_cq,
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

def guild_member_change_convert(info: msgs.MemberWithGuildID, selfid, is_useradd=True):
    try:
        retdata = {
            "time": int(time.time()),
            "self_id": selfid,
            "post_type": "notice",
            "notice_type": "group_increase" if is_useradd else "group_decrease",
            "sub_type": "approve" if is_useradd else "leave",
            "group_id": info.guild_id,
            "user_id": info.user.id if info.user is not None else "",
            "operator_id": info.user.id if info.user is not None else "",
        }

        return retdata
    except Exception as sb:
        retdata = {
            "code": -114514,
            "msg": repr(sb)
        }
        return retdata

def others_event(selfid, post_type, notice_type, sub_type, data: BaseModel, user_id="", guiid_id="", channel_id=""):

    retdata = {
        "time": int(time.time()),
        "self_id": selfid,
        "post_type": post_type,
        "notice_type": notice_type,
        "sub_type": sub_type,

        "user_id": user_id,
        "guiid_id": guiid_id,
        "channel_id": channel_id,
        "data": data.dict()
    }

    return retdata
