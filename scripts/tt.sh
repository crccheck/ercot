set -e

PORT=8008

# start server in the background
python ../tt_api/api.py --port=$PORT --logging=none &
PID=$!
echo pid: $PID

# make sure to kill the server if terminated early
trap "kill $PID; echo bye $PID" EXIT

# give time for the server to get up
sleep 1

mkdir -p ../metrics
ab -n 100 http://localhost:$PORT/pg/ > ../metrics/tornado_pg.log
ab -n 100 http://localhost:$PORT/py/ > ../metrics/tornado_py.log
ab -n 100 http://localhost:$PORT/psy/ > ../metrics/tornado_psy.log
ab -n 100 http://localhost:$PORT/array/ > ../metrics/tornado_array.log
ab -n 100 http://localhost:$PORT/array-sync/ > ../metrics/tornado_arraysync.log
# ab -n 100 -c 2 http://localhost:$PORT/ > ../metrics/tornadox2.log
# options:
#
#   -n requests
#   -c concurrency

# kill server, run in a subprocess so we can suppress "Terminated" message
(kill $PID 2>&1) > /dev/null

echo "bye"
