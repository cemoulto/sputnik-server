import os

from shuttle_server import app as application


application.debug = os.environ.get('DEBUG') == 'True'
application.secret_key = os.environ.get('SECRET_KEY')


if __name__ == "__main__":
    application.run()
