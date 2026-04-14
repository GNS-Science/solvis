# DEVELOPMENT

### Environment setup

- clone the repo
- setup python env

```
pyenv local 3.10
uv sync --all-groups
```

## Auditing requirements packages

```
uv export --all-groups > audit.txt
uv run pip-audit -r audit.txt -s pypi --require-hashes
uv run pip-audit -r audit.txt -s osv --require-hashes

uv run pip show {package-name}
```

### `safety` requires a user login registration
```
uv run safety scan
```

## Testing 

`uv run pytest`

## Detox (QA standards)

`uv run tox`

Or individual steps...

 - `uv run tox -e format` to apply formatting rules.
 - `uv run tox -e lint` to run lint checks (style and typing).
 - `uv run tox -e py310` to run tests with coverage report.
 
