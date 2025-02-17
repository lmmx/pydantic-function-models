# Pydantic Function Models

[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)
[![PyPI](https://img.shields.io/pypi/v/pydantic-function-models.svg)](https://pypi.org/project/pydantic-function-models)
[![Supported Python versions](https://img.shields.io/pypi/pyversions/pydantic-function-models.svg)](https://pypi.org/project/pydantic-function-models)
[![License](https://img.shields.io/pypi/l/pydantic-function-models.svg)](https://pypi.python.org/pypi/pydantic-function-models)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/lmmx/pydantic-function-models/master.svg)](https://results.pre-commit.ci/latest/github/lmmx/pydantic-function-models/master)

A library to model Python function signatures using Pydantic, inspired by the now-deprecated `ValidatedFunction` from Pydantic v1. This package helps validate function arguments according to type hints, bridging the gap between Pydantic v1 and v2.

## Installation

```bash
pip install pydantic-function-models
```

## Features

- **Signature modelling**: Wrap any Python function to model its signature (positional, keyword, etc.) using Pydantic. Note that if you are after just **validation** (whether the arguments are valid) then  you want [validate call](https://docs.pydantic.dev/latest/api/validate_call/)
- **Painless migration from Pydantic v1**: Provides a `ValidatedFunction` class ported to v2, for those who relied on `ValidatedFunction` in v1.
- **Clear error messages**: Raises Pydantic `ValidationError` with helpful details if input arguments do not match the declared types.
- **Reserved name checks**: Prevents usage of special parameter names (e.g., `v__args`, `v__kwargs`) that could conflict with internal validation logic.

## Usage

Below is a general overview of how to use **pydantic-function-models** in your own code. There is no built-in command-line interface; usage is purely through Python imports.

### Command-Line Interface

This library does **not** provide a CLI. All functionality is accessed by importing and using its classes in Python code. The remaining “Examples” section demonstrates typical usage patterns.

#### Example: Basic Validated Function

```python
from pydantic_function_models import ValidatedFunction

def add(a: int, b: int) -> int:
    return a + b

vf = ValidatedFunction(add)

# Build arguments for validation
args_to_validate = (1,)
kwargs_to_validate = {"b": 2}

validated = vf.model.model_validate({
    "a": args_to_validate[0],
    "b": kwargs_to_validate["b"]
})
result = add(**validated.model_dump(exclude_unset=True))

print(result)  # 3
```

Here, `ValidatedFunction` creates an internal Pydantic model that enforces integer values for `a` and `b`. If you passed a string for `a` or `b`, it would raise a `ValidationError`.

### Library Usage

Internally, each `ValidatedFunction` builds a Pydantic model representing the function’s signature. When you call `.model.model_validate(...)` or `.build_values(...)`, it validates the provided arguments (whether positional or keyword-based) against the signature.

---

## Project Structure

Take a look at the internals here:

- `validated_function.py`: Core logic for `ValidatedFunction`, which encapsulates argument validation and Pydantic model generation.
- `parameters.py`: Model definitions for function parameters/signatures, with checks for reserved argument names.

## Contributing

Maintained by [lmmx](https://github.com/lmmx). Contributions are welcome!

1. **Issues & Discussions**: Please open a GitHub issue or discussion for bugs, feature requests, or questions.
2. **Pull Requests**: PRs are welcome!
   - Install the dev extra (e.g. with [uv](https://docs.astral.sh/uv/): `uv pip install -e .[dev]`)
   - Run tests (e.g. `pytest`) and include updates to docs or examples if relevant.
   - If reporting a bug, please include the version and error message/traceback if available.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
