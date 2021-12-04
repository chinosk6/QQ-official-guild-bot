from threading import Thread


def gettext_between(text: str, before: str, after: str, is_include=False) -> str:
    """
    取出中间文本
    :param text: 原文本
    :param before: 前面文本
    :param after: 后面文本
    :param is_include: 是否取出标识文本
    :return: 操作后的文本
    """
    b_index = text.find(before)

    if b_index == -1:
        b_index = 0
    else:
        b_index += len(before)
    af_index = text.find(after, b_index)
    if af_index == -1:
        af_index = len(text)
    rettext = text[b_index: af_index]
    if is_include:
        rettext = before + rettext + after
    return rettext


def on_new_thread(f):
    def task_qwq(*args, **kwargs):
        t = Thread(target=f, args=args, kwargs=kwargs)
        t.start()

    return (task_qwq)
