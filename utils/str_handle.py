import re
from types import SimpleNamespace

list_indexs_complie = re.compile(r"\[(\d+)\]")

def get_context_value_by_key(context, key: str):
    if key in context.scenario.store.keys():
        return context.scenario.store[key]
    elif key in context.feature.store.keys():
        return context.feature.store[key]
    elif key in context.store.keys():
        return context.store[key]
    return key


def resolve_data(context, data):
    def replacer(match):
        return str(get_context_value_by_key(context, match.group(0)))
    
    if isinstance(data, str):
        return re.sub(r"\$\{(.+?)\}", replacer, data)
    elif isinstance(data, dict):
        return {resolve_data(context, k): resolve_data(context, v) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_data(context, item) for item in data]
    return data


def value_handler(value: str, context):
    if value.startswith("$"):
        keys = value.split(".", 1)
        response = context.store.response.get(keys[0].replace("$", ""))
        if keys[-1] in context.store:
            pass
        return get_keys_value(keys[-1], response.json())
    else:
        return value.strip()
    

def customize_get(mode: str, dict_obj: dict):
    if "[" in mode and "]" in mode:
        parts = list_indexs_complie.split(mode)
        key = mode.split("[")[0]
        obj = dict_obj.get(key)
        for part in parts:
            obj = obj[int(part)]
        return obj
    return dict_obj.get(mode, None)


def get_keys_value(keys, dict_obj):
    keys = keys.split(".")
    value = dict_obj
    for key in keys:
        value = customize_get(key, value)
        if value is None:
            raise ValueError(f"Can not get the target value of {keys}")
    return value


def wrap_namespace(data):
    """
    Recursively converts a dictionary into a SimpleNamespace object.
    """
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = wrap_namespace(value)
        return SimpleNamespace(**data)
    elif isinstance(data, list):
        return [wrap_namespace(item) for item in data]
    else:
        return data