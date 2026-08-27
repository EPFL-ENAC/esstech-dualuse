# dualuse

An example standalone Python package for the `esstech-dualuse` backend.

It is a uv workspace member of the parent `backend/` project and is installed as a
regular dependency there. This keeps the package independently editable and testable
while making it importable from the FastAPI app.

## Requirements

- [uv](https://docs.astral.sh/uv/getting-started/installation/) Python package and project manager

## Deploying locally

Setup your environment by running:

```bash
make install
```

## Test

```bash
make test
```

## Usage

```python
from dualuse import greet

print(greet("world"))
```

## Install from git

You can also install this package directly from the repository without cloning it:

```bash
pip install "git+https://github.com/<org>/esstech-dualuse.git#subdirectory=backend/package"
```

See the root README for details.
