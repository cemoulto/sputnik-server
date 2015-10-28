import os
import threading
import time
import re

from boto.s3.connection import S3Connection


class PackageIndex(threading.Thread):
    def __init__(self, *args, **kwargs):
        threading.Thread.__init__(self, target=self.run, args=args)
        self.daemon = True

        self.access_key_id = kwargs.pop('access_key_id',
            os.environ.get('AWS_ACCESS_KEY_ID'))
        self.secret_access_key = kwargs.pop('secret_access_key',
            os.environ.get('AWS_SECRET_ACCESS_KEY'))
        self.host = kwargs.pop('host')
        self.bucket = kwargs.pop('bucket')
        self.interval = kwargs.pop('interval', 600)  # 600sec = 10min

        self.packages = {}

        self.start()

    @classmethod
    def parse_package_name(cls, value):
        name, version = value.rsplit('-', 1)
        version_match = re.match(r'(\d+)\.(\d+)\.(\d+)', version)
        name_match = re.match(r'[a-z_-]+', name)
        if name_match and version_match:
            return name, version_match.groups()

    def list(self):
        os.environ['S3_USE_SIGV4'] = 'True'
        conn = S3Connection(self.access_key_id,
                            self.secret_access_key,
                            host=self.host)

        bucket = conn.get_bucket(self.bucket, validate=False)

        for item in bucket.list():
            if item.name.endswith('/meta.json'):

                dirname = os.path.basename(os.path.dirname(item.name))
                if self.__class__.parse_package_name(dirname):
                    yield (dirname, '/index/%s' % item.name)

    def run(self):
        while True:
            packages = {}
            for name, uri in self.list():
                packages[name] = uri

            # atomic update
            self.packages = packages

            time.sleep(self.interval)
