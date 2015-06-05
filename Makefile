run: env webapp testserver


testserver: env
	.env/bin/python flask_app/app.py

env: .env/.up-to-date

.env/.up-to-date: Makefile flask_app/pip_requirements.txt
	python -m virtualenv .env
	.env/bin/pip install -r ./flask_app/pip_requirements.txt
	touch .env/.up-to-date


webapp:
	cd frontend && ember build --output-path=../flask_app/static
