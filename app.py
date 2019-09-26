import sys
import socketio
from sanic import Sanic
from sanic_cors import CORS
from os import getenv, listdir, path, getcwd

sio = socketio.AsyncServer(async_mode='sanic', cors_allowed_origins=[])
app = Sanic()
app.config['CORS_SUPPORTS_CREDENTIALS'] = True
CORS(app)
sio.attach(app)

@sio.event
async def event(sid, data):
    print(data)

@sio.event
async def connect(sid, environ):
    print("connect ", sid)

@sio.event
async def disconnect(sid):
    print("disconnect ", sid)

if __name__ == "__main__":
    modules_dir = path.join(getcwd(), "modules")
    sys.path.append(modules_dir)
    for module in listdir(modules_dir):
        if path.isdir(path.join(modules_dir, module)):
            print("Loading module", module)
            exec("import " + module)

    PORT = getenv("PORT", 8000)
    app.run(host="0.0.0.0", port=PORT)
