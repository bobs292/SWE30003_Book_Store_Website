# SWE30003_Book_Store_Website
# Favourite Books

Online bookstore for SWE30003 Software Architectures and Design.

See docs/file-structure.md for the full project structure and architectural
decisions.

---

## How to Install

Clone the repository and create a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

Install the package and its dependencies.

```bash
pip install -e .
```

---

## Running the web Application

```bash
cd src
flask run
```

---

## Running Tests
The test suite includes unit tests, integration tests, and code style checks.
```bash
hatch run pytest
```
This runs:

    All unit and integration tests
    Code style checks via flake8 (formatting, linting, and pytest-specific style)
    Architectural import contract verification
To run tests without code style checks:
```bash
hatch run pytest -p no:flake8
```
## Setting Up for Development
The pip command installs the project and all development dependencies including pytest,
import-linter, pre-commit, pytest-flake8, flake8, black, and isort. It also makes
all imports resolve from src/ so you never need to modify your Python path manually.
Next, install the pre-commit hooks.
```bash
hatch run pre-commit install
```

This registers a git hook that runs automatically every time you run
git commit. You only need to do this once after cloning.

---

## How the Architecture is Enforced

This project uses import-linter to enforce the three-layer dependency rule.

The rule is: Presentation can import from Domain. Domain can import from Data.
Nothing can import upward.

import-linter checks this by scanning every import statement in the codebase
and verifying none of them cross a layer boundary in the wrong direction. If
they do, it prints exactly which file made the illegal import and which
contract it broke.

The check runs automatically when you commit. If a layer boundary is broken
the commit is blocked and you will see output.

To explore the dependencie graphs run:
```bash
hatch run import-linter explore src
```
or to explore a specifc layer (replace domain with your target layer)
```bash
hatch run import-linter explore src.domain
```
