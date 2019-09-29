STATUS_BUSY = 0
STATUS_FREE = 1

MYSQL_BASE = "mysql://{user}:{pass}@{host}:{port}/{db}"

def gen_mysql_url(data, table=None):
    url = MYSQL_BASE.format(data)

    if table:
        url += "?table=" + table

    return url

