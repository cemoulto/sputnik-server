import os
from functools import wraps

from flask import (Flask, session, jsonify, abort, redirect, current_app,
                   request)

from .package_index import PackageIndex
from .index_action import IndexAction
from . import util


class ShuttleServer(Flask):
    def __init__(self, *args, **kwargs):
        super(ShuttleServer, self).__init__(*args, **kwargs)

        util.set_config(self, 'DEBUG', False)
        util.set_config(self, 'SECRET_KEY')
        util.set_config(self, 'AWS_ACCESS_KEY_ID')
        util.set_config(self, 'AWS_SECRET_ACCESS_KEY')
        util.set_config(self, 'S3_BUCKET', 'spacy-index')
        util.set_config(self, 'AWS_REGION', 'eu-central-1')
        util.set_config(self, 'ACTION_TABLE', 'index-action')

        self.index = PackageIndex(
            access_key_id=self.config['AWS_ACCESS_KEY_ID'],
            secret_access_key=self.config['AWS_SECRET_ACCESS_KEY'],
            host='s3.%s.amazonaws.com' % self.config['AWS_REGION'],
            bucket=self.config['S3_BUCKET'])

        self.action = IndexAction(
            access_key_id=self.config['AWS_ACCESS_KEY_ID'],
            secret_access_key=self.config['AWS_SECRET_ACCESS_KEY'],
            region=self.config['AWS_REGION'],
            table=self.config['ACTION_TABLE'])


app = ShuttleServer(__name__)


def track_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not 'install_id' in session:
            session['install_id'] = util.random_string(16)

        current_app.action.create({
            'install_id': session['install_id'],
            'method': request.method,
            'path': request.path,
            'user_agent': request.user_agent.string,
            'range': str(request.range),
            'remote_addr': request.access_route[0],  # support x-forwarded-for header
        })

        return f(*args, **kwargs)
    return decorated_function


@app.route('/health')
def health():
    if not current_app.index.status():
        abort(503)  # index service not available
    if not current_app.action.status():
        abort(503)  # action service not available
    return jsonify({
        'status': 'ok'
    })


@app.route('/reindex', methods=['PUT'])
def reindex():
    current_app.index.reindex()
    return jsonify({
        'status': 'ok'
    })


@app.route('/index', methods=['GET'])
@track_user
def index():
    return jsonify(current_app.index.packages)


@app.route('/index/<package>/<filename>', methods=['HEAD', 'GET'])
@track_user
def index_package(package, filename):
    if filename not in ['meta.json', 'package.json', 'archive.gz']:
        abort(404)

    if not package in current_app.index.packages:
        abort(404)

    return redirect(current_app.index.get_url(os.path.join(package, filename)))
