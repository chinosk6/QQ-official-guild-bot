from . import inter
from .structs import Codes as BCd
import websocket
import json
import requests
import time
from threading import Thread
import typing as t
import os

event_types = BCd.QBot.GatewayEventName

class Intents:  # https://bot.q.qq.com/wiki/develop/api/gateway/intents.html
    GUILDS = 1 << 0
    GUILD_MEMBERS = 1 << 1
    DIRECT_MESSAGE = 1 << 12
    AUDIO_ACTION = 1 << 29
    AT_MESSAGES = 1 << 30
    GUILD_MESSAGE_REACTIONS = 1 << 10
    FORUM_EVENT = 1 << 28
    MESSAGE_CREATE = 1 << 9

def on_new_thread(f):
    def task_qwq(*args, **kwargs):
        _t = Thread(target=f, args=args, kwargs=kwargs)
        _t.start()
    return (task_qwq)


class BotApp(inter.BotMessageDistributor):
    def __init__(self, appid: int, token: str, secret: str, is_sandbox: bool, inters: t.List,
                 debug=False, api_return_pydantic=False, ignore_at_self=False, output_log=True, log_path=""):
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
        :param output_log: 是否输出日志到本地
        :param log_path: 日志输出位置, 默认为sdk目录内log文件夹
        """
        super().__init__(appid=appid, token=token, secret=secret, sandbox=is_sandbox, debug=debug,
                         api_return_pydantic=api_return_pydantic, output_log=output_log, log_path=log_path)
        self.inters = inters
        self.ignore_at_self = ignore_at_self
        self.self_id = ""
        self.self_name = ""
        self.EVENT_MESSAGE_CREATE_CALL_AT_MESSAGE_CREATE = False
        self.session_id = None
        self._d = None  # 心跳参数
        self._t = None
        self.heartbeat_time = -1  # 心跳间隔
        self.ws = None
        self._spath = os.path.split(__file__)[0]

    # @on_new_thread
    def start(self):
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

                    def _send_event(m_dantic, changed_data=None, changed_s_type=None):
                        """
                        事件聚合分发
                        :param m_dantic: 要发送的消息(Basemodel)
                        :param changed_data: 需要修改的消息, 默认为data["d"]
                        :param changed_s_type: 需要修改的消息类型, 默认为s_type, 即data["t"]
                        :return:
                        """
                        _send_data = data["d"] if changed_data is None else changed_data
                        _send_type = s_type if changed_s_type is None else changed_s_type
                        self._event_handout(_send_type, m_dantic(**_send_data))

                    if s_type == event_types.READY:  # 验证完成
                        self.session_id = data["d"]["session_id"]
                        self._on_open(data["d"]["user"]["id"], data["d"]["user"]["username"], data["d"]["user"]["bot"],
                                      is_login=True)
                        self.send_heart_beat(self.ws)

                    elif s_type == event_types.RESUMED:  # 服务器通知重连
                        self.logger("重连完成, 事件已全部补发")

                    elif s_type in self.known_events:
                        s_dantic = self.known_events[s_type][1]
                        if s_dantic is not None:
                            if s_type in [event_types.AT_MESSAGE_CREATE, event_types.MESSAGE_CREATE]:
                                if self.ignore_at_self:
                                    data["d"]["content"] = data["d"]["content"].replace(f"<@!{self.self_id}>",
                                                                                        "").strip()
                                if s_type == event_types.MESSAGE_CREATE:  # 收到消息(私域)
                                    if self.EVENT_MESSAGE_CREATE_CALL_AT_MESSAGE_CREATE:  # 普通消息依旧调用艾特消息函数
                                        _send_event(self.known_events[event_types.AT_MESSAGE_CREATE][1],
                                                    changed_s_type=event_types.AT_MESSAGE_CREATE)
                            _send_event(s_dantic)

                    # TODO 主题相关事件

                    else:
                        self.logger(f"收到未知或暂不支持的推送消息: {data}", debug=True)


            elif stat_code == BCd.QBot.OPCode.Reconnect:  # 服务器通知重连
                self.logger("服务器通知重连")
                self._on_close()

            elif stat_code == BCd.QBot.OPCode.Invalid_Session:  # 验证失败
                self.logger("连接失败: Invalid Session", error=True)
                self._on_close(active_close=True)

        except Exception as sb:
            self.logger(sb, error=True)


    def _event_handout(self, func_type: str, *args, **kwargs):
        if func_type in self.bot_events:
            throw_func = self.bot_events[func_type]
            if throw_func:
                for f in throw_func:
                    _t = Thread(target=f, args=args, kwargs=kwargs)
                    _t.start()

    def _check_files(self):
        pass

    def _on_open(self, botid="", botname="", isbot="", is_login=False):
        if is_login:
            self.self_id = botid
            self.self_name = botname
            self.logger(f"开始运行:\nBotID: {botid}\nBotName: {botname}\nbot: {isbot}")
            self._check_files()
            self._event_handout(BCd.SeverCode.FUNC_CALL_AFTER_BOT_LOAD, self)
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
        try:
            self.logger(f"获取服务器api: {response.json()['url']}", debug=True)
            return response.json()["url"]
        except Exception as sb:
            self.logger(f"获取服务器API失败 - {response.text}")
            print(sb)


    def _get_inters_code(self):
        if type(self.inters) != list:
            self.logger("事件订阅(inters)错误, 将使用默认值", error=True)
            return 1073741827

        result = 0
        for _int in self.inters:
            result = result | _int

        self.logger(f"intents计算结果: {result}", debug=True)
        return result
