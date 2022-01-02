SHELL = bash

activate = source venv/bin/activate
python = python3.9
dockerhub_repo = scoopex666

all: deps
.PHONY: all

deps: venv/bin/activate
.PHONY: deps


venv/bin/activate: requirements.txt
	${python} -m venv venv
	@# TODO: installation of wheel solves a pip install error, we have to check if that is needed permamently
	@# because it seems to be a packaging issue
	${activate} && \
		pip install wheel && \
		pip install -r requirements.txt

clean:
	rm -rf venv
.PHONY: clean

check:
	@# run sequentially so the output is easier to read
	${MAKE} --no-print-directory lint
	${MAKE} --no-print-directory type-check
	${MAKE} --no-print-directory test
.PHONY: check


lint: deps
	${activate} && ${python} -m flake8 base k8sobjects
.PHONY: lint

type-check: deps
	${activate} && ${python} -m mypy --no-color-output --pretty base k8sobjects
.PHONY: type-check

test: deps
	${activate} && ${python} -m pytest tests
.PHONY: test

run: deps
	${activate} && ${python} check_kubernetesd config_flip-dev.ini
.PHONY: run

doc:
	cd template && ./create_template_documentation
.PHONY: doc

publish: 
	./build.sh default publish_image ${dockerhub_repo}
.PHONY: publish

release: test doc
	[ `git status --porcelain=v1 2>/dev/null | wc -l` -le 0 ]
	${MAKE} --no-print-directory publish
.PHONY: release
