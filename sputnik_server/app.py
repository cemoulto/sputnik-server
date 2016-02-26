import os
import json
from datetime import timedelta
from functools import wraps

import newrelic.agent
newrelic.agent.initialize('newrelic.ini',
    os.environ.get('ENVIRONMENT', 'development'))

from flask import (Flask, session, jsonify, abort, redirect, current_app,
                   request)

from .package_index import PackageIndex
from .index_action import IndexAction
from .analytics import Analytics
from . import util


class App(Flask):
    def __init__(self, *args, **kwargs):
        super(App, self).__init__(*args, **kwargs)

        self.permanent_session_lifetime = timedelta(days=365)

        util.set_config(self, 'ENVIRONMENT', 'development')
        util.set_config(self, 'SECRET_KEY', False)
        util.set_config(self, 'DEBUG', True)

        util.set_config(self, 'GOOGLE_TRACKING_ID', False)

        util.set_config(self, 'AWS_ACCESS_KEY_ID')
        util.set_config(self, 'AWS_SECRET_ACCESS_KEY')
        util.set_config(self, 'AWS_REGION', 'eu-central-1')

        if self.config['ENVIRONMENT'] in ['development', 'staging']:
            util.set_config(self, 'S3_BUCKET', 'spacy-index-dev')
            util.set_config(self, 'ACTION_TABLE', 'index-action-dev')

        elif self.config['ENVIRONMENT'] in ['production']:
            util.set_config(self, 'S3_BUCKET', 'spacy-index')
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

        self.analytics = Analytics(tracking_id=self.config['GOOGLE_TRACKING_ID'])


app = newrelic.agent.WSGIApplicationWrapper(App(__name__))


def track_user(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_app.config['SECRET_KEY']:
            return f(*args, **kwargs)

        session.permanent = True
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

        system_string = request.headers.get('X-Sputnik-System')
        if system_string:
            system = json.loads(system_string)
        else:
            system = util.parse_user_agent(request.user_agent.string)

        current_app.analytics.pageview(
            client_id=session['install_id'],
            host=request.host.split(':')[0],
            path=request.path,
            remote_addr=request.access_route[0],
            user_agent=request.user_agent.string,
            **system)

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


@app.route('/upload', methods=['GET'])
def upload():
    return jsonify({
        'bucket': current_app.config['S3_BUCKET'],
        'region': current_app.config['AWS_REGION']
    })


@app.route('/models', methods=['GET'])
@track_user
def models():
    app_name = util.get_system(request).get('app_name')
    return jsonify(current_app.index.packages(app_name))


@app.route('/models/<package>/<filename>', methods=['HEAD', 'GET'])
@track_user
def models_package(package, filename):
    if filename not in ['meta.json', 'package.json', 'archive.gz']:
        abort(404)

    app_name = util.get_system(request).get('app_name')
    if package not in current_app.index.packages(app_name):
        abort(404)

    return redirect(current_app.index.get_url(os.path.join(package, filename)))
