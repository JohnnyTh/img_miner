.DEFAULT: help

.PHONY: help
help:
	@echo 'help          - show help information'
	@echo 'hooks         - install pre-commit hooks'
	@echo 'bootstrap     - setup project dependencies and init a new venv'
	@echo 'lint          - run linters from pre-commit hooks'

bootstrap:
	@poetry install --sync --verbose --with dev --with tests

hooks: bootstrap
	@poetry run pre-commit install --config .githooks.yml
	@poetry run pre-commit install --config .githooks.yml --hook-type commit-msg

lint: bootstrap
	@poetry run pre-commit run --all-files --config .githooks.yml
