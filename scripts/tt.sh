set -e

PORT=8008
AB_OPTIONS='-n 100'
# options:
#
#   -n requests
#   -c concurrency
#   -w output html table
#   -g gnuplot-file
OUTFILE=../metrics/out.html


# start server in the background
python ../tt_api/api.py --port=$PORT --logging=none &
PID=$!
echo pid: $PID

# make sure to kill the server if terminated early
trap "kill $PID; echo bye $PID" EXIT

# give time for the server to get up
sleep 1

plots=''

# params: url alias title
bench() {
    ab $AB_OPTIONS -w http://localhost:$PORT$1 >> $OUTFILE
    # can't do -w and -g at the same time
    ab $AB_OPTIONS -g ../metrics/$2.tsv http://localhost:$PORT$1 > /dev/null
    plots="$plots '$2.tsv' using 9 with lines title '$3' lw 3,"
}

cp ../metrics/out_head_template.html $OUTFILE
bench /psy/ psy "json.dumps(RealDictCursor)"
bench /pg/ pg "Postgres array_to_json"
bench /py/ py "json.dumps(dict)"
bench /array/ array "json.dumps(list) async"
bench /array-sync/ array2 "json.dumps(list) sync"
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
(kill $PID 2>&1) > /dev/null

echo "bye"
