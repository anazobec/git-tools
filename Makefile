.PHONY: help
help: ## Prints help for targets with comments
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

.PHONY: build
build: ## Build git-tools binary
	@pyi-makespec --onefile --paths="./src" --paths="./src/tools" ./src/main.py --name "git-tools" && \
		pyinstaller --clean "git-tools.spec"

.PHONY: format
format: ## Format using ruff
	@echo "--- RUFF ---"
	@ruff format --respect-gitignore
	@ruff check --unsafe-fixes --fix --show-fixes

.PHONY: lint
lint: ## Lint using mypy and ruff
	@echo "--- MYPY ---"
	@mypy .

	@echo -e "\n--- RUFF ---"
	@ruff check

.PHONY: sanity
sanity: ## Sanity check before formatting
	@echo "--- RUFF ---"
	@ruff format --check --diff --respect-gitignore
	@ruff check --diff --unsafe-fixes
