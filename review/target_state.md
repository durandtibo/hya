# hya: target state and the changes to reach it

This document describes the design `hya` should have, then the changes to make to the current code
(`main`, `a886c33`, 0.5.0a0) to get there. It replaces the previous review (PRs #753 to #764), whose
plan is now implemented: this version starts from what the code does today and lists only what is
still wrong or missing. The design follows the properties of `docs/docs/properties.md` and the rules
of `CLAUDE.md`. Its aim is a small package that is easy to maintain: **one registry, one
registration rule, thin resolvers, nothing heavy at import time, and an install that works next to
Hydra**. Breaking changes are accepted and the future state matters more than the past one.

Evidence comes from probes run on `main` (Python 3.14 in `.venv`, plus throw-away environments with
Python 3.11 and 3.12 and OmegaConf 2.2.3, 2.3.0 and 2.4.0; scripts kept outside the repository).
Items are tagged **[verified]** (reproduced) or **[reading]** (from the code). Nothing in `src`,
`tests` or `docs` was changed by this review.

---

## 1. Properties of the package

These are the rules the package guarantees. Each one is enforced by code or by a test (section 8).
The numbers are those of `docs/docs/properties.md`. Rows marked **changed** or **new** differ from
that page; section 2 says where `main` violates a property.

| #   | Property                   | Statement                                                                                                                                                                                                                                     |
| --- | -------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P1  | **Import is enough**       | `import hya` publishes every default resolver to OmegaConf. No other call is needed, and importing `hya` again after `OmegaConf.clear_resolvers()` or calling `register_resolvers()` publishes them again (**changed**).                      |
| P2  | **Cheap import**           | `import hya` imports neither `numpy`, `torch` nor `braceexpand`, does not even look for them on disk, and emits no warning. The module of an optional resolver is imported on the first call of that resolver (**changed**).                  |
| P3  | **Namespaced**             | Every built-in key starts with `hya.`. Optional ones are grouped (`hya.np.*`, `hya.torch.*`). Nothing is registered outside this namespace.                                                                                                   |
| P4  | **Thin resolvers**         | A resolver is a standard library callable or a function of a few lines with one documented behaviour. No hidden state, no I/O beyond what its name says (`hya.path` touches the file system).                                                 |
| P5  | **Pure**                   | A resolver never modifies its arguments. Interpolating a config node into a resolver cannot change the config.                                                                                                                                |
| P6  | **Deterministic output**   | Same arguments ⇒ same output, including inside error messages (sorted, no set order). A hash does not depend on the process (no `hash()`).                                                                                                    |
| P7  | **Explicit registry**      | A `ResolverRegistry` is a plain key → callable map. `register` adds, `register_resolvers` publishes to OmegaConf. Registries are independent of each other.                                                                                   |
| P8  | **Publishing is safe**     | `register_resolvers()` is idempotent and never silent about a conflict: a key that changed since it was published, or that another source registered, is skipped with a warning unless `replace=True` (**changed**: see P1).                  |
| P9  | **One default registry**   | `get_default_registry()` returns one process-wide registry with the built-in resolvers. **It holds the same keys on every machine, whatever packages are installed** (**changed**). Users extend it or create their own registry.             |
| P10 | **Errors are OmegaConf's** | A failing resolver surfaces as `InterpolationResolutionError` with the original error as cause. `hya` adds no wrapper. **A missing optional package gives an error that says how to install it, through an interpolation too** (**changed**). |
| P11 | **Any value out**          | A resolver may return any Python object (`Path`, `ndarray`, `Tensor`, `dtype`, list). Such values are for use in code and are not meant for `OmegaConf.to_yaml`.                                                                              |
| P12 | **Typed and documented**   | `py.typed`, `pyright --verifytypes` clean, every public name documented with a doctest, every resolver listed in `docs/` with its signature and one example.                                                                                  |
| P13 | **Keyword-only options**   | Options are keyword-only (`exist_ok`, `replace`). Positional arguments are the data.                                                                                                                                                          |
| P14 | **Installs next to Hydra** | `hya` accepts every OmegaConf release that a Hydra release accepts (`omegaconf >=2.2,<3.0`), on Python 3.11 and later. CI runs the tests on the oldest and the newest OmegaConf (**new**).                                                    |

**Not guaranteed:** thread-safety of registering while OmegaConf resolves (OmegaConf's registry is a
global dict); caching of resolver outputs (OmegaConf default: none); support of
`OmegaConf.to_yaml(resolve=True)` for object-valued resolvers (P11); the textual form of
`hya.sha256` for an input whose `str()` OmegaConf changes (the hash is of `str(obj)`).

---

## 2. Where `main` stands

### 2.1 Done since the previous review

| Item of the previous plan                                               | State                                                                          |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `hya.add` / `hya.mul` do not modify their arguments                     | done, doctest and regression test                                              |
| Overriding a resolver warns, `replace=True` applies it                  | done (`_published`, `register_resolvers(*, replace=False)`)                    |
| Keyword-only `exist_ok`, read-only `state`, `ResolverRegistry` exported | done                                                                           |
| Lazy optional resolvers (`register_lazy`), cheap import                 | done: `import hya` takes 0.11 s and imports no optional package **[verified]** |
| 14 stdlib wrappers replaced by the callables                            | done: `resolvers.py` is 249 lines, 7 functions                                 |
| `hya.to_path` merged into `hya.path`                                    | done                                                                           |
| `hya.braceexpand` returns a list, sorted dtype names                    | done                                                                           |
| Properties and migration pages                                          | done (`docs/docs/properties.md`, `docs/docs/migration/v0.4_to_v0.5.md`)        |

Gates on `main` **[verified]**: 249 tests pass, 6 are skipped, coverage of `src` is 100 %,
`ruff check` and `ty` pass, 24 doctests pass. `pyright --verifytypes hya --ignoreexternal` prints
`No py.typed file found` and a score of 0 % in this environment although `src/hya/py.typed` exists:
pyright does not resolve the package directory of the editable install here. The gate is not
informative locally; check it in CI (decision D6).

### 2.2 What is still wrong

#### Install

- **I1. `hya` 0.5 cannot be installed next to a stable Hydra [verified, PyPI].** `hya` requires
  `omegaconf >=2.4,<3.0`. `hydra-core` 1.3.8 (released 2026-10-25) requires `omegaconf >=2.2,<2.4`.
  The only Hydra that accepts OmegaConf 2.4 is `1.4.0rc3`, which requires `omegaconf >=2.4.1rc1` and
  is a pre-release. A library "designed to be used with Hydra" that an installer refuses to combine
  with Hydra stays unused: every Hydra user would remain on 0.4. The migration page warns about it;
  a warning is not a fix. Violates P14.
- **I2. The `>=2.4` requirement is not needed [verified].** With one publish call that switches on
  the OmegaConf version, all resolvers (including the lazy ones, `hya.path`, `hya.np.array`,
  `hya.braceexpand`) work with OmegaConf 2.2.3 and 2.3.0 under `python -W error`. OmegaConf 2.4 is
  needed only for the new name `register_resolver` (2.2 and 2.3 have it too, as a legacy API with
  another signature, so `hasattr` cannot tell) and for `annotation_validation`, which 2.2 and 2.3 do
  not have (they never validate annotations, which is what `"off"` selects in 2.4).
- **I3. Python 3.11 and 3.12 work with OmegaConf 2.4 [verified].** The builtin callables (`max`,
  `min`, `len`) register and resolve; `inspect.signature` is not a problem there.

#### Bugs

- **B1. `register_resolvers()` does nothing after `OmegaConf.clear_resolvers()` [verified].** The
  registry remembers what it published (`_published`) and skips an unchanged key without asking
  OmegaConf. After `OmegaConf.clear_resolvers()` (what a test suite or a notebook does to isolate
  itself), `get_default_registry().register_resolvers()` publishes nothing:
  `OmegaConf.has_resolver("hya.add")` stays `False`, and `import hya` again is a no-op (the module
  is cached). Violates P1 and P8.
- **B2. `hya.path` fails on a `Path` [verified].** `${hya.path:${hya.path:/a}}` raises
  `AttributeError: 'PosixPath' object has no attribute 'startswith'`. A path stored in the config by
  another resolver, or by `OmegaConf.create({"p": Path(...)})`, cannot be re-resolved.
- **B3. `hya.path` reads a `file:` URL loosely [verified].** `file://host/a/b` returns `/a/b`: the
  host is dropped silently. `FILE:///a/b` (the scheme is case-insensitive) is not recognised and
  returns `<cwd>/FILE:/a/b`.
- **B4. The error for a missing optional package never reaches the user [verified by reading
  `default.py`, `docs/docs/user_guide.md`].** The optional keys are registered only if
  `is_*_available()`. Without `torch`, `${hya.torch.tensor:[1]}` raises
  `UnsupportedInterpolationType: Unsupported interpolation type hya.torch.tensor`, which does not
  say that `torch` is missing. `check_torch()` (with the `pip install torch` hint) is reached only
  by calling the function directly. `docs/docs/get_started.md` promises "a helpful error message
  indicating which package needs to be installed" and the property P10 promises the same; the
  troubleshooting section of the user guide documents the opposite. Violates P10.

#### Design problems

- **D1. The registry content depends on the machine.** Because of B4, `get_default_registry().state`
  has 21 keys without numpy, torch and braceexpand and 25 with them. The documented-keys test of
  `tests/integration/test_resolvers.py` has to subtract an `OPTIONAL_KEYS` set, `default.py` has
  three `if is_*_available()` branches, and `find_spec` runs at every import to build them. Violates
  P9 as written in the target.
- **D2. `hya.default` registers resolvers when imported [reading].** The last line of
  `src/hya/default.py` is `get_default_registry().register_resolvers()`. A module that defines
  `get_default_registry` should not publish anything as a side effect. (Importing any `hya.*` runs
  `hya/__init__.py`, which imports `hya.default`, so the behaviour is the same for users; the
  location is the problem: `__init__.py` is where P1 should be visible.)
- **D3. `hya.numpy` has no `__all__` and a broken docstring [verified].** `CLAUDE.md` requires
  `__all__` in every module. The module docstring contains a stray line of code
  (`registry.register_resolvers()` and `# data: ${hya.np.array:[1, 2, 3]}` glued into the prose).
- **D4. A lazy resolver is anonymous [verified].** `register_lazy` builds a closure named `resolver`
  with the signature `(*args)` and no docstring. Tracebacks and `registry.state["hya.np.array"]` do
  not say what it is.
- **D5. Missing everyday resolvers [reading, user guide].** `hya.mul` and `hya.pow` return floats
  when an argument is a float, and OmegaConf has no `int` cast, so the user guide works around it
  (`warmup_steps: ${hya.ceildiv:${training.total_steps},10}` with an unused `warmup_ratio` key next
  to it). There is no `sum` of a list either: `hya.add` takes values, not a list (`${hya.add:${xs}}`
  returns the list). All of these are one stdlib callable each.

#### Documentation problems

- **U1.** The user guide, section "Overriding Existing Resolvers": the comment says "Without
  `replace=True`, the old resolver is kept" above a call that passes `replace=True`. The example
  resolver `first + sum(others)` fails for strings and lists (`sum` starts at `0`).
- **U2.** User guide, "Error Handling": catches `UnsupportedInterpolationType` and prints "PyTorch
  is required", which is only true because of B4. It changes with decision D2.
- **U3.** `docs/docs/migration/v0.4_to_v0.5.md` and the README table state the `>=2.4` requirement;
  both change with decision D1.
- **U4.** `docs/docs/get_started.md` says an optional resolver without its package gives a helpful
  message (false today, B4).

### 2.3 Must not regress

All current keys keep working for the documented inputs. `import hya` stays free of warnings and of
optional imports. The default registry stays a singleton; a custom `ResolverRegistry` stays
independent of it. The doctests keep running.

---

## 3. Target architecture

### 3.1 Module layout

Unchanged, except for the three edits marked below. The package is small (1,034 lines with
docstrings); the work is correctness and consistency, not restructuring.

```text
src/hya/
├── __init__.py       # exports ResolverRegistry, get_default_registry; publishes the defaults (P1)   [edited]
├── registry.py       # ResolverRegistry                                                              [edited]
├── default.py        # get_default_registry + the two tables (built-in, optional)                    [edited]
├── resolvers.py      # only resolvers with hya behaviour (add, mul, ceildiv, ...)                    [edited: path]
├── braceexpand.py    # braceexpand_resolver (guarded import + fallback)
├── numpy.py          # to_array_resolver (guarded import + fallback)                                 [edited: __all__, docstring]
├── torch.py          # to_tensor_resolver, torch_dtype_resolver (guarded import + fallback)
├── imports.py        # check_*/is_*_available (unchanged API)
├── testing.py        # pytest markers (unchanged)
└── utils/fallback/   # fake modules for the guarded imports (unchanged)
```

The guarded import with a fallback module in `hya.numpy`, `hya.torch` and `hya.braceexpand` stays:
it is a rule of `CLAUDE.md`, and the modules are imported (by a call, by the documentation build) in
environments where the package may be missing.

### 3.2 `ResolverRegistry`

The public API is already right (`register`, `register_lazy`, `register_resolvers`, `has_resolver`,
`state`). Two changes in the body.

**Publishing survives `OmegaConf.clear_resolvers()` (B1, P1, P8).** An unchanged key is skipped only
if OmegaConf still has a resolver for it:

```python
def register_resolvers(self, *, replace: bool = False) -> None:
    for key, resolver in self._state.items():
        has_resolver = OmegaConf.has_resolver(key)
        if self._published.get(key) is resolver and has_resolver:
            continue  # published by this registry and still there: nothing to do
        if has_resolver and not replace:
            warnings.warn(..., stacklevel=2)  # unchanged message
            continue
        _publish(key, resolver, replace=replace)
        self._published[key] = resolver
```

A key that another source registered after `hya` (same key, other function) is not detectable
without OmegaConf private state; it is left alone, as today.

**One publish function that works on every supported OmegaConf (I2, P14).** It is the only place
that knows about the OmegaConf version:

```python
# OmegaConf 2.4 renamed register_new_resolver to register_resolver (and validates the annotations
# at call time). 2.2 and 2.3 have no validation, which is what annotation_validation="off" selects.
_OMEGACONF_HAS_ANNOTATION_VALIDATION = tuple(map(int, omegaconf.__version__.split(".")[:2])) >= (2, 4)


def _publish(key: str, resolver: Callable[..., Any], *, replace: bool) -> None:
    if _OMEGACONF_HAS_ANNOTATION_VALIDATION:
        OmegaConf.register_resolver(key, resolver, replace=replace, annotation_validation="off")
    else:
        OmegaConf.register_new_resolver(key, resolver, replace=replace)
```

About 10 lines, two branches, both covered by a unit test (version constant patched) and by the
integration test that runs on the real installed version. Parsing `omegaconf.__version__` is enough:
it is `2.4.0`, `2.4.0.dev3`, `2.3.0`. Alternative in decision D1.

**`register_lazy` returns a named callable (D4).** The closure gets the name of its target and a
docstring that says what it imports (`resolver.__name__ = function_name`,
`resolver.__doc__ = f"Resolver {target}, imported on its first call."`). Nothing else changes: the
first call imports the module, a bad target raises `ValueError` at registration, an unknown module
or function raises on the first call.

### 3.3 Default registry: same keys everywhere (B4, D1, D2)

The optional resolvers are **always registered**, lazily. Registering costs nothing (a string and a
closure); the module (and the package) is imported on the first call. Without the package the call
reaches `check_torch()`, which raises
`RuntimeError("'torch' package is required but not installed. ... pip install torch")`; OmegaConf
reports it as
`InterpolationResolutionError: RuntimeError raised while resolving interpolation: 'torch' package is required...`
(P10). No `find_spec` runs at import (P2) and the registry is the same on every machine (P9).

```python
_BUILTINS: dict[str, Callable[..., Any]] = {
    "hya.add": resolvers.add_resolver,
    "hya.sub": operator.sub,
    ...
}

# key -> "module:function"; the package is imported on the first call, and the resolver raises
# a RuntimeError that says how to install it if the package is missing
_OPTIONAL: dict[str, str] = {
    "hya.braceexpand": "hya.braceexpand:braceexpand_resolver",
    "hya.np.array": "hya.numpy:to_array_resolver",
    "hya.torch.dtype": "hya.torch:torch_dtype_resolver",
    "hya.torch.tensor": "hya.torch:to_tensor_resolver",
}


@cache
def get_default_registry() -> ResolverRegistry:
    registry = ResolverRegistry(_BUILTINS)
    for key, target in _OPTIONAL.items():
        registry.register_lazy(key, target)
    return registry
```

`default.py` no longer imports `hya.imports` and loses the three `if` branches. The side effect
moves to `hya/__init__.py` (D2):

```python
from hya.default import get_default_registry
from hya.registry import ResolverRegistry

get_default_registry().register_resolvers()
```

### 3.4 Resolvers

**Resolvers that are exactly a stdlib callable are registered as that callable** (already the case).
The target adds the callables of D5 to the same table:

| Key         | Callable       | Example                            | Result  | Why                                                 |
| ----------- | -------------- | ---------------------------------- | ------- | --------------------------------------------------- |
| `hya.int`   | `int`          | `${hya.int:${hya.mul:100000,0.1}}` | `10000` | casts the float of a computation back to an integer |
| `hya.float` | `float`        | `${hya.float:3}`                   | `3.0`   | the opposite cast                                   |
| `hya.sum`   | `sum`          | `${hya.sum:[1,2,3]}`               | `6`     | the sum of a list; `hya.add` takes values           |
| `hya.abs`   | `abs`          | `${hya.abs:-3}`                    | `3`     | optional, same cost (decision D3)                   |
| `hya.round` | `round`        | `${hya.round:2.567,1}`             | `2.6`   | optional                                            |
| `hya.ceil`  | `math.ceil`    | `${hya.ceil:2.1}`                  | `3`     | optional                                            |
| `hya.floor` | `math.floor`   | `${hya.floor:2.9}`                 | `2`     | optional                                            |
| `hya.mod`   | `operator.mod` | `${hya.mod:7,3}`                   | `1`     | optional                                            |

All eight resolve correctly with OmegaConf 2.4 **[verified]**. `bool` and `str` are **not** added:
`bool("false")` is `True` (a trap), and `str` is what interpolation already does. Each key costs one
table row in `default.py`, one row in `docs/docs/resolvers.md`, one row of the integration table,
and no code to maintain (P4).

**Resolvers with hya behaviour stay as functions in `resolvers.py`** (`add`, `mul`, `ceildiv`, `pi`,
`iter_join`, `sha256`, `path`), unchanged except `path`.

`hya.path` (B2, B3) accepts any path-like, and reads a `file:` URL with the scheme case-insensitive,
and refuses a host it would drop:

```python
def path_resolver(path: str | os.PathLike[str]) -> Path:
    """Return the absolute path: expand ``~``, resolve, and read ``file:`` URLs."""
    path = os.fspath(path)
    url = urlparse(path)
    if url.scheme == "file":
        if url.netloc not in ("", "localhost"):
            msg = f"A file URL with a host is not supported: '{path}'"
            raise ValueError(msg)
        path = unquote(url.path)
    return Path(path).expanduser().resolve()
```

Any other string is still a plain path: `/a?b` and `/a%20b` stay as written (`urlparse` gives an
empty scheme for them). `file:rel` stays a relative path.

**Optional resolvers:** unchanged (`hya.braceexpand` returns a list, `hya.torch.dtype` lists the
sorted dtype names). `_dtype_names` drops its second `check_torch()`: it is called only by
`torch_dtype_resolver`, which already checks.

### 3.5 Dependencies and CI (I1, I2, P14)

- `pyproject.toml`: `dependencies = ["omegaconf >=2.2,<3.0"]`.
- `dev/config/package_versions.json`: `"omegaconf": ["2.2.3", "2.3.0", "2.4.0"]`, so the existing
  `ci-test-deps` job (`test-omegaconf`) runs the unit tests on the oldest, a middle and the newest
  release. No workflow change: the matrix comes from this file.
- README compatibility table and `docs/docs/migration/v0.4_to_v0.5.md`: the requirement is unchanged
  (`>=2.2`); the warning about Hydra disappears.
- `OmegaConf.register_resolver` is the only call that depends on the version (section 3.2).

### 3.6 Size effect

| File            | Now   | Target | Note                                                |
| --------------- | ----- | ------ | --------------------------------------------------- |
| `default.py`    | 91    | ~75    | no `imports`, no `if`, optional table               |
| `registry.py`   | 222   | ~240   | `_publish`, version constant, lazy name             |
| `resolvers.py`  | 249   | ~255   | `path` (fspath, scheme, host)                       |
| `numpy.py`      | 48    | ~40    | docstring fixed, `__all__`                          |
| `__init__.py`   | 16    | ~19    | the publish call                                    |
| **`src` total** | 1,034 | ~1,040 | the package is already small: no reduction expected |

---

## 4. Public API after the change

```python
import hya

hya.get_default_registry()
hya.ResolverRegistry

from hya.registry import ResolverRegistry          # unchanged
from hya.resolvers import path_resolver            # accepts os.PathLike
from hya.imports import check_numpy, is_numpy_available   # unchanged (and torch, braceexpand)
from hya.testing import numpy_available, ...        # unchanged
```

Nothing is removed. Added keys (if D3 is accepted): `hya.int`, `hya.float`, `hya.sum`, and the five
optional ones. `get_default_registry().state` now always contains the four optional keys.

---

## 5. Behaviour changes (for the release notes)

| Change                                                     | Before                                                     | After                                                                                                     |
| ---------------------------------------------------------- | ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| OmegaConf requirement                                      | `>=2.4,<3.0` (cannot be installed with `hydra-core` 1.3.x) | `>=2.2,<3.0`                                                                                              |
| `register_resolvers()` after `OmegaConf.clear_resolvers()` | publishes nothing                                          | publishes the resolvers again                                                                             |
| Optional resolver without its package                      | `UnsupportedInterpolationType` (no hint)                   | `InterpolationResolutionError` with `'torch' package is required but not installed ... pip install torch` |
| `get_default_registry().state` without numpy/torch         | 21 keys                                                    | 25 keys, same on every machine                                                                            |
| `hya.path` with a `Path` input                             | `AttributeError`                                           | accepted                                                                                                  |
| `hya.path:file://host/a`                                   | `/a` (host dropped)                                        | `ValueError`                                                                                              |
| `hya.path:FILE:///a`                                       | `<cwd>/FILE:/a`                                            | `/a`                                                                                                      |
| `hya.numpy` module                                         | no `__all__`                                               | `__all__ = ["to_array_resolver"]`                                                                         |
| New keys (D3)                                              | none                                                       | `hya.int`, `hya.float`, `hya.sum` (+ optional five)                                                       |

---

## 6. Documentation

- **Properties page**: add P14, reword P1, P2, P8, P9, P10 as in section 1, keep the **Details**
  section in step (P2 and P10 change: the optional keys are always registered; the missing package
  message comes from the resolver).
- **User guide**: fix U1 (comment and example of the override), U2 (error handling: catch
  `InterpolationResolutionError`, show the message), replace the `ceildiv` workaround of
  "Mathematical Computations" by `hya.int` (D5), add one line on `hya.sum`.
- **Get started**: U4 becomes true; keep the sentence and add the real message.
- **Migration page**: replace the "Requirements" warning by "OmegaConf `>=2.2,<3.0`"; add the rows
  of section 5.
- **`docs/docs/resolvers.md`**: add the rows of section 3.4; the `Standard Library Resolvers` table
  is the model.
- **README**: compatibility table (`omegaconf >=2.2`), "Available Resolvers" list.
- `docs/mkdocs.yml`, `refs/`: unchanged.

---

## 7. Migration plan

One branch and one PR per row, branch names per `CLAUDE.md`. Rows 3 and 4 are stacked (both edit
`default.py`); the others branch from `main`. Every PR updates the docs it touches and runs the
commands of section 8.

| #   | Branch                                        | Content                                                                                                                                                                                                         |
| --- | --------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `bugfix/republish-after-clear-resolvers`      | B1: `has_resolver` check in `register_resolvers`. Regression test with a real `OmegaConf.clear_resolvers()` (integration), checked to fail without the fix (`git stash push src`).                              |
| 2   | `bugfix/path-resolver-pathlike`               | B2, B3: `os.fspath`, scheme check, host check; unit tests for each input, regression tests, doc of `hya.path` and migration row.                                                                                |
| 3   | `refactor/register-optional-resolvers-always` | B4, D1: the `_OPTIONAL` table, no `is_*_available` in `default.py`, tests of the missing package through a real interpolation (subprocess or `monkeypatch` of `find_spec` + integration), docs U2, U4, P9, P10. |
| 4   | `refactor/publish-defaults-in-init`           | D2: move the call to `__init__.py`; D4: named lazy closure. Stacked on 3.                                                                                                                                       |
| 5   | `chore/numpy-module-all`                      | D3: `__all__` and docstring of `hya.numpy`.                                                                                                                                                                     |
| 6   | `feat/support-omegaconf-2-2`                  | I1, I2: `_publish`, `pyproject.toml`, `package_versions.json`, README, migration page, properties P14. Depends on decision D1.                                                                                  |
| 7   | `feat/add-cast-and-sum-resolvers`             | D5: table rows, docs rows, integration rows. Depends on decision D3.                                                                                                                                            |
| 8   | `docs/guide-final-pass`                       | U1 and what the others left; release `0.5.0`.                                                                                                                                                                   |

Order of value: 6 first if Hydra users matter (it unblocks the install), then 1 to 3. Rows 1, 2, 5
and 6 are independent and can be reviewed in parallel.

---

## 8. Tests and gates

Commands for every PR: `.venv/bin/ruff check src tests`, `.venv/bin/ruff format src tests`,
`.venv/bin/inv types.check`, `.venv/bin/pyright --verifytypes hya --ignoreexternal`, the unit tests
of the changed modules, `.venv/bin/python -m pytest --xdoctest src/hya`, and coverage of the changed
code (`--cov=hya --cov-report=term-missing`, 100 %).

### Tests to add (one behaviour each, `CLAUDE.md` style)

**Unit (`tests/unit/`):**

- `test_registry.py`: `register_resolvers` publishes again when `OmegaConf.has_resolver` is false
  for a published key (patched); skips an unchanged key that is still there; `_publish` calls
  `register_resolver` with `annotation_validation="off"` when the constant is true and
  `register_new_resolver` without it when false; `register_lazy` closure has the target's name and a
  docstring; one test per existing behaviour is kept.
- `test_default.py`: the registry holds the four optional keys even when `is_*_available` is patched
  to `False` (the functions are not called at all); no `hya.imports` import in `default`.
- `test_resolvers.py`: `path_resolver` with a `Path`; with `FILE:///a`; with `file://localhost/a`;
  with `file://host/a` (`pytest.raises(ValueError, match=r"with a host")`); with `file:rel`; with
  `/a?b` and `/a%20b` (still plain).
- `test_numpy.py`: nothing new (no logic).

**Integration (`tests/integration/`, no patching):**

- `test_registry.py`: after `OmegaConf.clear_resolvers()`,
  `get_default_registry().register_resolvers()` makes `${hya.add:1,2}` resolve (**regression of B1,
  fails without the fix**). The fixture must restore the resolvers it cleared.
- `test_resolvers.py`: add the new keys to the parametrized table; the existing "documented keys
  equal registered keys" test drops `OPTIONAL_KEYS` and now compares the whole registry (P9);
  `${hya.path:${hya.path:/a}}` returns `Path("/a")` (regression of B2).
- `test_default.py`: in a subprocess that hides `torch` (`sys.modules["torch"] = None`),
  `${hya.torch.tensor:[1]}` raises `InterpolationResolutionError` whose message contains
  `pip install torch` (P10, regression of B4); `import hya` still imports no optional package and
  emits no warning (P2, exists).
- A job of `ci-test-deps` on the oldest OmegaConf (`2.2.3`): the unit and integration tests pass
  (P14). This is the test of `_publish`'s second branch with the real library.

### Docs gate

`tests/integration/test_resolvers.py` already compares the keys of the registry with
`docs/docs/resolvers.md`: keep it (guards P3 and P12).

---

## 9. Decisions for the maintainers

| #   | Decision                                                                                                           | Recommendation                                                                                                                                                                                                                                                                                                                                                                  |
| --- | ------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1  | **OmegaConf range**: keep `>=2.4,<3.0` (previous decision), or support `>=2.2,<3.0` with `_publish`.               | **Support `>=2.2,<3.0`.** The previous decision was taken before Hydra 1.3.8 (2026-10-25) kept `omegaconf<2.4` and 1.4 stayed a release candidate: today a user of stable Hydra cannot install `hya` 0.5. The cost is ten lines, one constant and two CI versions. If the answer is "keep `>=2.4`": release 0.5 only after Hydra 1.4 is stable, and keep the migration warning. |
| D2  | **Optional keys**: always registered (error with the install hint), or only when the package is installed (today). | **Always registered.** It is the only way to meet P10 through an interpolation, it makes the registry identical everywhere and it removes code. The price: `has_resolver("hya.torch.tensor")` is true without torch.                                                                                                                                                            |
| D3  | **New stdlib resolvers**                                                                                           | **Adopt `int`, `float`, `sum`** (each solves a workaround in the user guide); adopt `abs`, `round`, `ceil`, `floor`, `mod` only if parity with `math` is wanted. Do not add `bool` or `str`.                                                                                                                                                                                    |
| D4  | **`file:` URL with a host**: raise `ValueError` (target) or keep dropping the host.                                | **Raise.** `file://data/x` is almost always a typo for `file:///data/x`; resolving it to `/x` is silent data loss.                                                                                                                                                                                                                                                              |
| D5  | **Release number**: ship all rows as `0.5.0`.                                                                      | Yes: the rows are small and 0.5.0a0 is not released; the migration page already exists.                                                                                                                                                                                                                                                                                         |
| D6  | **`pyright --verifytypes` locally** reports "No py.typed file found".                                              | Check the CI job; if it passes there, document `uv run` (an installed package) as the way to run it locally. Not a code change.                                                                                                                                                                                                                                                 |

---

## 10. Not covered, and rejected alternatives

- **A Hydra plugin** (`hydra_plugins/hya`, a `SearchPathPlugin`) would import `hya` at Hydra
  startup, so Hydra apps would not need `import hya` **[reading, not verified]**. Rejected for now:
  a second top-level package in the wheel, coupled to the Hydra plugin API, to remove one line the
  guide already documents (P1 says "import is enough").
- **Entry points for third-party resolver packages** (`importlib.metadata`): rejected, a user adds
  resolvers with `registry.register` in one line.
- **Caching the output of resolvers**: OmegaConf's `use_cache` exists per resolver; it is not a
  property of `hya` (not guaranteed, section 1).
- **Keeping `register_new_resolver` only**: it works on every version but emits a `UserWarning` on
  2.4 at import (verified in the previous review); P2 forbids it.
- **A registry `unregister` / `clear`**: no use case; `OmegaConf.clear_resolvers()` is B1's case and
  is handled by publishing again.
- **Making `hya.iter_join` reject a `str`** (`abc` joins to `a-b-c`): a possible footgun, but the
  behaviour is the one of `str.join(map(str, ...))`, stated in the docstring. Left as is.
- **Thread-safety, `to_yaml` of object values, Windows paths** (the classifiers list Linux and
  macOS): out of scope.

---

## Appendix: probes behind the findings

| Probe                                                                                                   | Result                                                                                      |
| ------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| `python -W error -c "import hya"`, then list `sys.modules`                                              | `import hya` 0.11 s; no `numpy`, `torch`, `braceexpand`; no warning                         |
| `OmegaConf.clear_resolvers(); get_default_registry().register_resolvers()`                              | `OmegaConf.has_resolver("hya.add")` is `False` (B1)                                         |
| `${hya.path:${hya.path:/a}}`                                                                            | `AttributeError: 'PosixPath' object has no attribute 'startswith'` (B2)                     |
| `${hya.path:file://host/a/b}`, `${hya.path:FILE:///a/b}`                                                | `/a/b`, `<cwd>/FILE:/a/b` (B3)                                                              |
| PyPI metadata of `hydra-core` 1.3.8 and 1.4.0rc3, `omegaconf`                                           | `omegaconf<2.4,>=2.2`; `omegaconf<2.5.0.dev0,>=2.4.1rc1`; OmegaConf 2.4.0 stable (I1)       |
| Python 3.11.18 and 3.12.16 with OmegaConf 2.4.0, `src` on `PYTHONPATH`                                  | `hya.max`, `hya.len`, `hya.sqrt`, `hya.add`, `hya.log`, `hya.pow` resolve (I3)              |
| OmegaConf 2.3.0 and 2.2.3, `register_resolver` mapped to `register_new_resolver`, `-W error`            | eleven resolvers including `hya.np.array`, `hya.braceexpand`, `hya.path:file:` resolve (I2) |
| `int`, `float`, `sum`, `round`, `abs`, `math.ceil`, `math.floor`, `operator.mod`, `sorted` as resolvers | all resolve; `bool("false")` is `True` (D3)                                                 |
| `.venv/bin/pytest tests/unit tests/integration --cov=hya`                                               | 249 passed, 6 skipped, 100 % coverage; `ruff`, `ty`, 24 doctests pass                       |
| `.venv/bin/pyright --verifytypes hya --ignoreexternal`                                                  | "No py.typed file found", score 0 % (not informative here, D6)                              |
