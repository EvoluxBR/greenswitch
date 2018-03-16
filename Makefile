init:
	pip install -r requirements.txt
	pip install -r test_requirements.txt

test:
	pytest --spec -s tests
