set -e

# start server in the background
python ../tt_api/api.py & echo $! > tornado.pid

# give time for the server to get up
sleep 2

mkdir -p ../metrics
ab -n 1000 http://localhost:8000/favicon.ico > ../metrics/tornado_404.log
ab -n 1000 http://localhost:8000/ > ../metrics/tornado.log
ab -n 1000 -c 2 http://localhost:8000/ > ../metrics/tornadox2.log
# options:
#
#   -n requests
#   -c concurrency

# kill server
kill $(cat tornado.pid)
