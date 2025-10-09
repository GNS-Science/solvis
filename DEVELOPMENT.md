# DEVELOPMENT

### Environment setup

- clone the repo
- setup python env

```
pyenv local 3.10
poetry env use 3.10
poetry sync --all-groups
```

## Auditing requirements packages

```
poetry export --all-groups > audit.txt
poetry run pip-audit -r audit.txt -s pypi --require-hashes
poetry run pip-audit -r audit.txt -s osv --require-hashes

poetry show {package-name}
```

### `safety` requires a user login registration
```
poetry run safety scan
```

## Testing 

`poetry run pytest`

## Detox (QA standards)

`poetry run tox`

Or individual steps...

 - `poetry run tox -e format` to apply formatting rules.
 - `poetry run tox -e lint` to run lint checks (style and typing).
 - `poetry run tox -e py310` to run tests with coverage report.
 
