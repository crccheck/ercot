
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
	python -m api_flask

ab_flask: reports
	ab -n 100 http://localhost:8000/ > reports/flask.log

tornado:
	python -m api_tornado

ab_tornado: reports
	ab -n 100 -c 2 http://localhost:8000/ > reports/tornado.log


.PHONY: clean test bench
