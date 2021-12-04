import json
import threading
import time
from typing import Any, Optional
import typing as t

import websocket


class wsc:
    """ws客户端实现"""

    def __init__(self, url: str, token: str, eventManager: Any, shard: t.List[int], s: Optional[int] = None, session:
    Optional[str] = None) -> None:
        self.ws = None
        self.path = url
        self.token = token
        self.shard = shard
        self.__eventManager = eventManager
        self.intents = int("01100000000000000000000000000011", 2)
        self.s = s
        self.session = session
        self.Heartbeat_out = True

    def authorization(self, ws):
        """
        鉴权
        ---
        进行登录
        """
        if self.session == None:
            load = {
                "op": 2,
                "d": {
                    "token": self.token,
                    "intents": self.intents,
                    "shard": [0, 1],
                    "properties": {
                        "$os": "linux",
                        "$browser": "python_sdk",
                        "$device": "server"
                    }
                }
            }
        else:
            print(f"分片掉线，进行重连")
            load = {
                "op": 6,
                "d": {
                    "token": self.token,
                    "session_id": self.session,
                    "seq": 1337
                }
            }
        ws.send(json.dumps(load))
        print(f"发送链接信息")

    def Heartbeat(self, event, ws):
        print(f"开始发送心跳")
        while self.Heartbeat:
            if not event.wait(self.heartbeat_interval):
                data = {
                    "op": opcode.Heartbeat,
                    "d": self.s
                }
                try:
                    ws.send(json.dumps(data))
                    print(f"s={self.s} 发送心跳")
                except:
                    break

    def sendEvent(self, type: str, data: Any):
        """
        事件发送器
        ---------
        封装一个常用的事件发送方法
        """
        event = Event(type_=type)
        event.dict["artical"] = data
        self.__eventManager.SendEvent(event)

    def on_opend(self, ws):
        """
        WS打开事件
        --
        ws打开时会调用的函数
        """
        logger.info('WS打开')

    def start_heart(self, ws):
        event = threading.Event()
        t = threading.Thread(target=self.Heartbeat, args=(event, ws))
        t.setDaemon(True)
        t.start()

    def on_message(self, ws, message):
        # print(message)
        data = json.loads(message)
        load = Load(**data)
        op = load.op
        if op == opcode.Hello:
            self.heartbeat_interval = load.d.heartbeat_interval / 1000
            logger.info(f"收到Hello信息，心跳间隔为{self.heartbeat_interval}秒")
            self.authorization(ws)
        elif op == opcode.Dispatch:
            self.s = load.s
            t = load.t
            # logger.debug(f"收到事件：{t}")
            # 这里阻止两个基本事件进入事件处理器
            if t == "READY":
                logger.info(f"收到READY信息，鉴权成功！欢迎{load.d.user.username}")
                self.session = load.d.session_id
                self.start_heart(ws)
            elif t == "RESUMED":
                logger.info("重连成功")
                self.start_heart(ws)
            else:
                # 将事件推送到事件处理器
                self.sendEvent(type=t, data=load.d)

        elif op == opcode.HeartbeatACK:
            logger.debug("收到心跳响应")

    def on_close(self, ws, close_status_code, close_msg):
        logger.warning(f"WS连接关闭 {close_status_code} - {close_msg}")
        self.Heartbeat_out = False

    def send(self, message):
        self.ws.send(json.dumps(message))
        print("发送完毕")

    def on_error(self, ws, error):
        logger.error(f"WS连接出现错误，错误是：{error}")

    def run(self):
        websocket.enableTrace(False)
        self.ws = websocket.WebSocketApp(self.path,
                                         on_open=self.on_opend,
                                         on_message=self.on_message,
                                         on_error=self.on_error,
                                         on_close=self.on_close)

        self.ws.run_forever()
