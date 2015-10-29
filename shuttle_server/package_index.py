import os
import re

from boto.s3.connection import S3Connection

from . import util


class PackageIndex():
    def __init__(self, *args, **kwargs):
        self.access_key_id = kwargs.pop('access_key_id')
        self.secret_access_key = kwargs.pop('secret_access_key')
        self.host = kwargs.pop('host')
        self.bucket_name = kwargs.pop('bucket')
        self.interval = kwargs.pop('interval', 600)  # 600sec = 10min

        self.packages = {}

        os.environ['S3_USE_SIGV4'] = 'True'
        conn = S3Connection(self.access_key_id,
                            self.secret_access_key,
                            host=self.host)
        self.bucket = conn.get_bucket(self.bucket_name, validate=False)
        self.reindex()

    @classmethod
    def parse_package_name(cls, value):
        name, version = value.rsplit('-', 1)
        version_match = re.match(r'(\d+)\.(\d+)\.(\d+)', version)
        name_match = re.match(r'[a-z_-]+', name)
        if name_match and version_match:
            return name, version_match.groups()

    def list(self):
        for item in self.bucket.list():
            etag = util.unquote(item.etag)
            if item.name.endswith('/meta.json'):
                dirname = os.path.basename(os.path.dirname(item.name))
                if self.__class__.parse_package_name(dirname):
                    yield (dirname, '/index/%s' % item.name, etag)

    def reindex(self):
        packages = {}

        for name, uri, etag in self.list():
            packages[name] = (uri, etag)

        # atomic update
        self.packages = packages

    def status(self):
        try:
            self.reindex()
            return True
        except Exception:
            return False
