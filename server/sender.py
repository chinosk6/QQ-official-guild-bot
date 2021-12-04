import json

import bot_api
from . import message_convert
from . import tooles
import requests


class MessageSender:
    def __init__(self, bot_app: bot_api.BotApp, ip_call: str, port_call: int):
        self.bot = bot_app
        self.ip_call = ip_call
        self.port_call = port_call


    @tooles.on_new_thread
    def _send_request(self, msg: str, method="POST"):
        try:
            headers = {'Content-Type': 'application/json'}
            requests.request(method=method, url=f"http://{self.ip_call}:{self.port_call}", data=msg, headers=headers)
        except Exception as sb:
            self.bot.logger(f"推送事件失败: {sb}", error=True)

    def reg_bot_at_message(self):
        self.bot.logger("艾特消息推送器已开启")
        self.bot.receiver(bot_api.structs.Codes.SeverCode.BotGroupAtMessage)(self._get_at_message)

    def _get_at_message(self, chain: bot_api.structs.Message):
        self.bot.logger(f"收到来自频道:{chain.guild_id} 子频道: {chain.channel_id} "
                        f"内用户: {chain.author.username}({chain.author.id}) 的消息: {chain.content} ({chain.id})")

        converted_json = message_convert.guild_at_msg_to_groupmsg(chain, self.bot.get_self_info(use_cache=True).id)
        self._send_request(json.dumps(converted_json))
