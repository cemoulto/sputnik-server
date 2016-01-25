import json
from urllib.parse import urlencode
import http.client

import requests


def print_json(string):
    defaults = dict(indent=4, separators=(',', ': '))
    print(json.dumps(json.loads(string), **defaults))


class Analytics(object):

    dimensions = {
        'cd1': 'app_name',
        'cd2': 'app_version',
        'cd3': 'sputnik_version',
        'cd4': 'py',
        'cd5': 'py_version',
        'cd6': 'os',
        'cd7': 'os_version',
        'cd8': 'bits'
    }

    def __init__(self, tracking_id, debug=False):
        self.tracking_id = tracking_id
        self.debug = debug

    def pageview(self, client_id, host, path, remote_addr, user_agent, **kwargs):
        if not self.tracking_id:
            return

        data = {'v': 1,
                't': 'pageview',
                'tid': self.tracking_id,
                'cid': client_id,
                'dh': host,
                'dp': path,
                'uip': remote_addr,
                'ua': user_agent}

        for k, v in self.dimensions.items():
            param = kwargs.get(v)
            if param:
                data[k] = param

        if self.debug:
            url = 'https://www.google-analytics.com/debug/collect'
        else:
            url = 'https://www.google-analytics.com/collect'

        r = requests.post(url, data=data)
        if self.debug:
            print_json(r.text)
