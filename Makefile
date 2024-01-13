.DEFAULT: help

PLATFORM_DEFAULT=arm64
IMAGE_NAME=image_miner

ifeq ($(PLATFORM),)
PLATFORM = $(PLATFORM_DEFAULT)
endif

ifeq ($(PLATFORM),arm64)
BASE_IMAGE=arm64v8/python:3.10-slim

else ifeq ($(PLATFORM),x86)
BASE_IMAGE=python:3.10-slim

else
$(error Unknown platform: $(PLATFORM))
endif

.PHONY: help
help:
	@echo 'help          - show help information'
	@echo 'hooks         - install pre-commit hooks'
	@echo 'bootstrap     - setup project dependencies and init a new venv'
	@echo 'lint          - run linters from pre-commit hooks'
	@echo 'image         - build docker image with project'

bootstrap:
	@poetry install --sync --verbose --with dev --with tests

hooks: bootstrap
	@poetry run pre-commit install --config .githooks.yml
	@poetry run pre-commit install --config .githooks.yml --hook-type commit-msg

lint: bootstrap
	@poetry run pre-commit run --all-files --config .githooks.yml

.PHONY: image
image:
	@echo "Using platform: $(PLATFORM), Image: $(BASE_IMAGE)"
	@docker run --rm --privileged multiarch/qemu-user-static --reset -p yes
	@docker build \
		    --build-arg "BASE_IMAGE=$(BASE_IMAGE)" \
			--tag $(IMAGE_NAME):$(PLATFORM)-latest $(PWD)
