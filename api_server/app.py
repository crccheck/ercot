from functools import wraps

from flask import Flask, request
import psycopg2

from middlewares import Gzipper


app = Flask(__name__)
app.wsgi_app = Gzipper(app.wsgi_app)
conn = psycopg2.connect("dbname='ercot' ")


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


@app.route('/')
@support_jsonp
def hello_world():
    cur = conn.cursor()
    n_results = 86400 / 10
    # http://blog.hashrocket.com/posts/faster-json-generation-with-postgresql
    cur.execute("""
        SELECT array_to_json(array_agg(row_to_json(t)))::text FROM (
            SELECT timestamp, "Actual System Demand", "Total System Capacity"
            FROM ercot_realtime ORDER BY timestamp LIMIT %s
        ) t;
        """, (n_results, ))
    return app.response_class(
        cur.fetchone()[0],
        mimetype="application/json",
    )


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True,
    )
