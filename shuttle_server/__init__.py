import os
from functools import wraps

from flask import (Flask, session, jsonify, abort, redirect, current_app,
                   request)

from .package_index import PackageIndex
from .index_action import IndexAction
from . import util


class ShuttleServer(Flask):
    def __init__(self, *args, **kwargs):
        self.index = PackageIndex(host='s3.eu-central-1.amazonaws.com',
                                  bucket='spacy-index')
        self.action = IndexAction(region='eu-central-1',
                                  table='index-action')

        super(ShuttleServer, self).__init__(*args, **kwargs)


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


@app.route('/config')
def debug():
    return jsonify({
        'DEBUG': util.hide(os.environ.get('DEBUG')),
        'SECRET_KEY': util.hide(os.environ.get('SECRET_KEY')),
        'AWS_ACCESS_KEY_ID': util.hide(os.environ.get('AWS_ACCESS_KEY_ID')),
        'AWS_SECRET_ACCESS_KEY': util.hide(os.environ.get('AWS_SECRET_ACCESS_KEY')),
    })


@app.route('/index')
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

    url = 'https://%s/%s/%s/%s' % (current_app.index.host,
        current_app.index.bucket, package, filename)
    return redirect(url)
