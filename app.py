import json
import socketio

from sys import modules, path as syspath
from sanic import Sanic
from os import getenv, listdir, path, getcwd

# from urltask import UrlTask
from constants import *

sio = socketio.AsyncServer(async_mode="sanic", cors_allowed_origins=[])
app = Sanic()
sio.attach(app)

@sio.event
async def event(sid, params):
    output = None

    interface = Interface(sid, params["module"])
    module_method = getattr(modules[params["module"]], params["name"])

    try:
        output = await module_method(interface, params["data"])
    except TypeError:
        output = await module_method(interface)

    return output

connected = []
@sio.event
async def connect(sid, _):
    print("connect ", sid)
    connected.append(sid)

@sio.event
async def disconnect(sid):
    print("disconnect ", sid)
    connected.remove(sid)

verify_toattempt = []
async def send_url_to_free_client(url, sid, clients, data):
    global verify_toattempt

    if int(data["status"]) == STATUS_FREE:
        await sio.emit("open_url", {
            "url": url
        }, room=sid)
    else:
        try:
            verify_toattempt.remove(sid)
            client = choice(verify_toattempt)
            await sio.emit("get_status", room=client,
                           callback=lambda d: send_url_to_free_client(url, client, clients, d))
        except (IndexError, ValueError):
            pass
            # UrlTask(url)

async def free_client_open(url):
    global verify_toattempt

    verify_toattempt = connected
    try:
        client = choice(verify_toattempt)
        await sio.emit("get_status", room=client,
                       callback=lambda d: send_url_to_free_client(url, client, connected, d))
    except IndexError:
        pass
        # UrlTask(url)

class Interface():
    def __init__(self, sid, name):
        self.sid  = sid
        self.name = name

    async def send(self, event, data):
        await sio.emit("event", {
            "event": event,
            "data":  data,
            "me": self.name
        }, room=self.sid)

if __name__ == "__main__":
    modules_dir = path.join(getcwd(), "modules")
    syspath.append(modules_dir)

    for module in listdir(modules_dir):
        if path.isdir(path.join(modules_dir, module)):
            print("Loading module", module)
            __import__(module)

    PORT = getenv("PORT", 8000)
    app.run(host="0.0.0.0", port=PORT)
