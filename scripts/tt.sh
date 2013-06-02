
# start server in the background
python ../tt_api/api.py & echo $! > tornado.pid

# give time for the server to get up
sleep 2

mkdir -p ../metrics
ab -n 1000 -c 2 http://localhost:8000/ > ../metrics/tornado.log
# options:
#
#   -n requests
#   -c concurrency

# kill server
kill $(cat tornado.pid)
