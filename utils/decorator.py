import re
from functools import wraps
from utils.str_handle import get_context_value_by_key


def resolve_vars(func):
    @wraps(func)
    def wrapper(context, *args, **kwargs):
        def replacer(match):
            return str(get_context_value_by_key(context, match.group(0)))
        
        new_args = [re.sub(r"\$\{(.*?)\}", replacer, str(arg)) if isinstance(arg, str) else arg for arg in args]
        new_kwargs = {k: re.sub(r"\$\{(.*?)\}", replacer, str(v)) if isinstance(v, str) else v for k, v in kwargs.items()}
        return func(context, *new_args, **new_kwargs)

    return wrapper