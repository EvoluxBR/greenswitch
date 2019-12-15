init:
	pip install -r requirements.txt
	pip install -r test_requirements.txt

test:
	pytest --spec -s tests/

test-coverage:
	pytest --spec -s tests/ --cov=./greenswitch --cov-report term-missing
