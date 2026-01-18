# Test Style Guide and Suggestions

This document summarizes the test style standards for the `hya` project and provides suggestions for future improvements.

## Current Test Style Standards

### 1. Test File Organization
- **Structure**: Flat structure with test functions, no test classes
- **Imports**: Always include `from __future__ import annotations` at the top
- **Type hints**: All test functions use `-> None` return type hint
- **Section dividers**: Not used (removed for consistency)

### 2. Test Function Naming
- **Pattern**: `test_<functionality>_<specific_case>()`
- **Examples**:
  - `test_add_resolver_int2()` - Tests add resolver with 2 integers
  - `test_get_default_registry_returns_singleton()` - Descriptive name
  - `test_resolver_registry_init_empty()` - Clear and concise

### 3. Docstrings
- **Standard**: No docstrings in test functions
- **Rationale**: Test names should be self-descriptive
- Exception: Module-level docstrings are fine if needed

### 4. Parametrization
- **Use when**: Multiple tests differ only by input/output values
- **Example**: Integration tests for checking resolver registration
- **Pattern**:
  ```python
  @pytest.mark.parametrize(
      "resolver_name",
      ["hya.add", "hya.sub", "hya.mul"],
  )
  def test_resolver_registered(resolver_name: str) -> None:
      assert OmegaConf.has_resolver(resolver_name)
  ```

### 5. Fixtures
- **Naming**: Prefix with underscore for internal/autouse fixtures
- **Example**: `_reset_default_registry()`
- **Scope**: Use appropriate scope (function, module, session)

### 6. Decorators
- **Custom decorators**: Use `@torch_available`, `@numpy_available`, `@braceexpand_available` for conditional tests
- **Parametrization**: Combine with custom decorators when needed
- **Pattern**:
  ```python
  @torch_available
  @pytest.mark.parametrize("name", ["hya.torch.tensor", "hya.torch.dtype"])
  def test_torch_resolvers(name: str) -> None:
      assert get_default_registry().has_resolver(name)
  ```

## Improvements Made

### Recent Changes (2024)
1. ✅ **Removed docstrings** from test functions for consistency
2. ✅ **Parametrized integration tests**: Reduced 22 tests to 1 parametrized test
3. ✅ **Removed section dividers**: Eliminated inconsistent `####` comment blocks
4. ✅ **Standardized imports**: Ensured `import hya` in integration tests

## Suggestions for Future Improvements

### 1. Additional Parametrization Opportunities

The following test files could benefit from parametrization:

#### `tests/unit/test_resolvers.py` (45 tests)
Consider grouping similar tests:

**Current (repetitive)**:
```python
def test_asinh_resolver_int() -> None:
    assert OmegaConf.create({"key": "${hya.asinh:1}"}).key == 0.881373587019543

def test_asinh_resolver_float() -> None:
    assert OmegaConf.create({"key": "${hya.asinh:1.0}"}).key == 0.881373587019543
```

**Suggested (parametrized)**:
```python
@pytest.mark.parametrize(
    ("input_value", "expected"),
    [
        (1, 0.881373587019543),
        (1.0, 0.881373587019543),
    ],
)
def test_asinh_resolver(input_value, expected) -> None:
    assert OmegaConf.create({"key": f"${{hya.asinh:{input_value}}}"}).key == expected
```

**Potential impact**: Could reduce ~45 tests to ~15-20 parametrized tests

### 2. Missing Edge Case Tests

Consider adding tests for:

#### Error Handling
- **Division by zero**: Test `ceildiv`, `floordiv`, `truediv` with divisor=0
- **Invalid types**: Test resolvers with unexpected input types
- **Empty inputs**: Test resolvers that accept iterables with empty lists/strings

Example:
```python
def test_ceildiv_resolver_division_by_zero() -> None:
    with pytest.raises(ZeroDivisionError):
        OmegaConf.create({"key": "${hya.ceildiv:11,0}"}).key

def test_add_resolver_empty_args() -> None:
    with pytest.raises(IndexError):
        OmegaConf.create({"key": "${hya.add:}"}).key
```

#### Boundary Conditions
- **Very large numbers**: Test math functions with large inputs
- **Negative numbers**: More comprehensive negative number tests
- **Special values**: Test with `None`, `NaN`, `Inf` where applicable

### 3. Test Organization Improvements

#### Group Related Tests
Consider organizing tests by resolver category:

```python
# Arithmetic resolvers
class TestArithmeticResolvers:
    """Tests for arithmetic resolvers (add, sub, mul, etc.)"""
    # ... tests here

# Mathematical functions
class TestMathResolvers:
    """Tests for math function resolvers (exp, log, sqrt, etc.)"""
    # ... tests here
```

**Benefit**: Easier to locate and maintain related tests

### 4. Test Coverage Gaps

Based on code analysis, consider adding tests for:

1. **Path resolvers**: Test with URL-encoded paths, special characters
2. **SHA256 resolver**: Test with various input types (not just strings)
3. **Iter_join resolver**: Test with different iterables (tuples, sets, generators)
4. **Registry edge cases**:
   - Registering same resolver multiple times with `exist_ok=True`
   - Un-registering resolvers
   - Registry state after errors

### 5. Performance Tests

Consider adding benchmark tests for frequently used resolvers:

```python
import pytest

@pytest.mark.benchmark
def test_add_resolver_performance(benchmark):
    def run_add():
        return OmegaConf.create({"key": "${hya.add:1,2,3,4,5}"}).key
    
    result = benchmark(run_add)
    assert result == 15
```

### 6. Integration Test Improvements

Current integration tests only verify resolver registration. Consider adding:

- **End-to-end tests**: Test resolvers in realistic OmegaConf configurations
- **Composition tests**: Test resolvers nested within other resolvers
- **Complex configs**: Test with real-world Hydra-style configurations

Example:
```python
def test_nested_resolvers() -> None:
    conf = OmegaConf.create({
        "a": 2,
        "b": 3,
        "c": "${hya.add:${a},${b}}",
        "d": "${hya.mul:${c},2}",
    })
    assert conf.d == 10  # (2 + 3) * 2
```

## Code Quality Tools

### Linting
The project uses:
- **ruff**: For linting and code style
- **black**: For code formatting
- **pytest**: For testing with coverage

### Running Tests
```bash
# Run all tests
python -m pytest tests/

# Run unit tests only
python -m pytest tests/unit/

# Run integration tests only
python -m pytest tests/integration/

# Run with coverage
python -m pytest tests/ --cov=hya --cov-report=html
```

## Summary

### Current State
- ✅ 147 tests across 21 test files
- ✅ Consistent naming conventions
- ✅ Good use of fixtures and decorators
- ✅ Clean, minimal style

### Recommended Next Steps
1. **High Priority**: Add error handling tests (division by zero, invalid inputs)
2. **Medium Priority**: Parametrize unit/test_resolvers.py to reduce duplication
3. **Low Priority**: Consider test organization improvements (test classes)
4. **Optional**: Add performance benchmarks for critical resolvers

### Metrics
- **Before improvements**: 147 tests, ~1500 lines of test code
- **After improvements**: 141 tests (6 consolidated via parametrization), ~1400 lines
- **Potential future**: ~120-130 well-organized tests with better coverage

---

*Last updated: 2024*
*Maintainer: Review periodically as project evolves*
