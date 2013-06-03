set -e

# this are also used to generate the chart title
AB_OPTIONS='-n 1000 -c 1'
# options:
#
#   -n requests
#   -c concurrency
#   -w output html table
#   -g <file> gnuplot-file
#   -q quiet
OUTFILE=../metrics/out.html


# start servers in the background
python ../tt_api/api.py --port=8008 --logging=none &
PID=$!
gunicorn api_flask.app:app -b 127.0.0.1:8009 -w 4 &
pid2=$!
pids="$PID $pid2"
echo "pids: $pids"

# make sure to kill the server if terminated early
trap "kill $pids; echo bye $pids" EXIT

# give time for the servers to get up
sleep 2

plots=''

# params: url alias title
bench() {
    echo bench: $1
    ab $AB_OPTIONS -q -w $1 >> $OUTFILE
    # can't do -w and -g at the same time
    ab $AB_OPTIONS -q -g ../metrics/$2.tsv $1 > /dev/null
    plots="$plots '$2.tsv' using 9 with lines title '$3' lw 3,"
}

cp ../metrics/out_head_template.html $OUTFILE
bench localhost:8008/psy/ psy "json.dumps(RealDictCursor)"
bench localhost:8008/pg/ pg "Postgres array_to_json"
bench localhost:8008/py/ py "json.dumps(dict)"
bench localhost:8008/array/ array "json.dumps(list) async"
bench localhost:8008/array-sync/ array2 "json.dumps(list) sync"
bench localhost:8009/psy/ fpsy "Flask json.dumps(RealDictCursor)"
bench localhost:8009/pg/ fpg "Flask Postgres array_to_json"
bench localhost:8009/py/ fpy "Flask json.dumps(dict)"
echo '</section></body></html>' >> $OUTFILE

cd ../metrics
# http://tjholowaychuk.com/post/543349452/apachebench-gnuplot-graphing-benchmarks

gnuplot -e "set terminal png;
set output \"out.png\";
set title \"ab $AB_OPTIONS\";
set key top left;
set grid y;
set ylabel \"response time (ms)\";
set xlabel \"request\";
plot ${plots%?};"


# kill server, run in a subprocess so we can suppress "Terminated" message
(kill $pids 2>&1) > /dev/null

echo "bye"
