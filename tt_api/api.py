import json
import os

import momoko
import psycopg2
import sqlalchemy
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web

from ercot.utils import dthandler, get_pg_connect_kwargs


class BaseResource(tornado.web.RequestHandler):
    columns = (
        'timestamp',
        'actual_system_demand',
        'total_system_capacity',
    )
    # 2016 = 14 days / 10 minutes
    sql = ("SELECT %s FROM ercot_realtime ORDER BY timestamp LIMIT 2016"
            % ', '.join(columns))

    def initialize(self, db, metadata=None):
        self.db = db
        self.metadata = metadata

    def get(self):
        raise NotImplementedError

    def write_response(self, content):
        callback = self.get_argument('callback', '')
        if callback:
            self.write_jsonp(callback, content)
        else:
            self.write_json(content)

    def write_json(self, content):
        self.write(content)
        self.set_header("Content-Type", "application/json; charset=UTF-8")

    def write_jsonp(self, callback, content):
        content = '%s(%s)' % (callback, content)
        self.write(content)
        self.set_header(
            "Content-Type", "application/javascript; charset=UTF-8")


class ErcotPGResource(BaseResource):
    """Makes Postgres do the JSON."""
    @tornado.web.asynchronous
    def get(self):
        self.db.execute("""
        SELECT array_to_json(array_agg(row_to_json(t)))::text FROM (
            %s
        ) t;
        """ % self.sql, callback=self.on_result)

    def on_result(self, cursor, error):
        content = cursor.fetchone()[0]
        self.write_response(content)
        self.finish()


class ErcotPyResource(BaseResource):
    """Makes Python do the JSON."""
    @tornado.web.asynchronous
    def get(self):
        self.db.execute(self.sql, callback=self.on_result)

    def on_result(self, cursor, error):
        def dictify(cursor):
            for x in cursor:
                yield dict(zip(self.columns, x))
        content = json.dumps(list(dictify(cursor)), default=dthandler)
        self.write_response(content)
        self.finish()


class ErcotPsyResource(BaseResource):
    """Makes Python do the JSON with psycopg2 making the dicts."""
    @tornado.web.asynchronous
    def get(self):
        self.db.execute(self.sql,
            # DictCursor returns dicts with no keys for some reason
            cursor_factory=psycopg2.extras.RealDictCursor,
            callback=self.on_result,
        )

    def on_result(self, cursor, error):
        content = json.dumps(list(cursor), default=dthandler)
        self.write_response(content)
        self.finish()


class ErcotArrayResource(BaseResource):
    """Makes Python do the JSON, Return arrays instead of dicts."""
    @tornado.web.asynchronous
    def get(self):
        self.db.execute(self.sql, callback=self.on_result)

    def on_result(self, cursor, error):
        content = json.dumps(list(cursor), default=dthandler)
        self.write_response(content)
        self.finish()


class ErcotArraySyncResource(BaseResource):
    """Makes Python do the JSON, Return arrays instead of dicts. Synchronous."""
    def get(self):
        cursor = self.db.cursor()
        cursor.execute(self.sql)
        content = json.dumps(list(cursor), default=dthandler)
        self.write_response(content)


def get_ercot_metadata():
    engine = sqlalchemy.create_engine(
            os.environ.get('DATABASE_URL', 'postgres:///ercot'))
    metadata = sqlalchemy.MetaData(bind=engine)
    metadata.reflect(only=[
        'ercot_realtime',
    ])

    return metadata


def main():
    tornado.options.define('port', default=8000, type=int, help="Listening Port")
    tornado.options.parse_command_line()

    # Connect to databases
    ercot_metadata = get_ercot_metadata()
    ercot_db = momoko.Pool(dsn='dbname=ercot', size=4)
    db_conn = psycopg2.connect(**get_pg_connect_kwargs('postgres:///ercot'))

    # Build handler kwargs
    ercot_kwargs = dict(metadata=ercot_metadata, db=ercot_db)

    # Configure application
    app = tornado.web.Application([
        (r'/pg/', ErcotPGResource, ercot_kwargs),
        (r'/py/', ErcotPyResource, ercot_kwargs),
        (r'/psy/', ErcotPsyResource, ercot_kwargs),
        (r'/array/', ErcotArrayResource, ercot_kwargs),
        (r'/array-sync/', ErcotArraySyncResource, dict(db=db_conn)),
    ], debug=True)

    # Start server
    server = tornado.httpserver.HTTPServer(app)
    server.bind(tornado.options.options.port)
    server.start(num_processes=1)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
