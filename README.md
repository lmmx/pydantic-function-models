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

#### Example 1: Basic Validated Function

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

In this example, `ValidatedFunction` creates an internal Pydantic model that enforces integer values for `a` and `b`. If you passed a string for `a` or `b`, it would raise a `ValidationError`.

#### Example 2: Handling Extra Arguments

```python
def concat(prefix: str, *values: str, suffix: str = "") -> str:
    return prefix + " ".join(values) + suffix

vf_concat = ValidatedFunction(concat)

# We'll try both positional and keyword
args_to_validate = ("Hello,", "world!", "pydantic!")
kwargs_to_validate = {"suffix": " :)"}

validated = vf_concat.model.model_validate({
    "prefix": args_to_validate[0],
    "args": list(args_to_validate[1:]),   # Internal var-positional
    "suffix": kwargs_to_validate["suffix"]
})
result = concat(**validated.model_dump(exclude_unset=True))

print(result)  # "Hello, world! pydantic! :)"
```

Here, the function has a variable number of positional arguments (`*values`) plus a keyword argument (`suffix`). The library accommodates these via internal models (`args`/`kwargs` fields).

#### Example 3: Invalid or Missing Arguments

```python
from pydantic import ValidationError

def multiply(a: int, b: int) -> int:
    return a * b

vf_multiply = ValidatedFunction(multiply)

try:
    # Passing a string instead of an int for "b"
    vf_multiply.model.model_validate({"a": 2, "b": "not-an-integer"})
except ValidationError as e:
    print(e)
    # This will display a Pydantic ValidationError explaining the type mismatch
```

#### Example 4: Disallowed (Reserved) Parameter Names

```python
# The parameter name 'v__args' is reserved and will raise a ValidationError
def bad_func(v__args: list[str]):
    return "This won't work"

try:
    vf_bad = ValidatedFunction(bad_func)
except ValidationError as e:
    print("ValidationError:", e)
```

Because certain parameter names (e.g., `v__args`, `v__kwargs`) are used internally, they are explicitly disallowed.

#### Example 5: Examining the Internal Signature

```python
from pydantic_function_models import ValidatedFunction

def greet(name: str, times: int = 1) -> None:
    for _ in range(times):
        print(f"Hello, {name}!")

vf_greet = ValidatedFunction(greet)
print(vf_greet.sig_model.parameters)
# A structured list describing each parameter’s name, annotation, default, kind, etc.
```

This reveals the internal inspection of Python’s `inspect.Signature` stored in a Pydantic model.

#### Example 6: Working with the Pydantic Model Directly

```python
# The `.model` attribute is a dynamically generated Pydantic model:
my_model = vf_greet.model

# We can introspect or even call .model_json_schema() on it:
print(my_model.model_json_schema())
```

This can be useful if you need to generate or document JSON schemas for function arguments.

#### Example 7: Custom Handling of Positional-Only Arguments

```python
# Python 3.8+ can declare positional-only args:
def positional_only(a, /, b: int) -> int:
    return a + b

vf_pos_only = ValidatedFunction(positional_only)
values = vf_pos_only.build_values(args=(1, 2), kwargs={})
validated = vf_pos_only.model.model_validate(values)
print(positional_only(**validated.model_dump(exclude_unset=True)))  # 3
```

This demonstrates how the library checks for positional-only arguments, ensuring they aren’t used as keywords.

### Library Usage

Internally, each `ValidatedFunction` builds a Pydantic model representing the function’s signature. When you call `.model.model_validate(...)` or `.build_values(...)`, it validates the provided arguments (whether positional or keyword-based) against the signature.

---

## Project Structure

- **`validated_function.py`**: Core logic for `ValidatedFunction`, which encapsulates argument validation and Pydantic model generation.
- **`parameters.py`**: Model definitions for function parameters/signatures, including checks for reserved argument names.
- **`__init__.py`**: Declares the package version and exposes primary imports.
- **`tests/`**: Contains tests demonstrating usage and verifying correctness (e.g. using `pytest`).

## Contributing

Maintained by [lmmx](https://github.com/lmmx). Contributions are welcome!

1. **Issues & Discussions**: Please open a GitHub issue or discussion for bugs, feature requests, or questions.
2. **Pull Requests**: PRs are welcome!
   - Install the dev extra (e.g. with [uv](https://docs.astral.sh/uv/): `uv pip install -e .[dev]`)
   - Run tests (e.g. `pytest`) and include updates to docs or examples if relevant.
   - If reporting a bug, please include the version and error message/traceback if available.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).
