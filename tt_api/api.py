import sqlalchemy
import momoko
import simplejson as json
import tornado.httpserver
import tornado.ioloop
import tornado.web


class Resource(tornado.web.RequestHandler):
    def initialize(self, metadata=None):
        self.metadata = metadata

    def get(self):
        meta = {}
        object_list = self.get_object_list()
        content = json.dumps({
            'meta': meta,
            'content': object_list
        }, use_decimal=True)

        self.write_response(content)

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


class Index(Resource):
    def get(self):
        self.write('Hello, API')


class ContributorResource(Resource):
    def get_object_list(self):
        contributors = self.metadata.tables['campaign_finance_contributor']
        query = contributors.select().limit(20)
        return list(dict(o) for o in query.execute())


class ErcotResource(Resource):
    def initialize(self, metadata, db):
        super(ErcotResource, self).initialize(metadata=metadata)
        self.db = db

    @tornado.web.asynchronous
    def get(self):
        self.db.execute("""
        SELECT array_to_json(array_agg(row_to_json(t)))::text FROM (
            SELECT timestamp, "Actual System Demand", "Total System Capacity"
            FROM ercot_realtime ORDER BY timestamp LIMIT 8640
        ) t;
        """, callback=self.on_result)

    def on_result(self, cursor, error):
        content = cursor.fetchone()[0]
        self.write_response(content)
        self.finish()


def get_mysql_metadata():
    engine = sqlalchemy.create_engine('mysql://root@localhost/tribune_dev')
    metadata = sqlalchemy.MetaData(bind=engine)
    metadata.reflect(only=[
        'campaign_finance_contributor',
        'campaign_finance_contribution',
        'campaign_finance_filer',
    ])

    return metadata


def get_ercot_metadata():
    engine = sqlalchemy.create_engine('postgres:///ercot')
    metadata = sqlalchemy.MetaData(bind=engine)
    metadata.reflect(only=[
        'ercot_realtime',
    ])

    return metadata


def main():
    # Connect to databases
    mysql_metadata = get_mysql_metadata()
    ercot_metadata = get_ercot_metadata()
    ercot_db = momoko.Pool(dsn='dbname=ercot', size=4)

    # Build handler kwargs
    mysql_kwargs = dict(metadata=mysql_metadata)
    ercot_kwargs = dict(metadata=ercot_metadata, db=ercot_db)

    # Configure application
    app = tornado.web.Application([
        (r'/v1/', Index),
        (r'/v1/contributors/', ContributorResource, mysql_kwargs),
        (r'/tribclips/ercot/', ErcotResource, ercot_kwargs),
    ], debug=False)

    # Start server
    server = tornado.httpserver.HTTPServer(app)
    server.bind(8888)
    server.start(num_processes=1)
    tornado.ioloop.IOLoop.instance().start()


if __name__ == '__main__':
    main()
