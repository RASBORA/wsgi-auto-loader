#!/usr/bin/python3
import os
import cgi
import configparser
import wsgiref.util
import importlib
from wsgiref import simple_server
from logging import getLogger, StreamHandler

logger = getLogger()
logger.setLevel('INFO')
stream_handler = StreamHandler()
logger.addHandler(stream_handler)

PROGRAM_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = PROGRAM_DIR
EXTS = ['.wsgi', '.py']

# key: url value: WSGI module class
wsgi_modules = {}

config = configparser.ConfigParser()
config.read(os.path.join(PROGRAM_DIR,'config.ini'))

class WsgiModule(object):
    def __init__(self,module, module_name, file_path, timestamp):
        self.module = module
        self.module_name = module_name
        self.file_path = file_path
        self.timestamp = timestamp

def application(environ, start_response):
    path = wsgiref.util.shift_path_info(environ)
    if path == '':
        start_response('200 OK',[('Content-Type','text/html')])
        method = environ.get('REQUEST_METHOD')
        return ['WSGI auto loader'.encode()]
    
    try:
        app = wsgi_modules[path]
    except KeyError:
        start_response('404 Not Found',[('Content-Type','text/html')])
        method = environ.get('REQUEST_METHOD')
        return ['404 Not Found'.encode()]
    
    # 変更が合った場合リロード
    if app.timestamp < os.stat(app.file_path).st_mtime:
        importlib.reload(app.module)
    return app.module.application(environ, start_response)

def wsgi_file_import():
    logger.info('wsgi file import')
    for name in os.listdir(BASE_DIR):
        extsplit = os.path.splitext(name)
        if extsplit[1].lower() not in EXTS:
            continue
        if name == __file__:
            continue

        logger.info('import: ' + name)

        file_path = os.path.join(BASE_DIR, name)
        module_name = 'wal_' + extsplit[0]
        module = importlib.machinery.SourceFileLoader(module_name, file_path).load_module()
        timestamp = os.stat(file_path).st_mtime
        wsgi_modules[name] = WsgiModule(module,module_name,file_path,timestamp)

def init():
    if config['General']['path']:
    BASE_DIR = config['General']['path']

    print(BASE_DIR)

    

init()
if __name__ == '__main__':
    server = simple_server.make_server('', 8005, application)
    server.serve_forever()

