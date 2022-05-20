import requests
import json
from . import structs
import typing as t
from . import models
from .logger import BotLogger


class BotApi(BotLogger):
    def __init__(self, appid: int, token: str, secret: str, debug: bool, sandbox: bool, api_return_pydantic=False,
                 output_log=True, log_path="", raise_api_error=False):
        super().__init__(debug=debug, write_out_log=output_log, log_path=log_path)
        self.appid = appid
        self.token = token
        self.secret = secret
        self.base_api = "https://sandbox.api.sgroup.qq.com" if sandbox else "https://api.sgroup.qq.com"
        self.debug = debug
        self.api_return_pydantic = api_return_pydantic
        self.raise_api_error = raise_api_error

        self.__headers = {
            'Authorization': f'Bot {self.appid}.{self.token}',
            'Content-Type': 'application/json'
        }

        self._cache = {}

    def _throwerr(self, error_response: str, error_message="", trace_id=None):
        """
        抛出API异常
        :param error_response: API返回信息
        :param error_message: 自定义描述
        :param trace_id: X-TPS-TRACE-ID
        """
        if self.raise_api_error:
            raise models.BotCallingAPIError(error_response, error_message, x_tps_trace_id=trace_id)

    def _tlogger(self, msg: str, debug=False, warning=False, error=False, error_resp=None, traceid=None):
        smsg = f"{msg}\nX-Tps-trace-ID: {traceid}\n" if traceid is not None else msg
        super().logger(msg=smsg, debug=debug, warning=warning, error=error)
        if error_resp is not None and error:
            self._throwerr(error_response=error_resp, error_message=smsg, trace_id=traceid)

    def _retter(self, response: requests.Response, wrong_text: str, data_model, retstr: bool, data_type=0):
        """
        返回器
        :param response: api返回值
        :param wrong_text: 错误信息
        :param data_model: pydantic_model信息
        :param retstr: 是否强制返回纯文本
        :param data_type: pydantic_model类型: 0-str, 1-List
        :return:
        """
        get_response = response.text
        trace_id = response.headers.get("X-Tps-trace-ID")
        data = json.loads(get_response)
        if "code" in data:
            self._tlogger(f"{wrong_text}: {get_response}", error=True, error_resp=get_response, traceid=trace_id)
            # if retstr:
            return get_response
            # return None
        elif self.api_return_pydantic and not retstr:
            try:
                if data_type == 0:
                    return data_model(**data)
                elif data_type == 1:
                    return [data_model(**g) for g in data]
                else:
                    self._tlogger("retter_data_type错误, 将原样返回", warning=True)

                    return get_response
            except Exception as sb:
                self._tlogger("请求转换为 Basemodel 失败, 将原样返回", error=True)
                self._tlogger(f"请求原文: {get_response}", debug=True, traceid=trace_id)
                print(sb)
                return get_response
        else:
            return get_response

    def api_create_dms(self, recipient_id, source_guild_id, retstr=False) -> t.Union[structs.DMS, str]:
        """
        创建私信会话
        :param recipient_id: 接收者 id
        :param source_guild_id: 源频道 id
        :param retstr: 强制返回文本
        :return: DMS对象
        """
        url = f"{self.base_api}/users/@me/dms"
        payload = {
            "recipient_id": recipient_id,
            "source_guild_id": source_guild_id
        }
        response = requests.request("POST", url, data=json.dumps(payload), headers=self.__headers)
        return self._retter(response, "创建私信会话失败", structs.DMS, retstr, data_type=0)

    def api_reply_message(self, event: structs.Message, content="", image_url="", retstr=False,
                          embed=None, ark=None, others_parameter: t.Optional[t.Dict] = None, at_user=True,
                          message_reference=True, **kwargs) \
            -> t.Union[str, structs.Message, None]:
        """
        快速回复消息, 支持频道消息/私聊消息
        :param event: 原event
        :param content: 消息内容, 可空
        :param image_url: 图片url, 可空
        :param retstr: 调用此API后返回纯文本
        :param embed: embed消息, 可空
        :param ark: ark消息, 可空
        :param others_parameter: 其它自定义字段
        :param at_user: 艾特被回复者
        :param message_reference: 引用对应消息
        """
        event_type = event.message_type_sdk
        if at_user:
            if "<@" not in content and event_type != "private":
                content = f"<@{event.author.id}>\n{content}"

        ref_type = 1 if message_reference else 0

        if event_type == "guild":
            return self.api_send_message(channel_id=event.channel_id, msg_id=event.id, content=content,
                                         image_url=image_url, retstr=retstr, embed=embed, ark=ark,
                                         others_parameter=others_parameter, message_reference_type=ref_type, **kwargs)
        elif event_type == "private":
            return self.api_send_private_message(guild_id=event.guild_id, channel_id=event.channel_id, msg_id=event.id,
                                                 content=content, image_url=image_url,
                                                 retstr=retstr, embed=embed, ark=ark, others_parameter=others_parameter,
                                                 message_reference_type=ref_type, **kwargs)
        else:
            self.logger("reply_message() - 无法识别传入的event", error=True)
            return None

    def api_send_message(self, channel_id, msg_id="", content="", image_url="", retstr=False,
                         embed=None, ark=None, message_reference_type=0, message_reference_id=None,
                         others_parameter: t.Optional[t.Dict] = None, **kwargs) \
            -> t.Union[str, structs.Message, None]:
        """
        发送消息
        :param channel_id: 子频道ID
        :param msg_id: 消息ID, 可空
        :param content: 消息内容, 可空
        :param image_url: 图片url, 可空
        :param retstr: 调用此API后返回纯文本
        :param embed: embed消息, 可空
        :param ark: ark消息, 可空
        :param message_reference_type: 引用消息, 0-不引用; 1-引用消息, 不忽略获取引用消息详情错误; 2- 引用消息, 忽略获取引用消息详情错误
        :param message_reference_id: 引用消息的ID, 若为空, 则使用"msg_id"字段的值
        :param others_parameter: 其它自定义字段
        """
        return self._api_send_message(channel_id=channel_id, msg_id=msg_id, content=content, image_url=image_url,
                                      retstr=retstr, embed=embed, ark=ark,
                                      message_reference_type=message_reference_type,
                                      message_reference_id=message_reference_id, others_parameter=others_parameter,
                                      **kwargs)

    def api_send_private_message(self, guild_id, channel_id, msg_id="", content="", image_url="", retstr=False,
                                 embed=None, ark=None, message_reference_type=0, message_reference_id=None,
                                 others_parameter: t.Optional[t.Dict] = None, **kwargs):
        """
        发送私聊消息
        :param guild_id: 频道ID
        :param channel_id: 子频道ID
        :param msg_id: 消息ID, 可空
        :param content: 消息内容, 可空
        :param image_url: 图片url, 可空
        :param retstr: 调用此API后返回纯文本
        :param embed: embed消息, 可空
        :param ark: ark消息, 可空
        :param message_reference_type: 引用消息, 0-不引用; 1-引用消息, 不忽略获取引用消息详情错误; 2- 引用消息, 忽略获取引用消息详情错误
        :param message_reference_id: 引用消息的ID, 若为空, 则使用"msg_id"字段的值
        :param others_parameter: 其它自定义字段
        """
        return self._api_send_message(channel_id=channel_id, msg_id=msg_id, content=content, image_url=image_url,
                                      retstr=retstr, embed=embed, ark=ark, others_parameter=others_parameter,
                                      message_reference_type=message_reference_type,
                                      message_reference_id=message_reference_id,
                                      guild_id=guild_id, **kwargs)

    def _api_send_message(self, channel_id, msg_id="", content="", image_url="", retstr=False,
                          embed=None, ark=None, others_parameter: t.Optional[t.Dict] = None, guild_id=None,
                          message_reference_type=0, message_reference_id=None, is_markdown=False) \
            -> t.Union[str, structs.Message, None]:
        """
        发送消息
        :param channel_id: 子频道ID
        :param msg_id: 消息ID, 可空
        :param content: 消息内容, 可空
        :param image_url: 图片url, 可空
        :param retstr: 调用此API后返回纯文本
        :param embed: embed消息, 可空
        :param ark: ark消息, 可空
        :param others_parameter: 其它自定义字段
        :param guild_id: 填写该字段后将发送私聊消息
        :param message_reference_type: 引用消息, 0-不引用; 1-引用消息, 不忽略获取引用消息详情错误; 2- 引用消息, 忽略获取引用消息详情错误
        :param message_reference_id: 引用消息的ID, 若为空, 则使用"msg_id"字段的值
        """

        url = f"{self.base_api}/channels/{channel_id}/messages" if guild_id is None else \
            f"{self.base_api}/dms/{guild_id}/messages"
        if content == "" and image_url == "" and embed is None and ark is None and others_parameter is None:
            self._tlogger("消息为空, 请检查", error=True)
            return None

        if content != "":
            if is_markdown:
                _c = {"markdown": {"content": content}}
            else:
                _c = {"content": content}
        else:
            _c = None

        _im = {"image": image_url} if image_url != "" else None
        _msgid = {"msg_id": msg_id} if msg_id != "" else None
        _embed = embed.ark_to_json() if callable(getattr(embed, "ark_to_json", None)) else None
        _ark = ark.ark_to_json() if callable(getattr(ark, "ark_to_json", None)) else None

        message_reference_id = msg_id if message_reference_id is None else message_reference_id
        _ref = {"message_reference": {"message_id": message_reference_id,
                                      "ignore_get_message_error": False if message_reference_type == 1 else True}} \
            if message_reference_id and message_reference_type else None

        def merge_dict(*args) -> dict:
            merged = {}
            for _d in args:
                if _d is not None:
                    merged = {**merged, **_d}
            return merged

        payload = json.dumps(merge_dict(_c, _im, _msgid, _embed, _ark, _ref, others_parameter))

        response = requests.request("POST", url, headers=self.__headers, data=payload)
        return self._retter(response, "发送信息失败", structs.Message, retstr)

    def api_mute_guild(self, guild_id, mute_seconds="", mute_end_timestamp="",
                       user_ids: t.Optional[t.List[str]] = None) -> t.Union[str, dict, t.List[str]]:
        """
        全频道禁言, 秒数/时间戳二选一
        :param guild_id: 频道ID
        :param mute_seconds: 禁言秒数
        :param mute_end_timestamp: 禁言截止时间戳
        :param user_ids: 批量禁言的用户ID列表, 若此项为None, 则全员禁言
        :return: 若成功, 返回空字符串(全员禁言) 或 被禁言的用户id列表(批量禁言); 失败则返回错误信息
        """
        url = f"{self.base_api}/guilds/{guild_id}/mute"
        _body = {"mute_end_timestamp": f"{mute_end_timestamp}"} if mute_end_timestamp != "" else \
            {"mute_seconds": f"{mute_seconds}"}
        if user_ids is None:
            response = requests.request("PATCH", url, data=json.dumps(_body), headers=self.__headers)
            if response.status_code != 204:
                data = response.text
                self._tlogger(f"禁言频道失败: {data}", error=True, error_resp=data,
                              traceid=response.headers.get("X-Tps-trace-ID"))
                return data
            else:
                return ""
        else:
            _body["user_ids"] = user_ids
            response = requests.request("PATCH", url, data=json.dumps(_body), headers=self.__headers)
            if response.status_code != 200:
                self._tlogger(f"批量禁言失败: {response.text}", error=True, error_resp=response.text,
                              traceid=response.headers.get("X-Tps-trace-ID"))
                return response.text
            else:
                udata = json.loads(response.text)
                return udata["user_ids"] if f"{user_ids}" in udata else udata

    def api_mute_member(self, guild_id, member_id, mute_seconds="", mute_end_timestamp="") -> str:
        """
        指定用户禁言, 秒数/时间戳二选一
        :param guild_id: 频道ID
        :param member_id: 用户ID
        :param mute_seconds: 禁言秒数
        :param mute_end_timestamp: 禁言截止时间戳
        :return: 若成功, 返回空字符串; 失败则返回错误信息
        """
        url = f"{self.base_api}/guilds/{guild_id}/members/{member_id}/mute"
        _body = {"mute_end_timestamp": f"{mute_end_timestamp}"} if mute_end_timestamp != "" else \
            {"mute_seconds": f"{mute_seconds}"}
        response = requests.request("PATCH", url, data=json.dumps(_body), headers=self.__headers)
        if response.status_code != 204:
            data = response.text
            self._tlogger(f"禁言成员失败: {data}", error=True, error_resp=data,
                          traceid=response.headers.get("X-Tps-trace-ID"))
            return data
        else:
            return ""

    def api_guild_roles_list_get(self, guild_id, retstr=False) -> t.Union[str, structs.RetModel.GetGuildRole]:
        """
        获取频道身份组列表
        :param guild_id: 频道ID
        :param retstr: 强制返回纯文本
        :return: 频道身份组信息
        """
        url = f"{self.base_api}/guilds/{guild_id}/roles"
        response = requests.request("GET", url, headers=self.__headers)
        return self._retter(response, "获取频道身份组列表失败", structs.RetModel.GetGuildRole, retstr, data_type=0)

    def api_guild_role_create(self, guild_id, name="", color=-1, hoist=1, retstr=False) \
            -> t.Union[str, structs.RetModel.CreateGuildRole]:
        """
        创建频道身份组
        :param guild_id: 频道ID
        :param name: 名称
        :param color: ARGB的HEX十六进制颜色值转换后的十进制数值
        :param hoist: 在成员列表中单独展示: 0-否, 1-是
        :param retstr: 强制返回纯文本
        """
        url = f"{self.base_api}/guilds/{guild_id}/roles"
        body = models.role_body(name, color, hoist)
        response = requests.request("POST", url, data=json.dumps(body), headers=self.__headers)
        return self._retter(response, "创建频道身份组失败", structs.RetModel.CreateGuildRole, retstr, data_type=0)

    def api_guild_role_change(self, guild_id, role_id, name="", color=-1, hoist=1, retstr=False) \
            -> t.Union[str, structs.RetModel.ChangeGuildRole]:
        """
        修改频道身份组
        :param guild_id: 频道ID
        :param role_id: 身份组ID
        :param name: 名称
        :param color: ARGB的HEX十六进制颜色值转换后的十进制数值
        :param hoist: 在成员列表中单独展示: 0-否, 1-是
        :param retstr: 强制返回纯文本
        """
        url = f"{self.base_api}/guilds/{guild_id}/roles/{role_id}"
        body = models.role_body(name, color, hoist)
        response = requests.request("PATCH", url, data=json.dumps(body), headers=self.__headers)
        return self._retter(response, "修改频道身份组失败", structs.RetModel.ChangeGuildRole, retstr, data_type=0)

    def api_guild_role_remove(self, guild_id, role_id):
        """
        删除频道身份组
        :param guild_id: 频道ID
        :param role_id: 身份组ID
        :return: 成功返回空字符串, 失败返回报错
        """
        url = f"{self.base_api}/guilds/{guild_id}/roles/{role_id}"
        response = requests.request("DELETE", url, headers=self.__headers)
        if response.status_code != 204:
            self._tlogger(f"删除频道身份组失败: {response.text}", error=True, error_resp=response.text,
                          traceid=response.headers.get("X-Tps-trace-ID"))
            return response.text
        else:
            return ""

    def api_guild_role_member_add(self, guild_id, role_id, user_id, channel_id=""):
        """
        增加频道身份组成员
        :param guild_id: 频道ID
        :param role_id: 身份组ID
        :param user_id: 用户ID
        :param channel_id: 如果要增加的身份组ID是 5-子频道管理员, 则需要填写channel_id指定频道
        :return: 成功返回空字符串, 失败返回报错
        """
        return self._request_guild_role_member(guild_id, role_id, user_id, channel_id, "PUT")

    def api_guild_role_member_remove(self, guild_id, role_id, user_id, channel_id=""):
        """
        移除频道身份组成员
        :param guild_id: 频道ID
        :param role_id: 身份组ID
        :param user_id: 用户ID
        :param channel_id: 如果要增加的身份组ID是 5-子频道管理员, 则需要填写channel_id指定频道
        :return: 成功返回空字符串, 失败返回报错
        """
        return self._request_guild_role_member(guild_id, role_id, user_id, channel_id, "DELETE")

    def api_announces_create(self, guild_id, message_id=None, channel_id=None, announces_type=None,
                             recommend_channels=None, retstr=False) \
            -> t.Union[str, structs.Announces]:
        """
        创建频道公告
        :param guild_id: 频道ID
        :param message_id: 选填，消息 id，message_id 有值则优选将某条消息设置为成员公告
        :param channel_id: 选填，子频道 id，message_id 有值则为必填。
        :param announces_type: 选填，公告类别 0:成员公告，1:欢迎公告，默认为成员公告
        :param recommend_channels: 选填，推荐子频道列表，会一次全部替换推荐子频道列表, 填写格式: [[子频道id, 推荐语], [子频道id, 推荐语], ...]
        :param retstr: 强制返回纯文本
        :return: Announces
        """
        url = f"{self.base_api}/guilds/{guild_id}/announces"
        body = {}
        if message_id is not None:
            body["message_id"] = message_id
        if channel_id is not None:
            body["channel_id"] = channel_id
        if announces_type is not None:
            body["announces_type"] = announces_type
        if recommend_channels is not None:
            tl = []
            for channel_id, introduce in recommend_channels:
                tl.append({"channel_id": channel_id, "introduce": introduce})
            body[recommend_channels] = tl

        response = requests.request("POST", url, data=json.dumps(body), headers=self.__headers)
        return self._retter(response, "创建频道公告失败", structs.Announces, retstr, data_type=0)

    def api_announces_global_remove(self, guild_id, message_id="all"):
        """
        删除频道公告
        :param guild_id: 频道ID
        :param message_id: 消息ID. message_id 有值时，会校验 message_id 合法性，若不校验 message_id，请将 message_id 设置为 all
        :return: 成功返回空字符串, 失败返回错误信息
        """
        url = f"{self.base_api}/guilds/{guild_id}/announces/{message_id}"
        response = requests.request("DELETE", url, headers=self.__headers)
        if response.status_code != 204:
            self._tlogger(f"删除频道公告失败: {response.text}", error_resp=response.text,
                          traceid=response.headers.get("X-Tps-trace-ID"))
            return response.text
        else:
            return ""

    def api_permissions_get_channel(self, channel_id, user_id, retstr=False) \
            -> t.Union[str, structs.ChannelPermissions]:
        """
        获取指定子频道的权限
        :param channel_id: 子频道ID
        :param user_id: 用户ID
        :param retstr: 强制返回纯文本
        :return: ChannelPermissions, role_id必为None
        """
        url = f"{self.base_api}/channels/{channel_id}/members/{user_id}/permissions"
        response = requests.request("GET", url, headers=self.__headers)
        return self._retter(response, "获取指定子频道的权限失败", structs.ChannelPermissions, retstr, data_type=0)

    def api_permissions_change_channel(self, channel_id, user_id, add: str, remove: str, **kwargs):
        """
        修改指定子频道的权限, 详见: https://bot.q.qq.com/wiki/develop/api/openapi/channel_permissions/put_channel_permissions.html
        :param channel_id: 子频道ID
        :param user_id: 用户ID
        :param add: 字符串形式的位图表示赋予用户的权限
        :param remove: 字符串形式的位图表示赋予用户的权限
        :return: 成功返回空字符串, 失败返回错误信息
        """
        if "setrole" in kwargs:
            url = f"{self.base_api}/channels/{channel_id}/members/{user_id}/permissions"
            ft = "修改指定子频道身份组的权限失败"
        else:
            url = f"{self.base_api}/channels/{channel_id}/roles/{user_id}/permissions"
            ft = "修改指定子频道的权限失败"
        body = {"add": add, "remove": remove}
        response = requests.request("PUT", url, data=json.dumps(body), headers=self.__headers)
        if response.status_code != 204:
            self._tlogger(f"{ft}: {response.text}", error_resp=response.text,
                          traceid=response.headers.get("X-Tps-trace-ID"))
            return response.text
        else:
            return ""

    def api_permissions_get_channel_group(self, channel_id, role_id, retstr=False) \
            -> t.Union[str, structs.ChannelPermissions]:
        """
        获取指定子频道身份组的权限
        :param channel_id: 子频道ID
        :param role_id: 身份组ID
        :param retstr: 强制返回纯文本
        :return: ChannelPermissions, user_id必为None
        """
        url = f"{self.base_api}/channels/{channel_id}/roles/{role_id}/permissions"
        response = requests.request("GET", url, headers=self.__headers)
        return self._retter(response, "获取指定子频道身份组的权限失败", structs.ChannelPermissions, retstr, data_type=0)

    def api_permissions_change_channel_group(self, channel_id, role_id, add: str, remove: str):
        """
        修改指定子频道身份组的权限, 详见: https://bot.q.qq.com/wiki/develop/api/openapi/channel_permissions/put_channel_permissions.html
        :param channel_id: 子频道ID
        :param role_id: 用户ID
        :param add: 字符串形式的位图表示赋予用户的权限
        :param remove: 字符串形式的位图表示赋予用户的权限
        :return: 成功返回空字符串, 失败返回错误信息
        """
        return self.api_permissions_change_channel(channel_id, role_id, add, remove, setrole=1)

    def api_audio_control(self, channel_id, audio_url: str, status: int, text=""):
        """
        音频控制
        :param channel_id: 子频道ID
        :param audio_url: 音频url
        :param status: 播放状态, 见: structs.AudioControlSTATUS
        :param text: 状态文本(比如: 简单爱-周杰伦)，可选，status为0时传，其他操作不传
        :return: 成功返回"{}"
        """
        url = f"{self.base_api}/channels/{channel_id}/audio"
        body = models.audio_control(audio_url, status, text)
        response = requests.request("POST", url, data=json.dumps(body), headers=self.__headers)
        if response.text != "{}":
            self._tlogger(f"音频控制失败: {response.text}", error_resp=response.text,
                          traceid=response.headers.get("X-Tps-trace-ID"))
        return response.text

    def api_get_self_guilds(self, before="", after="", limit="100", use_cache=False, retstr=False) \
            -> t.Union[str, t.List[structs.Guild], None]:
        """
        获取Bot加入的频道列表
        :param before: 读此id之前的数据(before/after 只能二选一)
        :param after: 读此id之后的数据(before/after 只能二选一)
        :param limit: 每次拉取条数
        :param use_cache: 使用缓存
        :param retstr: 强制返回纯文本
        """
        return self.get_self_guilds(before=before, after=after, limit=limit, use_cache=use_cache, retstr=retstr)

    def api_get_self_info(self, use_cache=False):
        """
        获取Bot自身信息
        """
        return self.get_self_info(use_cache=use_cache)

    def api_get_message(self, channel_id, message_id, retstr=False) -> t.Union[str, structs.Message, None]:
        """
        获取指定消息
        :param channel_id: 子频道id
        :param message_id: 消息id
        :param retstr: 强制返回纯文本
        """
        return self.get_message(channel_id=channel_id, message_id=message_id, retstr=retstr)

    def api_get_guild_channel_list(self, guild_id, retstr=False) -> t.Union[str, t.List[structs.Channel], None]:
        """
        获取频道内子频道列表
        :param guild_id: 频道id
        :param retstr: 强制返回纯文本
        """
        return self.get_guild_channel_list(guild_id=guild_id, retstr=retstr)

    def api_get_channel_info(self, channel_id, retstr=False) -> t.Union[str, structs.Channel, None]:
        """
        获取子频道信息
        :param channel_id: 频道id
        :param retstr: 强制返回纯文本
        """
        return self.get_channel_info(channel_id=channel_id, retstr=retstr)

    def api_get_guild_user_info(self, guild_id, member_id, retstr=False) -> t.Union[str, structs.Member, None]:
        """
        获取频道用户信息
        :param guild_id: 频道id
        :param member_id: 用户id
        :param retstr: 强制返回纯文本
        """
        return self.get_guild_user_info(guild_id=guild_id, member_id=member_id, retstr=retstr)

    def api_get_guild_info(self, guild_id, retstr=False) -> t.Union[str, structs.Guild, None]:
        """
        获取频道信息
        :param guild_id: 频道id
        :param retstr: 强制返回纯文本
        """
        return self.get_guild_info(guild_id=guild_id, retstr=retstr)

    def api_get_schedule_list(self, channel_id, retstr=False) -> t.Union[str, t.List[structs.Schedule], None]:
        """
        获取子频道日程列表
        :param channel_id: 子频道ID
        :param retstr: 强制返回纯文本
        :return: 日程列表(若为空, 则返回 None)
        """
        url = f"{self.base_api}/channels/{channel_id}/schedules"
        response = requests.request("GET", url, headers=self.__headers)
        return self._retter(response, "获取日程列表失败", structs.Schedule, retstr, data_type=1)

    def api_get_schedule(self, channel_id, schedule_id, retstr=False) -> t.Union[str, structs.Schedule, None]:
        """
        获取单个日程信息
        :param channel_id: 子频道ID
        :param schedule_id: 日程ID
        :param retstr: 强制返回纯文本
        :return: 单个日程信息(若为空, 则返回 None)
        """
        url = f"{self.base_api}/channels/{channel_id}/schedules/{schedule_id}"
        response = requests.request("GET", url, headers=self.__headers)
        return self._retter(response, "获取日程信息失败", structs.Schedule, retstr, data_type=0)

    def api_schedule_create(self, channel_id, name: str, description: str, start_timestamp: str, end_timestamp: str,
                            jump_channel_id: str, remind_type: str, retstr=False) -> t.Union[str, structs.Schedule,
                                                                                             None]:
        """
        创建日程
        :param channel_id: 子频道ID
        :param name: 日程标题
        :param description: 日程描述
        :param start_timestamp: 开始时间, 13位时间戳
        :param end_timestamp: 结束时间, 13位时间戳
        :param jump_channel_id: 日程跳转频道ID
        :param remind_type: 日程提醒类型, 见: https://bot.q.qq.com/wiki/develop/api/openapi/schedule/model.html#remindtype
        :param retstr: 强制返回纯文本
        :return: 新创建的日程
        """
        url = f"{self.base_api}/channels/{channel_id}/schedules"
        payload = json.dumps(models.schedule_json(name, description, start_timestamp, end_timestamp,
                                                  jump_channel_id, remind_type))
        response = requests.request("POST", url, headers=self.__headers, data=payload)
        return self._retter(response, "创建日程失败", structs.Schedule, retstr, data_type=0)

    def api_schedule_change(self, channel_id, schedule_id, name: str, description: str, start_timestamp: str,
                            end_timestamp: str, jump_channel_id: str, remind_type: str, retstr=False) \
            -> t.Union[str, structs.Schedule, None]:
        """
        修改日程
        :param channel_id: 子频道ID
        :param schedule_id: 日程ID
        :param name: 日程标题
        :param description: 日程描述
        :param start_timestamp: 开始时间, 13位时间戳
        :param end_timestamp: 结束时间, 13位时间戳
        :param jump_channel_id: 日程跳转频道ID
        :param remind_type: 日程提醒类型, 见: https://bot.q.qq.com/wiki/develop/api/openapi/schedule/model.html#remindtype
        :param retstr: 强制返回纯文本
        :return: 修改后的日程
        """
        url = f"{self.base_api}/channels/{channel_id}/schedules/{schedule_id}"
        payload = json.dumps(models.schedule_json(name, description, start_timestamp, end_timestamp,
                                                  jump_channel_id, remind_type))
        response = requests.request("PATCH", url, headers=self.__headers, data=payload)
        return self._retter(response, "修改日程失败", structs.Schedule, retstr, data_type=0)

    def api_schedule_delete(self, channel_id, schedule_id):
        """
        删除日程
        :param channel_id: 子频道ID
        :param schedule_id: 日程ID
        :return: 成功返回空字符串, 失败返回错误信息
        """
        url = f"{self.base_api}/channels/{channel_id}/schedules/{schedule_id}"
        response = requests.request("DELETE", url, headers=self.__headers)
        if response.status_code != 204:
            data = response.text
            self._tlogger(f"日程删除失败: {data}", error_resp=response.text,
                          traceid=response.headers.get("X-Tps-trace-ID"))
            return data
        else:
            return ""

    def api_message_recall(self, channel_id, message_id, hidetip=False):
        """
        撤回消息
        :param channel_id: 频道ID
        :param message_id: 消息ID
        :param hidetip: 隐藏提示小灰条
        :return: 成功返回空字符串, 失败返回错误信息
        """
        url = f"{self.base_api}/channels/{channel_id}/messages/{message_id}"
        payload = {
            'hidetip': str(hidetip).lower()
        }
        response = requests.request("DELETE", url, headers=self.__headers, params=payload)
        if response.status_code != 200:
            data = response.text
            self._tlogger(f"撤回消息失败: {data}", error_resp=response.text,
                          traceid=response.headers.get("X-Tps-trace-ID"))
            return data
        else:
            return ""

    def api_get_api_permission(self, guild_id, retstr=False) -> t.Union[structs.APIPermission, str]:
        """
        获取频道可用权限列表
        :param guild_id: 频道ID
        :param retstr: 强制返回文本
        :return: 频道权限列表
        """
        url = f"{self.base_api}/guilds/{guild_id}/api_permission"
        response = requests.request("GET", url, headers=self.__headers)
        return self._retter(response, "获取频道可用权限列表失败", structs.APIPermission, retstr, data_type=1)

    def api_demand_api_permission(self, guild_id, channel_id: str, path: str, method: str, desc: str, retstr=False) \
            -> t.Union[structs.APIPermissionDemand, str]:
        """
        创建频道 API 接口权限授权链接
        :param guild_id: 频道ID
        :param channel_id: 子频道ID
        :param path: API 接口名，例如 /guilds/{guild_id}/members/{user_id}
        :param method: 请求方法，例如 GET
        :param desc: 机器人申请对应的 API 接口权限后可以使用功能的描述
        :param retstr: 强制返回文本
        :return: 接口权限需求对象
        """
        url = f"{self.base_api}/guilds/{guild_id}/api_permission/demand"
        payload = {
            "channel_id": channel_id,
            "api_identify": {
                "path": path,
                "method": method
            },
            "desc": desc
        }
        response = requests.request("POST", url, headers=self.__headers, data=json.dumps(payload))
        return self._retter(response, "创建授权链接失败", structs.APIPermissionDemand, retstr, data_type=0)

    def api_add_pins(self, channel_id, message_id, retstr=False) -> t.Union[structs.PinsMessage, str]:
        """
        添加精华消息
        :param channel_id: 子频道ID
        :param message_id: 消息ID
        :param retstr: 强制返回str
        :return:
        """
        url = f"{self.base_api}/channels/{channel_id}/pins/{message_id}"
        response = requests.request("PUT", url, headers=self.__headers)
        return self._retter(response, "添加精华消息失败", structs.PinsMessage, retstr, data_type=0)

    def api_remove_pins(self, channel_id, message_id):
        """
        移除精华消息
        :param channel_id: 子频道ID
        :param message_id: 消息ID, 删除全部填入: all
        :return:
        """
        url = f"{self.base_api}/channels/{channel_id}/pins/{message_id}"
        response = requests.request("DELETE", url, headers=self.__headers)
        if response.status_code != 204:
            self._tlogger(f"移除精华消息失败: {response.text}", error=True, error_resp=response.text,
                          traceid=response.headers.get("X-Tps-trace-ID"))
            return response.text
        else:
            return ""

    def api_get_pins(self, channel_id, retstr=False) -> t.Union[structs.PinsMessage, str]:
        """
        获取精华消息
        :param channel_id: 子频道ID
        :param retstr: 强制返回str
        :return:
        """
        url = f"{self.base_api}/channels/{channel_id}/pins"
        response = requests.request("GET", url, headers=self.__headers)
        return self._retter(response, "获取精华消息失败", structs.PinsMessage, retstr, data_type=0)

    def api_send_message_reactions(self, channel_id, message_id, emoji_type, emoji_id):
        """
        发表表情表态
        :param channel_id: 子频道ID
        :param message_id: 消息ID
        :param emoji_type: 表情类型, 参考: https://bot.q.qq.com/wiki/develop/api/openapi/emoji/model.html#emojitype
        :param emoji_id: 表情列表, 参考: https://bot.q.qq.com/wiki/develop/api/openapi/emoji/model.html#Emoji%20%E5%88%97%E8%A1%A8
        :return: 成功返回空字符串
        """
        url = f"{self.base_api}/channels/{channel_id}/messages/{message_id}/reactions/{emoji_type}/{emoji_id}"
        response = requests.request("PUT", url, headers=self.__headers)
        if response.status_code != 204:
            self._tlogger(f"发送表情表态失败: {response.text}", error=True, error_resp=response.text,
                          traceid=response.headers.get("X-Tps-trace-ID"))
            return response.text
        else:
            return ""

    def api_pv_get_member_list(self, guild_id, retstr=False) -> t.Union[str, t.List[structs.Member], None]:
        """
        仅私域机器人可用 - 取频道成员列表
        :param guild_id: 频道ID
        :param retstr: 强制返回字符串
        :return: 成功返回成员列表, 失败返回错误信息
        """
        url = f"{self.base_api}/guilds/{guild_id}/members"
        response = requests.request("GET", url, headers=self.__headers)
        return self._retter(response, "获取频道成员列表失败", structs.Member, retstr, data_type=1)

    def api_pv_kick_member(self, guild_id, user_id, add_blick_list=False, delete_history_msg_days=0) -> str:
        """
        仅私域机器人可用 - 踢出指定成员
        消息撤回时间范围仅支持固定的天数：3，7，15，30。 特殊的时间范围：-1: 撤回全部消息。默认值为0不撤回任何消息。
        :param guild_id: 频道ID
        :param user_id: 成员ID
        :param add_blick_list: 将该成员加入黑名单
        :param delete_history_msg_days: 撤回该成员的消息
        :return: 成功返回空字符串, 失败返回错误信息
        """
        url = f"{self.base_api}/guilds/{guild_id}/members/{user_id}"
        payload = {
            "add_blacklist": add_blick_list,
            "delete_history_msg_days": f"{delete_history_msg_days}"
        }
        response = requests.request("DELETE", url, headers=self.__headers, data=json.dumps(payload))
        if response.status_code != 204:
            self._tlogger(f"移除成员失败: {response.text}", error=True, error_resp=response.text,
                          traceid=response.headers.get("X-Tps-trace-ID"))
            return response.text
        else:
            return ""

    def api_pv_create_channel(self, guild_id, channel_name: str, channel_type: int,
                              channel_position: int, channel_parent_id: int, retstr=False) \
            -> t.Union[str, structs.Channel, None]:
        """
        仅私域机器人可用 - 创建子频道
        :param guild_id: 频道ID
        :param channel_name: 子频道名称
        :param channel_type: 子频道类型
        :param channel_position: 子频道排序
        :param channel_parent_id: 子频道分组ID
        :param retstr: 强制返回纯文本
        :return: 成功返回子频道信息, 失败返回错误信息
        """
        url = f"{self.base_api}/guilds/{guild_id}/channels"
        body_s = {
            "name": channel_name,
            "type": channel_type,
            "position": channel_position,
            "parent_id": channel_parent_id
        }
        response = requests.request("POST", url, data=json.dumps(body_s), headers=self.__headers)
        return self._retter(response, "创建子频道失败", structs.Channel, retstr, data_type=0)

    def api_pv_change_channel(self, channel_id, channel_name: str, channel_type: int,
                              channel_position: int, channel_parent_id: int, retstr=False) \
            -> t.Union[str, structs.Channel, None]:
        """
        仅私域机器人可用 - 修改子频道信息
        :param channel_id: 子频道ID
        :param channel_name: 子频道名称
        :param channel_type: 子频道类型
        :param channel_position: 子频道排序
        :param channel_parent_id: 子频道分组ID
        :param retstr: 强制返回纯文本
        :return: 成功返回修改后的子频道信息, 失败返回错误信息
        """
        url = f"{self.base_api}/channels/{channel_id}"
        body_s = {
            "name": channel_name,
            "type": channel_type,
            "position": channel_position,
            "parent_id": channel_parent_id
        }
        response = requests.request("PATCH", url, data=json.dumps(body_s), headers=self.__headers)
        return self._retter(response, "修改子频道失败", structs.Channel, retstr, data_type=0)

    def api_pv_delete_channel(self, channel_id):
        """
        仅私域机器人可用 - 删除子频道
        :param channel_id: 子频道ID
        :return: 成功返回空字符串, 失败返回错误信息
        """
        url = f"{self.base_api}/channels/{channel_id}"
        response = requests.request("DELETE", url, headers=self.__headers)
        if response.status_code != 200 and response.status_code != 204:
            self._tlogger(f"删除子频道失败: {response.text}", error_resp=response.text,
                          traceid=response.headers.get("X-Tps-trace-ID"))
            return response.text
        else:
            return ""

    def get_guild_info(self, guild_id, retstr=False) -> t.Union[str, structs.Guild, None]:
        url = f"{self.base_api}/guilds/{guild_id}"
        response = requests.request("GET", url, headers=self.__headers)
        return self._retter(response, "获取频道信息失败", structs.Guild, retstr, data_type=0)

    def get_guild_user_info(self, guild_id, member_id, retstr=False) -> t.Union[str, structs.Member, None]:
        url = f"{self.base_api}/guilds/{guild_id}/members/{member_id}"
        response = requests.request("GET", url, headers=self.__headers)
        return self._retter(response, "获取成员信息失败", structs.Member, retstr, data_type=0)

    def get_channel_info(self, channel_id, retstr=False) -> t.Union[str, structs.Channel, None]:
        url = f"{self.base_api}/channels/{channel_id}"
        response = requests.request("GET", url, headers=self.__headers)
        return self._retter(response, "获取子频道信息失败", structs.Channel, retstr, data_type=0)

    def get_guild_channel_list(self, guild_id, retstr=False) -> t.Union[str, t.List[structs.Channel], None]:
        url = f"{self.base_api}/guilds/{guild_id}/channels"
        response = requests.request("GET", url, headers=self.__headers)
        return self._retter(response, "获取子频道列表失败", structs.Channel, retstr, data_type=1)

    def get_message(self, channel_id, message_id, retstr=False) -> t.Union[str, structs.Message, None]:
        url = f"{self.base_api}/channels/{channel_id}/messages/{message_id}"
        response = requests.request("GET", url, headers=self.__headers)
        return self._retter(response, "获取消息信息失败", structs.Message, retstr, data_type=0)

    def get_self_info(self, use_cache=False) -> t.Union[str, structs.User, None]:
        if use_cache and "self_info" in self._cache:
            get_response = self._cache["self_info"]
        else:
            url = f"{self.base_api}/users/@me"
            response = requests.request("GET", url, headers=self.__headers)
            get_response = response.text
            self._cache["self_info"] = response.text

        data = json.loads(get_response)
        if "code" in data:
            self._tlogger(f"获取自身信息失败: {get_response}", error=True, error_resp=get_response)
            return None
        elif self.api_return_pydantic:
            data["bot"] = True
            return structs.User(**data)
        else:
            return get_response

    def get_self_guilds(self, before="", after="", limit="100", use_cache=False, retstr=False) \
            -> t.Union[str, t.List[structs.Guild], None]:
        if use_cache and "get_self_guilds" in self._cache:
            get_response = self._cache["get_self_guilds"]
            x_trace_id = None
        else:
            if after != "":
                url = f"{self.base_api}/users/@me/guilds?after={after}&limit={limit}"
            elif before != "":
                url = f"{self.base_api}/users/@me/guilds?before={before}&limit={limit}"
            else:
                url = f"{self.base_api}/users/@me/guilds?limit={limit}"
            response = requests.request("GET", url, headers=self.__headers)
            get_response = response.text
            x_trace_id = response.headers.get("X-Tps-trace-ID")
            self._cache["get_self_guilds"] = response.text

        data = json.loads(get_response)
        if "code" in data:
            self._tlogger(f"获取频道列表失败: {get_response}", error=True, error_resp=get_response, traceid=x_trace_id)
            if retstr:
                return get_response
            return None
        elif self.api_return_pydantic and not retstr:
            return [structs.Guild(**g) for g in data]
        else:
            return get_response

    def api_get_guild_message_freq(self, guild_id, retstr=False) -> t.Union[str, None, structs.MessageSetting]:
        """
        获取频道消息频率设置
        :param guild_id: 频道ID
        :param retstr: 强制返回文本
        :return: MessageSetting
        """
        url = f"{self.base_api}/guilds/{guild_id}/message/setting"
        response = requests.request("GET", url, headers=self.__headers)
        return self._retter(response, "获取频道消息频率设置失败", structs.MessageSetting, retstr, data_type=0)

    def api_send_message_guide(self, channel_id, content: str):
        """
        发送消息设置引导
        :param channel_id: 子频道ID
        :param content: 内容
        :return:
        """
        url = f"{self.base_api}/channels/{channel_id}/settingguide"
        data = {"content": content}
        response = requests.request("POST", url, data=json.dumps(data), headers=self.__headers)
        if not str(response.status_code).startswith("2"):
            self._tlogger(f"发送消息设置引导失败: {response.text}", error=True, error_resp=response.text,
                          traceid=response.headers.get("X-Tps-trace-ID"))
        else:
            return ""

    def _request_guild_role_member(self, guild_id, role_id, user_id, channel_id="", request_function="PUT"):
        url = f"{self.base_api}/guilds/{guild_id}/members/{user_id}/roles/{role_id}"
        body = {"channel": {"id": channel_id}} if channel_id != "" else None
        response = requests.request(request_function, url, data=None if body is None else json.dumps(body),
                                    headers=self.__headers)
        if response.status_code != 204:
            self._tlogger(f"{'增加' if request_function == 'PUT' else '删除'}频道身份组成员失败: {response.text}", error=True,
                          error_resp=response.text, traceid=response.headers.get("X-Tps-trace-ID"))
            return response.text
        else:
            return ""

    # TODO 更多API
