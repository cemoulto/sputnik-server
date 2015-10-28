import time
import uuid

import boto.dynamodb


class IndexAction(object):
    def __init__(self, region, table):
        self.conn = boto.dynamodb.connect_to_region(region)
        self.table = self.conn.get_table(table)

    def create(self, attrs):
        attrs.update({'created_at': int(time.time())})
        attrs = {k: v for k, v in attrs.items() if v is not None}

        item = self.table.new_item(
            hash_key=uuid.uuid1().hex,
            attrs=attrs)

        item.put()
