from . import structs
from typing import Callable, List, Dict
from . import api

BCd = structs.Codes

class BotMessageDistributor(api.BotApi):
    def __init__(self, appid: int, token: str, secret: str, sandbox: bool, debug=False, api_return_pydantic=False,
                 output_log=True, log_path=""):
        self.debug = debug
        super().__init__(appid=appid, token=token, secret=secret, debug=debug, sandbox=sandbox,
                         api_return_pydantic=api_return_pydantic, output_log=output_log, log_path=log_path)

        self.known_events = {BCd.SeverCode.BotGroupAtMessage: ["群艾特消息", structs.Message],
                             BCd.SeverCode.AT_MESSAGE_CREATE: ["群艾特消息", structs.Message],
                             BCd.SeverCode.MESSAGE_CREATE: ["收到消息(私域)", structs.Message],
                             BCd.SeverCode.GUILD_CREATE: ["Bot加入频道消息", structs.Guild],
                             BCd.SeverCode.GUILD_UPDATE: ["频道更新", structs.Guild],
                             BCd.SeverCode.GUILD_DELETE: ["频道更新", structs.Guild],
                             BCd.SeverCode.CHANNEL_CREATE: ["子频道创建", structs.Channel],
                             BCd.SeverCode.CHANNEL_UPDATE: ["子频道更新", structs.Channel],
                             BCd.SeverCode.CHANNEL_DELETE: ["子频道删除", structs.Channel],
                             BCd.SeverCode.GUILD_MEMBER_ADD: ["用户加入频道", structs.MemberWithGuildID],
                             BCd.SeverCode.GUILD_MEMBER_UPDATE: ["用户信息更新", structs.MemberWithGuildID],
                             BCd.SeverCode.GUILD_MEMBER_REMOVE: ["用户离开频道", structs.MemberWithGuildID],
                             BCd.SeverCode.AUDIO_START: ["音频开始播放", structs.AudioAction],
                             BCd.SeverCode.AUDIO_FINISH: ["音频结束", structs.AudioAction],
                             BCd.SeverCode.AUDIO_ON_MIC: ["上麦", structs.AudioAction],
                             BCd.SeverCode.AUDIO_OFF_MIC: ["下麦", structs.AudioAction],
                             BCd.SeverCode.MESSAGE_REACTION_ADD: ["添加表情表态", structs.MessageReaction],
                             BCd.SeverCode.MESSAGE_REACTION_REMOVE: ["移除表情表态", structs.MessageReaction],
                             BCd.SeverCode.FUNC_CALL_AFTER_BOT_LOAD: ["Bot载入完成后加载函数", None],
                             BCd.SeverCode.MESSAGE_AUDIT_PASS: ["消息审核通过", structs.MessageAudited],
                             BCd.SeverCode.MESSAGE_AUDIT_REJECT: ["消息审核不通过", structs.MessageAudited]
                             }

        self.bot_events: Dict[str, List] = {}

        self.img_to_url = None  # 图片转为url

        self.modules = {}  # 模块注册

    def receiver(self, reg_type: str, reg_name=""):
        self.logger(f"注册函数: {reg_type} {reg_name}", debug=True)

        def reg(func: Callable):
            def _adder(event_type, event_name):
                if event_type not in self.bot_events:
                    self.bot_events[event_type] = []
                self.bot_events[event_type].append(func)
                self.logger(f"函数: {func.__name__} 注册到事件: {event_name}", debug=True)

            if reg_type in self.known_events:
                _adder(reg_type, self.known_events[reg_type][0])

            elif reg_type == BCd.SeverCode.image_to_url:
                if self.img_to_url is not None:
                    self.logger(f"图片转url只允许注册一次。 生效函数由 {self.img_to_url.__name__} 更改为 {func.__name__}",
                                warning=True)
                self.img_to_url = func

            elif reg_type == BCd.SeverCode.Module:  # 注册自定义模块
                if reg_name != "":
                    self.modules[reg_name] = func

        return reg

    def call_module(self, module, *args, **kwargs):  # 调用模块
        return self.modules[module](*args, **kwargs)
