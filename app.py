import sys
import yaml
import klepto
import socketio

from sanic import Sanic
from inspect import isclass
from sanic_cors import CORS
from pypika import Table, Query
from sanic.response import text
from sqlalchemy import create_engine
from os import getenv, listdir, path, getcwd

from response import Response
# from urltask import UrlTask
from constants import *

sio = socketio.AsyncServer(async_mode="sanic", cors_allowed_origins=[])
app = Sanic()
app.config["CORS_SUPPORTS_CREDENTIALS"] = True
CORS(app)
sio.attach(app)

mysql_prefs = {}

@sio.event
async def event(sid, params):
    global mysql_prefs

    output = object()

    statement = "output = {method}.{name}("
    if params["data"]:
        statement += "{data}"
    statement = (statement + ")").format(params)
    exec(statement)

    if (output.response):
        return output.response
    else:
        if output.mode is Response.MODE_TARGET:
            if isinstance(output.data, string):
                free_client_open(output.data)
                return text("ok")
        elif output.mode is Response.MODE_DBGET:
            fetched_dict = {}

            for (key, value) in output.data.items():
                table_name = "_{0}_{1}".format(output.module, key)
                mysql_u = gen_mysql_url(mysql_prefs, table_name)

                fetched_dict[key] = {}

                d = klepto.archives.sqltable_archive(mysql_u)
                d.load()

                engine = create_engine(mysql_u, echo=True)
                conn = engine.connect()

                keys_to_fetch = []
                for item_key in value:
                    if key["is_object"]:
                        fetched_dict[key].update({item_key: d[item_key["name"]]})
                        value.pop(item_key)
                    else:
                        keys_to_fetch.append(item_key["name"])

                table = Table(table_name)
                q = Query._from(table).select(*keys_to_fetch)

                with conn.cursor() as cursor:
                    cursor.execute(q)
                    fetched_dict[key].update(cursor.fetchall())

                del d
                if output.cb:
                    output.cb(fetched_dict)
        elif output.mode is Response.MODE_DBSAVE:
            for (key, value) in output.data.items():
                table_name = "_{0}_{1}".format(output.module, key)
                mysql_u = gen_mysql_url(mysql_prefs, table_name)

                d = klepto.archives.sqltable_archive(mysql_u)
                engine = create_engine(mysql_u, echo=True)
                conn = engine.connect()

                for row in value:
                    for (col, m_val) in row.items():
                        if isclass(m_val):
                            d[col] = m_val
                            del value[col]

                    table = Table(table_name)

                    sql_params = [Param("%s") for i in len(row)]
                    q = Query.into(table).columns(*row.keys()).insert(sql_params)
                    conn.execute(q, row.values())

                d.dump()
                conn.commit()
                del d

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

if __name__ == "__main__":
    modules_dir = path.join(getcwd(), "modules")
    sys.path.append(modules_dir)
    for module in listdir(modules_dir):
        if path.isdir(path.join(modules_dir, module)):
            print("Loading module", module)
            exec("import " + module)

    with open("config.yaml") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
        mysql_prefs = data["mysql"]

    PORT = getenv("PORT", 8000)
    app.run(host="0.0.0.0", port=PORT)
