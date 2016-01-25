import json
from urllib.parse import urlencode
import http.client


def print_json(bytes):
    defaults = dict(indent=4, separators=(',', ': '))
    print(json.dumps(json.loads(bytes.decode('utf8')), **defaults))


class Analytics(object):
    def __init__(self, tracking_id, debug=False):
        self.conn = http.client.HTTPSConnection('www.google-analytics.com')
        self.tracking_id = tracking_id
        self.debug = debug

    def pageview(self, client_id, path, remote_addr, user_agent):
        if not self.tracking_id:
            return

        data = urlencode({'v': 1,
                          't': 'pageview',
                          'tid': self.tracking_id,
                          'cid': client_id,
                          'dp': path,
                          'uip': remote_addr,
                          'ua': user_agent}).encode('ascii')
        
        url = '/collect'
        if self.debug:
            url = '/debug' + url
    
        self.conn.request('POST', url, data)
        response = self.conn.getresponse().read()
    
        if self.debug:
            print_json(response)
