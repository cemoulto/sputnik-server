import os

from shuttle_server import app as application


application.debug = os.environ.get('DEBUG') == 'True'


if __name__ == "__main__":
    application.run()
