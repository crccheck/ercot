from functools import wraps
import json

from flask import Flask, request
import psycopg2
import psycopg2.extras

# from middlewares import Gzipper
from ercot.utils import dthandler, get_pg_connect_kwargs


app = Flask(__name__)


# https://gist.github.com/aisipos/1094140
def support_jsonp(f):
    """Wraps JSONified output for JSONP"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        callback = request.args.get('callback', False)
        if callback:
            content = str(callback) + '(' + str(f(*args, **kwargs).data) + ')'
            return app.response_class(
                content,
                mimetype='application/javascript',
            )
        else:
            return f(*args, **kwargs)
    return decorated_function


@app.route('/pg/')
@support_jsonp
def pg_resource():
    cur = conn.cursor()
    # http://blog.hashrocket.com/posts/faster-json-generation-with-postgresql
    cur.execute("""
        SELECT array_to_json(array_agg(row_to_json(t)))::text FROM (
            %s
        ) t;
        """ % sql)
    return app.response_class(
        cur.fetchone()[0],
        mimetype="application/json",
    )


@app.route('/py/')
@support_jsonp
def py_resource():
    cur = conn.cursor()
    cur.execute(sql)
    return app.response_class(
        json.dumps([dict(zip(columns, x)) for x in cur], default=dthandler),
        mimetype="application/json",
    )


@app.route('/psy/')
@support_jsonp
def psy_resource():
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    # cursor = conn.cursor(cursor_factory=extras.RealDictCursor)
    cursor.execute(sql)
    return app.response_class(
        json.dumps(list(cursor), default=dthandler),
        mimetype="application/json",
    )


if __name__ == '__main__':
    # app.wsgi_app = Gzipper(app.wsgi_app)
    conn = psycopg2.connect(**get_pg_connect_kwargs('postgres:///ercot'))

    columns = (
        'timestamp',
        'actual_system_demand',
        'total_system_capacity',
    )
    # 2016 = 14 days / 10 minutes
    sql = ("SELECT %s FROM ercot_realtime ORDER BY timestamp LIMIT 2016"
            % ', '.join(columns))

    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True,
    )
