from . import inter
from . import structs
from . import api
from . import models
from .structs import Codes as BCd
import websocket
import json
import requests
import time
from threading import Thread
import typing as t


class Intents:  # https://bot.q.qq.com/wiki/develop/api/gateway/intents.html
    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1
    DIRECT_MESSAGE = 1 << 12
    AUDIO_ACTION = 1 << 29
    AT_MESSAGES = 1 << 30

def on_new_thread(f):
    def task_qwq(*args, **kwargs):
        _t = Thread(target=f, args=args, kwargs=kwargs)
        _t.start()
    return (task_qwq)


class BotApp(inter.BotMessageDistributor):
    def __init__(self, appid: int, token: str, secret: str, is_sandbox: bool, inters: t.List,
                 debug=False, api_return_pydantic=False, ignore_at_self=False):
        """
        BotAPP
        :param appid: BotAPPId
        :param token: BotToken
        :param secret: BotSecret
        :param is_sandbox: 是否在测试环境运行
        :param inters: 接收事件
        :param debug: 输出debug日志
        :param api_return_pydantic: 调用api后返回pydantic对象, 默认为纯文本
        :param ignore_at_self: 过滤消息中艾特bot的内容
        """
        super().__init__(appid=appid, token=token, secret=secret, sandbox=is_sandbox, debug=debug,
                         api_return_pydantic=api_return_pydantic)
        self.inters = inters
        self.ignore_at_self = ignore_at_self
        self.self_id = ""
        self.self_name = ""
        self.session_id = None
        self._d = None  # 心跳参数
        self._t = None
        self.heartbeat_time = -1  # 心跳间隔
        self.ws = None

    # @on_new_thread
    def start(self):
        if not self.bot_at_message_group:
            self.logger("未注册艾特消息处理器", warning=True)

        websocket.enableTrace(False)
        self.ws = self._get_connection()
        self.ws.run_forever()

    def _get_connection(self):
        ws = websocket.WebSocketApp(url=self._get_websocket_url(),
                                    on_message=self._on_message,
                                    on_open=self._on_open,
                                    on_error=self._ws_on_error,
                                    on_close=self._on_close
                                    )
        return ws

    def _get_verify_body(self, reconnect=False):
        if reconnect:
            rb = {
                "op": 6,
                "d": {
                    "token": f'Bot {self.appid}.{self.token}',
                    "session_id": self.session_id,
                    "seq": 1337
                }
            }
        else:
            rb = {
                "op": 2,
                "d": {
                    "token": f'Bot {self.appid}.{self.token}',
                    "intents": self._get_inters_code(),  # 1073741827
                    "shard": [0, 1],
                    "properties": {
                        "$os": "linux",
                        "$browser": "python_sdk",
                        "$device": "server"
                    }
                }
            }

        return rb

    def _ws_on_error(self, ws, err, *args):
        try:
            raise err
        except websocket.WebSocketConnectionClosedException:
            self._on_close()

        self.logger(f"Error: {args}", error=True)

    def _on_message(self, ws, msg):  # 收到ws消息
        try:
            self.logger(msg, debug=True)
            data = json.loads(msg)
            stat_code = data["op"]  # 状态码, 参考: https://bot.q.qq.com/wiki/develop/api/gateway/opcode.html

            if stat_code == BCd.QBot.OPCode.Hello:  # 网关下发的第一条消息
                if "heartbeat_interval" in data["d"]:  # 初始化心跳
                    self.heartbeat_time = data["d"]["heartbeat_interval"] / 1000
                    ws.send(json.dumps(self._get_verify_body()))

            elif stat_code == BCd.QBot.OPCode.Dispatch:  # 服务器主动推送消息
                self._d = data["s"]
                if "t" in data:
                    s_type = data["t"]
                    if s_type == BCd.QBot.GatewayEventName.READY:  # 验证完成
                        self.session_id = data["d"]["session_id"]
                        self._on_open(data["d"]["user"]["id"], data["d"]["user"]["username"], data["d"]["user"]["bot"],
                                      is_login=True)
                        self.send_heart_beat(self.ws)


                    elif s_type == BCd.QBot.GatewayEventName.RESUMED:  # 服务器通知重连
                        self.logger("重连完成, 事件已全部补发")

                    elif s_type == BCd.QBot.GatewayEventName.AT_MESSAGE_CREATE:  # 用户艾特Bot
                        if self.ignore_at_self:
                            data["d"]["content"] = data["d"]["content"].replace(f"<@!{self.self_id}>", "").strip()
                        self._event_handout(self.bot_at_message_group, structs.Message(**data["d"]))

                    elif s_type == BCd.QBot.GatewayEventName.GUILD_CREATE:  # bot加入频道
                        self._event_handout(self.event_guild_create, structs.Guild(**data["d"]))
                    elif s_type == BCd.QBot.GatewayEventName.GUILD_UPDATE:
                        self._event_handout(self.event_guild_update, structs.Guild(**data["d"]))
                    elif s_type == BCd.QBot.GatewayEventName.GUILD_DELETE:
                        self._event_handout(self.event_guild_delete, structs.Guild(**data["d"]))

                    elif s_type == BCd.QBot.GatewayEventName.CHANNEL_CREATE:  # 子频道三事件
                        self._event_handout(self.event_channel_create, structs.Channel(**data["d"]))
                    elif s_type == BCd.QBot.GatewayEventName.CHANNEL_UPDATE:
                        self._event_handout(self.event_channel_update, structs.Channel(**data["d"]))
                    elif s_type == BCd.QBot.GatewayEventName.CHANNEL_DELETE:
                        self._event_handout(self.event_channel_delete, structs.Channel(**data["d"]))

                    elif s_type == BCd.QBot.GatewayEventName.GUILD_MEMBER_ADD:  # 用户三事件
                        self._event_handout(self.event_guild_member_add, structs.MemberWithGuildID(**data["d"]))
                    elif s_type == BCd.QBot.GatewayEventName.GUILD_MEMBER_UPDATE:  # TX: 暂无
                        self._event_handout(self.event_guild_member_update, structs.MemberWithGuildID(**data["d"]))
                    elif s_type == BCd.QBot.GatewayEventName.GUILD_MEMBER_REMOVE:
                        self._event_handout(self.event_guild_member_remove, structs.MemberWithGuildID(**data["d"]))

                    elif s_type == BCd.QBot.GatewayEventName.AUDIO_START:  # 音频四事件
                        self._event_handout(self.event_audio_start, structs.AudioAction(**data["d"]))
                    elif s_type == BCd.QBot.GatewayEventName.AUDIO_FINISH:
                        self._event_handout(self.event_audio_finish, structs.AudioAction(**data["d"]))
                    elif s_type == BCd.QBot.GatewayEventName.AUDIO_ON_MIC:
                        self._event_handout(self.event_audio_on_mic, structs.AudioAction(**data["d"]))
                    elif s_type == BCd.QBot.GatewayEventName.AUDIO_OFF_MIC:
                        self._event_handout(self.event_audio_off_mic, structs.AudioAction(**data["d"]))


            elif stat_code == BCd.QBot.OPCode.Reconnect:  # 服务器通知重连
                self.logger("服务器通知重连")
                self._on_close()

            elif stat_code == BCd.QBot.OPCode.Invalid_Session:  # 验证失败
                self.logger("连接失败: Invalid Session", error=True)
                self._on_close(active_close=True)

        except Exception as sb:
            self.logger(sb, error=True)

    @staticmethod
    def _event_handout(throw_func: t.List[t.Callable], *args):
        if throw_func:
            for f in throw_func:
                _t = Thread(target=f, args=args)
                _t.start()

    def _on_open(self, botid="", botname="", isbot="", is_login=False):
        if is_login:
            self.self_id = botid
            self.self_name = botname
            self.logger(f"开始运行:\nBotID: {botid}\nBotName: {botname}\nbot: {isbot}")
        else:
            self.logger("开始尝试连接")

    def _on_close(self, *args, active_close=False):
        self.logger(f"on_close {args}", debug=True)
        try:
            self.heartbeat_time = -1
            self._d = None
            self.ws.close()
        except Exception as sb:
            self.logger(f"关闭连接失败: {sb}", error=True)

        if not active_close:
            self.heartbeat_time = -1
            self._d = None
            self.logger("连接断开, 尝试重连", warning=True)
            self.ws = self._get_connection()
            self.ws.run_forever()
            self.ws.send(json.dumps(self._get_verify_body(reconnect=True)))
        else:
            self.logger("连接已断开", warning=True)

    def send_heart_beat(self, ws):

        def _send_heart_beat():
            try:
                while True:
                    if self.heartbeat_time != -1 and self._d is not None:
                        self.logger(f"发送心跳: {self._d}", debug=True)

                        self.ws.send(json.dumps({"op": 1, "d": self._d}))
                        time.sleep(self.heartbeat_time)
                    else:
                        continue
            except websocket.WebSocketConnectionClosedException:
                self.logger("发送心跳包失败", error=True)
                self._on_close()

        if self._t is None:
            self._t = Thread(target=_send_heart_beat)
            self._t.start()
        else:
            if not self._t.is_alive():
                self._t = Thread(target=_send_heart_beat)
                self._t.start()


    def _get_websocket_url(self):
        url = f"{self.base_api}/gateway"
        headers = {'Authorization': f'Bot {self.appid}.{self.token}'}
        response = requests.request("GET", url, headers=headers)
        self.logger(f"获取服务器api: {response.json()['url']}", debug=True)
        return response.json()["url"]


    def _get_inters_code(self):
        if type(self.inters) != list:
            self.logger("事件订阅(inters)错误, 将使用默认值", error=True)
            return 1073741827

        result = 0
        for _int in self.inters:
            result = result | _int

        self.logger(f"intents计算结果: {result}", debug=True)
        return result
