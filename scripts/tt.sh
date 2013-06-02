set -e

PORT=8008
AB_OPTIONS='-n 10 -w'
# options:
#
#   -n requests
#   -c concurrency
#   -w output html table
OUTFILE=../metrics/out.html


# start server in the background
python ../tt_api/api.py --port=$PORT --logging=none &
PID=$!
echo pid: $PID

# make sure to kill the server if terminated early
trap "kill $PID; echo bye $PID" EXIT

# give time for the server to get up
sleep 1

cp ../metrics/out_head_template.html $OUTFILE
ab $AB_OPTIONS http://localhost:$PORT/pg/ >> $OUTFILE
ab $AB_OPTIONS http://localhost:$PORT/py/ >> $OUTFILE
ab $AB_OPTIONS http://localhost:$PORT/psy/ >> $OUTFILE
ab $AB_OPTIONS http://localhost:$PORT/array/ >> $OUTFILE
ab $AB_OPTIONS http://localhost:$PORT/array-sync/ >> $OUTFILE
echo '</body></html>' >> $OUTFILE

# kill server, run in a subprocess so we can suppress "Terminated" message
(kill $PID 2>&1) > /dev/null

echo "bye"
