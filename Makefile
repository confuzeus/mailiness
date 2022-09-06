.PHONY: install-requirements compile-requirements \
	build-source build-wheel build \
	publish-test publish release \
	version-patch version-minor version-major

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
	hatch publish -r pypi

release: build publish

version-patch:
	hatch version patch

version-minor:
	hatch version minor

version-major:
	hatch version major

clean:
	hatch clean
