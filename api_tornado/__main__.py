"""

Proof of concept tornado server based on:
A module for asynchronous PostgreSQL queries in Tornado
https://gist.github.com/FSX/861193
"""
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
import dj_database_url
import tornado.web

from .async_psycopg2 import Pool

config = dj_database_url.config(default="postgres:///ercot")
config_map = dict(
    NAME='database',
    USER='user',
    PASSWORD='password',
    HOST='host',
    PORT='port',
)
connect_args = dict([(config_map[k], v) for k, v in config.items()
        if k in config_map])


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r'/', MainHandler),
        ]
        settings = dict(
        )
        tornado.web.Application.__init__(self, handlers, **settings)

        self.db = None


class BaseHandler(tornado.web.RequestHandler):
    @property
    def db(self):
        if not self.application.db:
            connect_args['async'] = 1
            self.application.db = Pool(1, 20, 10, **connect_args)
        return self.application.db


class MainHandler(BaseHandler):
    @tornado.web.asynchronous
    def get(self):
        n_results = 86400 / 10
        sql = """
        SELECT array_to_json(array_agg(row_to_json(t)))::text FROM (
            SELECT timestamp, "Actual System Demand", "Total System Capacity"
            FROM ercot_realtime ORDER BY timestamp LIMIT %s
        ) t;
        """
        self.db.execute(sql, (n_results, ), callback=self._on_response)

    def _on_response(self, cursor):
        out = cursor.fetchone()[0]
        cursor.close()
        self.write(out)
        self.finish()


if __name__ == "__main__":
    http_server = HTTPServer(Application())
    http_server.bind(8000)
    http_server.start(0)
    IOLoop.instance().start()
