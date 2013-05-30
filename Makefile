
clean:
	find -name "*.pyc" -delete
	rm -rf MANIFEST
	rm -rf build
	rm -rf dist
	rm -rf *.egg-info

test:
	nosetests -s

.PHONY: test
