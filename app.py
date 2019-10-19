import sys
import json
import socketio

import nest_asyncio
import asyncio

from sanic import Sanic
from os import getenv, listdir, path, getcwd

# from urltask import UrlTask
from constants import *

sio = socketio.AsyncServer(async_mode="sanic", cors_allowed_origins=[])
app = Sanic()
sio.attach(app)

@sio.event
async def event(sid, params):
    loop = asyncio.get_event_loop()

    interface = Interface(sid, params["module"])
    statement = "output = loop.run_until_complete({module}.{name}(interface"
    try:
        if params["data"]:
            statement += ', """{data}"""'
    except:
        pass

    statement = (statement + "))").format(**params,sid=sid)
    exec(statement, globals())

    if isinstance(output, (dict, list)):
        return json.dumps(output)
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
    sys.path.append(modules_dir)
    for module in listdir(modules_dir):
        if path.isdir(path.join(modules_dir, module)):
            print("Loading module", module)
            exec("import " + module)

    # disable uvloop and replace the default
    # event loop with a normal one so we 
    # can nest coroutines
    asyncio.set_event_loop_policy(None)
    loop = asyncio.new_event_loop()
    nest_asyncio.apply(loop)
    asyncio.set_event_loop(loop)

    PORT = getenv("PORT", 8000)
    app.run(host="0.0.0.0", port=PORT)
