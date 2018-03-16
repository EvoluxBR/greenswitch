init:
	pip install -r requirements.txt

test:
	pytest --spec -s tests
