import os
from functools import wraps

from flask import Flask, session, jsonify, abort, make_response, redirect, current_app

from .package_index import PackageIndex
from . import util


class ShuttleServer(Flask):
    def run(self, *args, **kwargs):
        debug = self.debug or kwargs.get('debug')

        self.secret_key = os.environ.get('SECRET_KEY')

        # don't run again when reloading code (debug mode)
        if not debug or os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            self.index = PackageIndex(host='s3.eu-central-1.amazonaws.com',
                                      bucket='spacy-index')

        super(ShuttleServer, self).run(*args, **kwargs)


app = ShuttleServer(__name__)


def track_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'install_id' in session:
            session['install_id'] = util.random_string()
        print(session['install_id'])
        return f(*args, **kwargs)
    return decorated_function


@app.route('/index')
@track_user
def index():
    return jsonify(current_app.index.packages)


@app.route('/index/<package>/<filename>')
@track_user
def index_package(package, filename):
    if filename not in ['meta.json', 'package.json', 'archive.gz']:
        abort(404)

    if not package in current_app.index.packages:
        abort(404)

    url = 'https://%s/%s/%s/%s' % (current_app.index.host,
        current_app.index.bucket, package, filename)
    return redirect(url)
