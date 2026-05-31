# -*- coding: utf-8 -*-
# 状态定义注册表
#data/status 只定义“状态是什么”

STATUS_REGISTRY = {}
STATUS_DEFS = {}

def register_status(status_id):
    def decorator(cls):
        STATUS_REGISTRY[status_id] = cls
        return cls
    return decorator

def register_status_def(status_def):
    key = status_def.key

    if key in STATUS_DEFS:
        raise ValueError("重复注册状态：{}".format(key))

    STATUS_DEFS[key] = status_def
    return status_def


def get_status_def(key):
    return STATUS_DEFS.get(key)


def get_status_name(key):
    status_def = get_status_def(key)

    if status_def is None:
        return key

    return status_def.name


def iter_status_defs():
    return sorted(
        STATUS_DEFS.values(),
        key=lambda status_def: status_def.order
    )


def has_status_def(key):
    return key in STATUS_DEFS