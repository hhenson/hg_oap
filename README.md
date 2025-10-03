# HGraph Orders and Pricing Library

Provides a library, based on the hgraph functional reactive framework to
support creating order and pricing logic.

The core components of the library include:

* instruments
* positions
* portfolios
* orders
* pricing

This library is currently very green and is expected to have significant changes.


## Development

This project now uses the uv package manager for dependency management and running tasks.

- uv homepage and install instructions: https://docs.astral.sh/uv/

Once you have checked out the project, you can set up a local virtual environment and install dependencies as follows:

1) Create or reuse a virtual environment with Python 3.11 (recommended):

```bash
uv venv -p 3.11
```

2) Activate the virtual environment (example for bash/zsh):

```bash
source .venv/bin/activate
```

3) Install the project and all development dependencies (tests, docs, etc.):

```bash
uv sync --all-extras --all-groups
```

Notes:
- `uv sync` reads pyproject.toml and uv.lock and installs the project in editable mode along with dependencies.
- If you only want runtime dependencies, omit `--all-groups`.
- If you don't need optional extras, omit `--all-extras`.

To see where the Python interpreter lives for IDE configuration (e.g., PyCharm), after activating the venv you can run:

```bash
which python
```

PyCharm can be pointed at the `.venv` interpreter in the project root.

### Run Tests

```bash
# No Coverage
uv run pytest
```

```bash
# Generate Coverage Report
uv run pytest --cov=hg_oap --cov-report=xml
```