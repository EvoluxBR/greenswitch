init:
	pip install -r requirements.txt
	pip install -r test_requirements.txt

test:
	pytest --spec -s tests/

test-coverage:
	pytest --spec -s tests/ --cov=./greenswitch --cov-report term-missing

build:
	python setup.py sdist bdist_wheel

upload:
	python -m twine upload dist/*

release: build upload
