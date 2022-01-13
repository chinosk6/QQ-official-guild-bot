import typing as t
import json


class BotCallingAPIError(Exception):
    def __init__(self, error_response: str, error_message=""):
        try:
            data = json.loads(error_response)
        except json.JSONDecodeError:
            data = {}

        self.error_response = error_response
        self.error_code: t.Optional[int] = data["code"] if "code" in data else None
        self.error_description: str = data["message"] if "message" in data else str(error_response)
        self.error_message = error_message.replace(error_response, "").strip()
        if self.error_message.endswith(":"):
            self.error_message = self.error_message[:-1]

    def __str__(self):
        return self.error_response


class Embed:
    def __init__(self, title: str, fields: t.List[str], image_url: t.Optional[str] = None,
                 prompt: t.Optional[str] = None):
        """
        embed消息
        :param title: 标题
        :param fields: 内容文本
        :param image_url: 缩略图url, 选填
        :param prompt: 消息弹窗内容
        """
        self.title = title
        self.prompt = prompt
        self.image_url = image_url
        self.fields = fields

    def ark_to_json(self):
        fields = []
        for name in self.fields:
            fields.append({"name": name})

        ret = {
            "embed": {
                "title": self.title,
                "fields": fields
            }
        }

        if self.prompt is not None:
            ret["embed"]["prompt"] = self.prompt
        if self.image_url is not None:
            ret["embed"]["thumbnail"] = {}
            ret["embed"]["thumbnail"]["url"] = self.image_url

        return ret


class Ark:
    class LinkWithText:
        def __init__(self, description: str, prompt: str, text_and_link: t.Optional[t.List[t.List[str]]] = None):
            """
            23 链接+文本列表模板
            :param description: 描述
            :param prompt: 提示信息
            :param text_and_link: 正文, 可以混合使用纯文本/链接文本.
            例1, 纯文本: [[文本], [文本], ...]; 例2: 链接文本: [[文本, 链接], [文本, 链接], ...]
            """
            self.description = description
            self.prompt = prompt
            self.text_and_link = text_and_link

        def ark_to_json(self):
            ret = {
                "ark": {
                    "template_id": 23,
                    "kv": [
                        {
                            "key": "#DESC#",
                            "value": self.description
                        },
                        {
                            "key": "#PROMPT#",
                            "value": self.prompt
                        }
                    ]
                }
            }
            if self.text_and_link is not None:
                k_obj = []
                k_ds = ["desc", "link"]
                for obj in self.text_and_link:
                    p_obj = {"obj_kv": []}
                    count = 0
                    for i in obj:
                        p_obj["obj_kv"].append({
                            "key": k_ds[count],
                            "value": i
                        })
                        count += 1
                        if count + 1 > len(obj):
                            break
                    if count != 0:
                        k_obj.append(p_obj)
                obj_list = {
                    "key": "#LIST#",
                    "obj": k_obj
                }
                ret["ark"]["kv"].append(obj_list)
            return ret

    class TextAndThumbnail:
        def __init__(self, desc: str, prompt: str, title: str, metadesc: str, img_url: str, jump: str, subtitle: str):
            """
            24 文本+缩略图模板
            :param desc: 描述
            :param prompt: 提示文本
            :param title: 标题
            :param metadesc: 详细描述
            :param img_url: 图片链接
            :param jump: 跳转链接
            :param subtitle: 子标题(来源)
            """
            self.desc = desc
            self.prompt = prompt
            self.title = title
            self.metadesc = metadesc
            self.img_url = img_url
            self.jump = jump
            self.subtitle = subtitle

        def ark_to_json(self):
            ret = {
                "ark": {
                    "template_id": 24,
                    "kv": [
                        {
                            "key": "#DESC#",
                            "value": self.desc
                        },
                        {
                            "key": "#PROMPT#",
                            "value": self.prompt
                        },
                        {
                            "key": "#TITLE#",
                            "value": self.title
                        },
                        {
                            "key": "#METADESC#",
                            "value": self.metadesc
                        },
                        {
                            "key": "#IMG#",
                            "value": self.img_url
                        },
                        {
                            "key": "#LINK#",
                            "value": self.jump
                        },
                        {
                            "key": "#SUBTITLE#",
                            "value": self.subtitle
                        }
                    ]
                }
            }
            return ret

    class BigImage:
        def __init__(self, prompt: str, title: str, sub_title: str, cover: str, jump: str):
            """
            37 大图模板
            :param prompt: 提示信息
            :param title: 标题
            :param sub_title: 子标题
            :param cover: 大图url, 尺寸: 975*540
            :param jump: 跳转链接
            """
            self.prompt = prompt
            self.title = title
            self.sub_title = sub_title
            self.cover = cover
            self.jump = jump

        def ark_to_json(self):
            ret = {
                "ark": {
                    "template_id": 37,
                    "kv": [
                        {
                            "key": "#PROMPT#",
                            "value": self.prompt
                        },
                        {
                            "key": "#METATITLE#",
                            "value": self.title
                        },
                        {
                            "key": "#METASUBTITLE#",
                            "value": self.sub_title
                        },
                        {
                            "key": "#METACOVER#",
                            "value": self.cover
                        },
                        {
                            "key": "#METAURL#",
                            "value": self.jump
                        }
                    ]
                }
            }
            return ret

def schedule_json(name, description, start_timestamp, end_timestamp, jump_channel_id, remind_type):
    ret = {
            "schedule": {
                "name": name,
                "description": description,
                "start_timestamp": start_timestamp,
                "end_timestamp": end_timestamp,
                "jump_channel_id": jump_channel_id,
                "remind_type": remind_type
            }
        }
    return ret

# a = Ark.Embed("标题", ["内容1", "内容2"], "http", "xxtc").ark_to_json()
# a = Ark.LinkWithText("描述", "提示", [["文本1"], ["文本2", "uurrll"]]).ark_to_json()

def role_body(name="", color=-1, hoist=1):
    body = {"filter": {"name": 1 if name != "" else 0,
                       "color": 1 if color != -1 else 0,
                       "hoist": hoist},
            "info": {"name": name,
                     "color": color,
                     "hoist": hoist}}
    if name == "":
        body["info"].pop("name")
    if color == -1:
        body["info"].pop("color")
    return body

def audio_control(audio_url: str, status: int, text=""):
    ret = {"audio_url": audio_url,
           "text": text,
           "status": status}
    if status != 0 or text == "":
        ret.pop("text")
    return ret
