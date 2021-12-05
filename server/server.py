import json
from flask import Flask, jsonify
from flask import request
from waitress import serve as wserve
from . import sender
from . import tools
from . import message_convert
import bot_api

flask = Flask(__name__)


class BotServer(sender.MessageSender):
    def __init__(self, bot_app: bot_api.BotApp, ip_call: str, port_call: int, ip_listen: str, port_listen: int,
                 allow_push=False):
        """
        启动HTTP上报器
        :param bot_app: BotAPP
        :param ip_call: Event回报ip
        :param port_call: Event回报端口
        :param ip_listen: POST上报ip
        :param port_listen: POST上报端口
        :param allow_push: 是否允许发送主动推送消息(即消息内不含CQ码: [CQ:reply,id=...])
        """
        super().__init__(bot_app, ip_call, port_call)

        self.ip_listen = ip_listen
        self.port_listen = port_listen
        self.allow_push = allow_push
        self.cache = {}

    def send_group_msg(self):
        channel_id = request.args.get("group_id")
        message = request.args.get("message")

        cmsg, reply_msg_id, img_url = message_convert.cq_to_guild_text(message, self.bot.img_to_url)
        if not self.allow_push and reply_msg_id == "":
            self.bot.logger("不发送允许PUSH消息, 请添加回复id, 或者将\"allow_push\"设置为True", warning=True)
        else:
            sendmsg = self.bot.api_send_reply_message(channel_id, reply_msg_id, cmsg, img_url, retstr=True)
            sdata = json.loads(sendmsg)
            if "id" in sdata:
                ret = {
                    "data": {
                        "message_id": sdata["id"]
                    },
                    "retcode": 0,
                    "status": "ok"
                }
            else:
                ret = sdata

            return jsonify(ret)

    def get_self_info(self):
        use_cache = request.args.get("cache")
        selfinfo = self.bot.get_self_info(use_cache)
        return jsonify(message_convert.self_info_convert_to_json(selfinfo))

    def get_group_member_info(self):
        group_id = request.args.get("group_id")
        user_id = request.args.get("user_id")
        no_cache = request.args.get("no_cache")

        if not no_cache and f"get_group_member_info_{group_id}_{user_id}" in self.cache:
            data = self.cache[f"get_group_member_info_{group_id}_{user_id}"]
        else:
            data = message_convert.guild_member_info_convert(self.bot.get_guild_user_info(group_id, user_id), group_id)
            self.cache[f"get_group_member_info_{group_id}_{user_id}"] = data
        return jsonify(data)

    def get_channel_info(self):
        channel_id = request.args.get("channel_id")
        data = self.bot.get_channel_info(channel_id, retstr=True)
        return jsonify(json.loads(data))

    def get_channel_list(self):
        guild_id = request.args.get("guild_id")
        data = self.bot.get_guild_channel_list(guild_id, retstr=True)
        return jsonify(json.loads(data))

    def get_message(self):
        channel_id = request.args.get("channel_id")
        message_id = request.args.get("message_id")
        data = self.bot.get_message(channel_id, message_id, retstr=True)
        return jsonify(json.loads(data))

    def get_self_guild_list(self):
        cache = request.args.get("cache")
        before = "" if request.args.get("before") is None else request.args.get("before")
        after = "" if request.args.get("after") is None else request.args.get("before")
        limit = 100 if request.args.get("limit") is None else request.args.get("limit")
        data = self.bot.get_self_guilds(before=before, after=after, limit=limit, use_cache=cache, retstr=True)
        return jsonify(json.loads(data))

    def get_guild_info(self):
        guild_id = request.args.get("guild_id")
        data = self.bot.get_guild_info(guild_id, retstr=True)
        return jsonify(json.loads(data))


    @staticmethod
    @flask.route("/mark_msg_as_read")
    def mark_msg_as_read():
        return "ok"

    @tools.on_new_thread
    def listening_server_start(self):
        flask.route("/send_group_msg", methods=["GET", "POST"])(self.send_group_msg)
        flask.route("/get_self_info", methods=["GET", "POST"])(self.get_self_info)
        flask.route("/get_self_guild_list", methods=["GET", "POST"])(self.get_self_guild_list)
        flask.route("/get_group_member_info", methods=["GET", "POST"])(self.get_group_member_info)
        flask.route("/get_channel_info", methods=["GET", "POST"])(self.get_channel_info)
        flask.route("/get_channel_list", methods=["GET", "POST"])(self.get_channel_list)
        flask.route("/get_message", methods=["GET", "POST"])(self.get_message)
        flask.route("/get_guild_info", methods=["GET", "POST"])(self.get_guild_info)

        # flask.run(self.ip_listen, self.port_listen)
        self.bot.logger(f"Event回报地址: {self.ip_call}:{self.port_call}")
        self.bot.logger(f"POST上报器启动: {self.ip_listen}:{self.port_listen}")
        wserve(flask, host=self.ip_listen, port=self.port_listen)
