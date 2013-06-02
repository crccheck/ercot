import json
import os

import momoko
import sqlalchemy
import tornado.httpserver
import tornado.ioloop
import tornado.web


class BaseResource(tornado.web.RequestHandler):
    def initialize(self, metadata=None):
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


class ErcotResource(BaseResource):
    def initialize(self, metadata, db):
        super(ErcotResource, self).initialize(metadata=metadata)
        self.db = db

    @tornado.web.asynchronous
    def get(self):
        self.db.execute("""
        SELECT array_to_json(array_agg(row_to_json(t)))::text FROM (
            SELECT timestamp, "actual_system_demand", "total_system_capacity"
            FROM ercot_realtime ORDER BY timestamp LIMIT 8640
        ) t;
        """, callback=self.on_result)

    def on_result(self, cursor, error):
        content = cursor.fetchone()[0]
        self.write_response(content)
        self.finish()


# TODO syncronous request resource example


class Ercot2Resource(ErcotResource):
    @tornado.web.asynchronous
    def get(self):
        self.db.execute("""
            SELECT timestamp, actual_system_demand, total_system_capacity
            FROM ercot_realtime ORDER BY timestamp LIMIT 8640;
        """, callback=self.on_result)

    def on_result(self, cursor, error):
        def dictify(cursor):
            # Too lazy to figure out how to use dictCursor just for this Resource
            for x in cursor:
                yield dict(zip(('timestamp', 'actual_system_demand', 'total_system_capacity'), x))
        import datetime
        dthandler = lambda obj: obj.isoformat(sep=' ') if isinstance(obj, datetime.datetime) else None
        content = json.dumps(list(dictify(cursor)), default=dthandler)
        self.write_response(content)
        self.finish()


def get_ercot_metadata():
    engine = sqlalchemy.create_engine(
            os.environ.get('DATABASE_URL', 'postgres:///ercot'))
    metadata = sqlalchemy.MetaData(bind=engine)
    metadata.reflect(only=[
        'ercot_realtime',
    ])

    return metadata


def main():
    # Connect to databases
    ercot_metadata = get_ercot_metadata()
    ercot_db = momoko.Pool(dsn='dbname=ercot', size=4)

    # Build handler kwargs
    ercot_kwargs = dict(metadata=ercot_metadata, db=ercot_db)

    # Configure application
    app = tornado.web.Application([
        (r'/', ErcotResource, ercot_kwargs),
        (r'/2/', Ercot2Resource, ercot_kwargs),
    ], debug=True)

    # Start server
    server = tornado.httpserver.HTTPServer(app)
    server.bind(8000)
    server.start(num_processes=1)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
