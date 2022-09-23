.PHONY: install-requirements compile-requirements \
	build-source build-wheel build \
	publish-test publish release \
	version-patch version-minor version-major fmt lint fmtl

install-requirements:
	pip install -r requirements/base.txt -r requirements/dev.txt
	pip install -e .

compile-requirements:
	pip-compile -o requirements/base.txt pyproject.toml
	pip-compile --extra dev -o requirements/dev.txt pyproject.toml

build-source:
	hatch build -t sdist

build-wheel:
	hatch build -t wheel

build: build-source build-wheel

publish-test:
	hatch publish -r testpypi

publish:
	hatch publish

release: build publish

version-patch:
	hatch version patch

version-minor:
	hatch version minor

version-major:
	hatch version major

fmt:
	@black --exclude __pycache__ src tests
	@isort --skip __pycache__ src tests

lint:
	@flake8 src tests

fmtl: fmt lint

clean:
	hatch clean
