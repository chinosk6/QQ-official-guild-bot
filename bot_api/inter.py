from .structs import Codes as BCd
from typing import Callable, List
from . import api



class BotMessageDistributor(api.BotApi):
    def __init__(self, appid: int, token: str, secret: str, sandbox: bool, debug=False, api_return_pydantic=False,
                 output_log=True):
        self.debug = debug
        super().__init__(appid=appid, token=token, secret=secret, debug=debug, sandbox=sandbox,
                         api_return_pydantic=api_return_pydantic, output_log=output_log)

        # self.bot_call_before_load: List[Callable] = []  # 加载Bot前执行函数
        self.bot_call_after_load: List[Callable] = []  # 加载Bot完成后执行函数

        self.bot_at_message_group: List[Callable] = []  # 消息处理函数
        self.bot_get_message_pv: List[Callable] = []  # 收到消息(私域)
        self.event_guild_create: List[Callable] = []  # bot加入频道事件
        self.event_guild_update: List[Callable] = []  # 频道信息更新事件
        self.event_guild_delete: List[Callable] = []  # 频道删除事件

        self.event_channel_create: List[Callable] = []  # 子频道创建事件
        self.event_channel_update: List[Callable] = []  # 子频道信息更新事件
        self.event_channel_delete: List[Callable] = []  # 子频道删除事件

        self.event_guild_member_add: List[Callable] = []  # 用户加入频道
        self.event_guild_member_update: List[Callable] = []  # TX: 暂无
        self.event_guild_member_remove: List[Callable] = []  # 用户离开频道

        self.event_audio_start: List[Callable] = []  # 音频开始
        self.event_audio_finish: List[Callable] = []  # 音频结束
        self.event_audio_on_mic: List[Callable] = []  # 机器人上麦
        self.event_audio_off_mic: List[Callable] = []  # 机器人下麦

        self.event_message_reaction_add: List[Callable] = []  # 添加表情表态
        self.event_message_reaction_remove: List[Callable] = []  # 移除表情表态

        self.img_to_url = None  # 图片转为url

        self.modules = {}  # 模块注册

    def receiver(self, reg_type: str, reg_name=""):
        self.logger(f"注册函数: {reg_type} {reg_name}", debug=True)

        def reg(func: Callable):
            def _appender(fl: List[Callable], event_name: str):
                fl.append(func)
                self.logger(f"函数: {func.__name__} 注册到事件: {event_name}", debug=True)

            if reg_type == BCd.SeverCode.BotGroupAtMessage:  # 群艾特处理函数
                _appender(self.bot_at_message_group, "群艾特消息")

            if reg_type == BCd.SeverCode.AT_MESSAGE_CREATE:  # 群艾特处理函数
                _appender(self.bot_at_message_group, "群艾特消息")

            if reg_type == BCd.SeverCode.MESSAGE_CREATE:
                _appender(self.bot_get_message_pv, "收到消息(私域)")

            elif reg_type == BCd.SeverCode.GUILD_CREATE:  # bot加入频道
                _appender(self.event_guild_create, "Bot加入频道消息")

            elif reg_type == BCd.SeverCode.GUILD_UPDATE:  # 频道信息更新
                _appender(self.event_guild_update, "频道更新")

            elif reg_type == BCd.SeverCode.GUILD_DELETE:
                _appender(self.event_guild_delete, "退出频道/频道解散")

            elif reg_type == BCd.SeverCode.CHANNEL_CREATE:  # 子频道创建
                _appender(self.event_channel_create, "子频道创建")

            elif reg_type == BCd.SeverCode.CHANNEL_UPDATE:  # 子频道信息更新
                _appender(self.event_channel_update, "子频道更新")

            elif reg_type == BCd.SeverCode.CHANNEL_DELETE:
                _appender(self.event_channel_delete, "子频道删除")

            elif reg_type == BCd.SeverCode.GUILD_MEMBER_ADD:
                _appender(self.event_guild_member_add, "用户加入频道")

            elif reg_type == BCd.SeverCode.GUILD_MEMBER_UPDATE:
                _appender(self.event_guild_member_update, "用户信息更新")

            elif reg_type == BCd.SeverCode.GUILD_MEMBER_REMOVE:
                _appender(self.event_guild_member_remove, "用户离开频道")

            elif reg_type == BCd.SeverCode.AUDIO_START:
                _appender(self.event_audio_start, "音频开始播放")

            elif reg_type == BCd.SeverCode.AUDIO_FINISH:
                _appender(self.event_audio_finish, "音频结束")

            elif reg_type == BCd.SeverCode.AUDIO_ON_MIC:
                _appender(self.event_audio_on_mic, "机器人上麦")

            elif reg_type == BCd.SeverCode.AUDIO_OFF_MIC:
                _appender(self.event_audio_off_mic, "机器人下麦")

            elif reg_type == BCd.SeverCode.MESSAGE_REACTION_ADD:
                _appender(self.event_message_reaction_add, "添加表情表态")

            elif reg_type == BCd.SeverCode.MESSAGE_REACTION_REMOVE:
                _appender(self.event_message_reaction_remove, "移除表情表态")

            elif reg_type == BCd.SeverCode.FUNC_CALL_AFTER_BOT_LOAD:
                _appender(self.bot_call_after_load, "Bot载入完成后加载函数")

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
