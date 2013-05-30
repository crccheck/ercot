
clean:
	find -name "*.pyc" -delete
	rm -rf MANIFEST
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info

test:
	nosetests -s


reports:
	mkdir -p reports

flask:
	python -m api_flask &

ab_flask: reports
	ab -n 100 http://localhost:8000/ > reports/flask.log

tornado:
	echo $$(cat Procfile)

ab_tornado: reports
	python -m api_tornado & echo $$! > tornado.pid
	sleep 2
	ab -n 100 http://localhost:8000/ > reports/tornado.log
	kill -TERM -$$(cat tornado.pid)
	rm tornado.pid


.PHONY: clean test bench
