import os
import string
import random


def random_string(size, chars=string.ascii_letters + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))


def hide(value):
    return value and '*' * len(value)


def set_config(app, key, value=None, cast=str):
    env_value = os.environ.get(key, value)
    if value is None and env_value is None:
        raise Exception('environment variable missing: %s' % key)

    if isinstance(value, bool) or cast == bool:
        cast = lambda x: x is True or str(x).lower() == 'true' or x

    env_value = cast(env_value)
    app.config[key] = env_value

    if 'secret' in key.lower():
        out_value = hide(env_value)
    else:
        out_value = env_value

    print('%s: %s (%s)' % (key, out_value, env_value.__class__.__name__))


def unquote(s):
    if (s[0] == s[-1]) and s.startswith(("'", '"')):
        return s[1:-1]
    return s


def parse_user_agent(ua):
    if not ua or not ua.lower().startswith('sputnik'):
        return {}

    def flatten(l):
        return [item for sublist in l for item in sublist]

    parts = flatten([ua_parts.split('/', 1) for ua_parts in ua.split(' ')])
    sputnik_version = parts[1]

    app_name = None
    app_version = None
    for i, part in enumerate(parts):
        if part.lower() in ['spacy']:
            app_name = parts.pop(i)
            app_version = parts.pop(i)
            if app_version == 'None':
                app_version = None
            elif app_version[:5].lower() in ['major', 'prere', 'build', 'minor', 'patch']:
                app_version = '0.100.1+'

    os = None
    os_version = None
    for i, part in enumerate(parts):
        if part[:5].lower() in ['linux', 'darwi', 'windo', 'cygwi']:
            os = parts.pop(i)
            os_version = parts.pop(i)

    py = None
    py_version = None
    for i, part in enumerate(parts):
        if part.lower() in ['cpython', 'ironpython', 'jython', 'pypy']:
            py = parts.pop(i)
            py_version = parts.pop(i)

    bits = None
    for i, part in enumerate(parts):
        if part.lower() in ['64bits']:
            bits = 64 if parts.pop(i+1) == 'True' else 32

    return {
        'app_name': app_name,
        'app_version': app_version,
        'sputnik_version': sputnik_version,
        'py': py,
        'py_version': py_version,
        'os': os,
        'os_version': os_version,
        'bits': bits
    }
