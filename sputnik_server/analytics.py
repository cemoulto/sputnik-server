import json
from urllib.parse import urlencode
import http.client

import requests


def print_json(string):
    defaults = dict(indent=4, separators=(',', ': '))
    print(json.dumps(json.loads(string), **defaults))


class Analytics(object):
    def __init__(self, tracking_id, debug=False):
        self.tracking_id = tracking_id
        self.debug = debug

    def pageview(self, client_id, host, path, remote_addr, user_agent):
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

        if self.debug:
            url = 'https://www.google-analytics.com/debug/collect'
        else:
            url = 'https://www.google-analytics.com/collect'

        r = requests.post(url, data=data)
        if self.debug:
            print_json(r.text)
