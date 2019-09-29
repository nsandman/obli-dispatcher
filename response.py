class Response():
    MODE_JSON   = 0
    MODE_RAW    = 1
    MODE_TARGET = 2         # open URL "data" in browser
    MODE_DBGET  = 3         # get key or list of keys "data" and return to cb
    MODE_DBSAVE = 4         # save dict "data" to database
