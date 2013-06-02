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


bench() {
    ab $AB_OPTIONS -w http://localhost:$PORT$1 >> $OUTFILE
    # can't do -w and -g at the same time
    ab $AB_OPTIONS -g ../metrics/$2.tsv http://localhost:$PORT$1 > /dev/null
}

cp ../metrics/out_head_template.html $OUTFILE
bench /psy/ psy
bench /pg/ pg
bench /py/ py
bench /array/ array
bench /array-sync/ array2
echo '</section></body></html>' >> $OUTFILE

cd ../metrics
# http://tjholowaychuk.com/post/543349452/apachebench-gnuplot-graphing-benchmarks
# plots manually ordered slowest to fastest

gnuplot -e "set terminal png;
set output \"out.png\";
set key top left;
set grid y;
set ylabel \"response time (ms)\";
plot
  'psy.tsv' using 9 smooth sbezier with lines title 'json.dumps(RealDictCursor)',
  'pg.tsv' using 9 smooth sbezier with lines title 'Postgres array_to_json',
  'py.tsv' using 9 smooth sbezier with lines title 'json.dumps(dict)',
  'array.tsv' using 9 smooth sbezier with lines title 'json.dumps(list) async',
  'array2.tsv' using 9 smooth sbezier with lines title 'json.dumps(list) sync';
"


# kill server, run in a subprocess so we can suppress "Terminated" message
(kill $PID 2>&1) > /dev/null

echo "bye"
