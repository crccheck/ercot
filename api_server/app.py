from flask import Flask
app = Flask(__name__)

import psycopg2
conn = psycopg2.connect("dbname='ercot' ")


@app.route('/')
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
    return cur.fetchone()[0]


if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True,
    )
