import pymongo

class DBConnection():

    user = ""
    password = ""
    host = "localhost"
    port = 27017
    dbname = "Fanout"

    def __init__(self):
        self.connect_uri = "mongodb://{}:{}/{}".format(\
            self.host, self.port, self.dbname)

    def connect(self):
        self.conn = None

        self.client = pymongo.MongoClient(self.connect_uri,\
            serverSelectionTimeoutMS=2000, connectTimeoutMS=10000)

        try:
            self.conn = self.client[self.dbname]
            self.client.server_info()
            self.connresult = "OK"
        except Exception as e:
            self.conn = None
            self.connresult = e

        return (self.conn, self.connresult)