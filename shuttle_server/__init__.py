import os

from flask import Flask, session, jsonify, abort, make_response

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


@app.route('/index')
def index():
    if not 'install_id' in session:
        session['install_id'] = util.random_string()
        print(session['install_id'])

    if not app.index.loaded:
        abort(500)

    resp = make_response(jsonify(app.index.packages))
    resp.headers['Server'] = "Shuttle"
    return resp
