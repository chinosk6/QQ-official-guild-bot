import json

import bot_api
from . import message_convert
from . import tools
import requests


class MessageSender:
    def __init__(self, bot_app: bot_api.BotApp, ip_call: str, port_call: int):
        self.bot = bot_app
        self.ip_call = ip_call
        self.port_call = port_call


    @tools.on_new_thread
    def _send_request(self, msg: str, method="POST"):
        try:
            self.bot.logger(f"推送事件: {msg}", debug=True)
            headers = {'Content-Type': 'application/json'}
            requests.request(method=method, url=f"http://{self.ip_call}:{self.port_call}", data=msg, headers=headers)
        except Exception as sb:
            self.bot.logger(f"推送事件失败: {sb}", error=True)

    def reg_bot_at_message(self):
        """
        开启艾特消息Event
        """
        self.bot.logger("艾特消息Event已开启")
        self.bot.receiver(bot_api.structs.Codes.SeverCode.BotGroupAtMessage)(self._get_at_message)

    def reg_guild_member_add(self):
        """
        开启成员增加Event
        """
        self.bot.logger("成员增加Event已开启")
        self.bot.receiver(bot_api.structs.Codes.SeverCode.GUILD_MEMBER_ADD)(self._get_guild_member_change(True))

    def reg_guild_member_remove(self):
        """
        开启成员减少Event
        """
        self.bot.logger("成员减少Event已开启")
        self.bot.receiver(bot_api.structs.Codes.SeverCode.GUILD_MEMBER_REMOVE)(self._get_guild_member_change(False))

    def reg_guild_create(self):
        """
        开启Bot加入频道Event
        """
        self.bot.logger("Bot加入频道Event已开启")
        self.bot.receiver(bot_api.structs.Codes.SeverCode.GUILD_CREATE)(self._get_guild_change("guild_create"))

    def reg_guild_delete(self):
        """
        开启Bot离开频道Event
        """
        self.bot.logger("Bot离开频道Event已开启")
        self.bot.receiver(bot_api.structs.Codes.SeverCode.GUILD_DELETE)(self._get_guild_change("guild_delete"))

    def reg_guild_update(self):
        """
        开启频道信息更新Event
        """
        self.bot.logger("频道信息更新Event已开启")
        self.bot.receiver(bot_api.structs.Codes.SeverCode.GUILD_DELETE)(self._get_guild_change("guild_update"))

    def reg_channel_create(self):
        """
        开启子频道创建Event
        """
        self.bot.logger("子频道创建Event已开启")
        self.bot.receiver(bot_api.structs.Codes.SeverCode.CHANNEL_CREATE)(self._get_channel_change("channel_create"))

    def reg_channel_update(self):
        """
        开启子频道更新Event
        """
        self.bot.logger("子频道更新Event已开启")
        self.bot.receiver(bot_api.structs.Codes.SeverCode.CHANNEL_UPDATE)(self._get_channel_change("channel_update"))

    def reg_channel_delete(self):
        """
        开启子频道删除Event
        """
        self.bot.logger("子频道删除Event已开启")
        self.bot.receiver(bot_api.structs.Codes.SeverCode.CHANNEL_DELETE)(self._get_channel_change("channel_delete"))


    def _get_channel_change(self, notice_type):
        def send_channel(event: bot_api.structs.Channel):
            converted_json = message_convert.others_event(selfid=self.bot.get_self_info(use_cache=True).id,
                                                          post_type="notice", notice_type=notice_type,
                                                          sub_type=notice_type,
                                                          user_id="", guiid_id=event.guild_id, channel_id=event.id,
                                                          data=event)
            self._send_request(json.dumps(converted_json))
        return send_channel

    def _get_guild_change(self, notice_type):
        def send_guild(event: bot_api.structs.Guild):
            converted_json = message_convert.others_event(selfid=self.bot.get_self_info(use_cache=True).id,
                                                          post_type="notice", notice_type=notice_type,
                                                          sub_type=notice_type,
                                                          user_id="", guiid_id=event.id, channel_id="", data=event)
            self._send_request(json.dumps(converted_json))
        return send_guild

    def _get_guild_member_change(self, is_useradd: bool):
        def send_member_change(event: bot_api.structs.MemberWithGuildID):
            converted_json = message_convert.guild_member_change_convert(event, self.bot.get_self_info(use_cache=True).id,
                                                                         is_useradd=is_useradd)
            self._send_request(json.dumps(converted_json))
        return send_member_change

    def _get_at_message(self, chain: bot_api.structs.Message):
        self.bot.logger(f"收到来自频道:{chain.guild_id} 子频道: {chain.channel_id} "
                        f"内用户: {chain.author.username}({chain.author.id}) 的消息: {chain.content} ({chain.id})")

        converted_json = message_convert.guild_at_msg_to_groupmsg(chain, self.bot.get_self_info(use_cache=True).id)
        self._send_request(json.dumps(converted_json))
