import yaml


class yaml_util:
    @staticmethod
    def read(yaml_path):
        """
        读取指定目录的yaml文件
        :param yaml_path 相对当前的yaml文件绝对路径
        :return: yaml 中的内容
        """
        with open(yaml_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
