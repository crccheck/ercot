set -e

# start server in the background
python ../tt_api/api.py &
PID=$!
echo pid: $PID

# make sure to kill the server if terminated early
trap "kill $PID; echo bye $PID" EXIT

# give time for the server to get up
sleep 1

mkdir -p ../metrics
ab -n 1000 http://localhost:8000/ > ../metrics/tornado.log
ab -n 1000 -c 2 http://localhost:8000/ > ../metrics/tornadox2.log
# options:
#
#   -n requests
#   -c concurrency

# kill server, run in a subprocess so we can suppress "Terminated" message
(kill $PID 2>&1) > /dev/null

echo "bye"
