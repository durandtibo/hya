# hya: target state and the changes to reach it

This document describes the design `hya` should have, then the changes to make to the current code
(`main`, `00798b1`, 0.5.0a0) to get there. It replaces the previous review (PRs #753 to #765). The
plan of that review is now implemented (PRs #766 to #774), so this version starts from what the code
does today and lists only the distance that is left. The design follows the properties of
`docs/docs/properties.md` and the rules of `CLAUDE.md`. Its aim is a small package that is easy to
maintain: **one registry, one registration rule, thin resolvers, nothing heavy at import time, and
an install that works next to Hydra**. Breaking changes are accepted and the future state matters
more than the past one.

Evidence comes from probes run on `main` (Python 3.14 in `.venv`; Python 3.11 and 3.12 and OmegaConf
2.2.3 and 2.3.0 in throw-away environments; scripts and the prototype of section 6 kept outside the
repository). Items are tagged **[verified]** (reproduced) or **[reading]** (from the code or the
documentation). Nothing in `src`, `tests` or `docs` was changed by this review.

**The finding in one sentence:** `main` already is the target architecture; what is left is two
statements of the documentation that are false, one missing feature (a `dtype` for the array and
tensor resolvers), one quality gate that reports a false result, stale docstrings, and tests for the
properties that nothing enforces yet. No architectural change and no new breaking change is needed
(section 3.6 lists the breaking changes that were considered and rejected).

---

## 1. Properties of the package

These are the rules the package guarantees. Each one is enforced by code or by a test (section 6.2
lists the test of each property and the ones to add). The numbers are those of
`docs/docs/properties.md`. Rows marked **changed** or **new** differ from that page; section 2 says
why.

| #   | Property                   | Statement                                                                                                                                                                                                                                                                                              |
| --- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| P1  | **Import is enough**       | `import hya` publishes every default resolver to OmegaConf. No other call is needed, and `register_resolvers()` publishes them again after `OmegaConf.clear_resolvers()`.                                                                                                                              |
| P2  | **Cheap import**           | `import hya` imports neither `numpy`, `torch` nor `braceexpand` (nor the `hya` modules that import them), does not look for them on disk, and emits no warning. The module of an optional resolver is imported on the first call of that resolver.                                                     |
| P3  | **Namespaced**             | Every built-in key starts with `hya.`. Optional ones are grouped (`hya.np.*`, `hya.torch.*`). Nothing is registered outside this namespace.                                                                                                                                                            |
| P4  | **Thin resolvers**         | A resolver is a standard library callable or a function of a few lines with one documented behaviour. No hidden state, no I/O beyond what its name says (`hya.path` touches the file system).                                                                                                          |
| P5  | **Pure**                   | A resolver never modifies its arguments. Interpolating a config node into a resolver cannot change the config.                                                                                                                                                                                         |
| P6  | **Deterministic output**   | The same arguments give the same output, including inside error messages (sorted, no set order). A hash does not depend on the process (no `hash()`).                                                                                                                                                  |
| P7  | **Explicit registry**      | A `ResolverRegistry` is a plain key to callable map. `register` adds, `register_resolvers` publishes to OmegaConf. Registries are independent of each other.                                                                                                                                           |
| P8  | **Replace is explicit**    | `register_resolvers()` is idempotent and never silently keeps a stale resolver: a key that changed in the registry since it was published, or that another source registered **before** the registry published it, is skipped with a warning unless `replace=True` (**changed**: "before").            |
| P9  | **One default registry**   | `get_default_registry()` returns one process-wide registry holding the built-in resolvers. It holds the same keys on every machine, whatever packages are installed. Users extend it or create their own registry.                                                                                     |
| P10 | **Errors are OmegaConf's** | A failing resolver surfaces as `InterpolationResolutionError`. The message names the original exception and the original exception is in its `__context__` chain, **not** its `__cause__` (**changed**). `hya` adds no wrapper. A missing optional package gives an error that says how to install it. |
| P11 | **Any value out**          | A resolver may return any Python object (`Path`, `ndarray`, `Tensor`, `dtype`, list). Such values are for use in code and are not meant for `OmegaConf.to_yaml`.                                                                                                                                       |
| P12 | **Typed and documented**   | `py.typed`, `pyright --verifytypes` at 100 %, every public name documented with a doctest, every resolver listed in `docs/` with its signature and one example.                                                                                                                                        |
| P13 | **Keyword-only options**   | The options of the Python API are keyword-only (`exist_ok`, `replace`). The arguments of a resolver are positional: the interpolation grammar has no keyword syntax. An optional argument of a resolver comes last and has a default (**changed**: clarified).                                         |
| P14 | **Installs next to Hydra** | `hya` accepts every OmegaConf release that a Hydra release accepts (`omegaconf >=2.2,<3.0`), on Python 3.11 and later. CI runs the tests on the oldest and the newest OmegaConf.                                                                                                                       |
| P15 | **Composable**             | A resolver accepts the values OmegaConf gives it (`str`, `int`, `float`, `bool`, `None`, `list`, `dict`, `ListConfig`, `DictConfig`) and the output of another `hya` resolver (a `Path` for `hya.path`, a `torch.dtype` for `hya.torch.tensor`) (**new**).                                             |

**Not guaranteed:** thread-safety of registering while OmegaConf resolves (OmegaConf's registry is a
global dict); caching of resolver outputs (OmegaConf default: none); support of
`OmegaConf.to_yaml(resolve=True)` for object-valued resolvers (P11); detection of a resolver that
another source registered **after** `hya` published the same key (section 2.2, G5); the textual form
of `hya.sha256` for an input whose `str()` OmegaConf changes (the hash is of `str(obj)`, so two
mappings with the same items in another order have different hashes).

---

## 2. Where `main` stands

### 2.1 Done since the previous review

| Item of the previous plan                                        | State                                                            |
| ---------------------------------------------------------------- | ---------------------------------------------------------------- |
| Accept `omegaconf >=2.2,<3.0`; one `_publish` for 2.2 to 2.4     | done (#766); CI matrix `2.2.3`, `2.3.0`, `2.4.0` in `dev/config` |
| `register_resolvers()` publishes again after `clear_resolvers()` | done (#767), regression test                                     |
| `hya.path` accepts a path-like, checks the host of a file URL    | done (#768)                                                      |
| `__all__` and docstring of `hya.numpy`                           | done (#769)                                                      |
| Optional resolvers always registered, same keys everywhere       | done (#770): 28 keys on every machine, no `find_spec` at import  |
| Defaults published in `__init__.py`, named lazy resolvers        | done (#771)                                                      |
| `hya.int`, `hya.float`, `hya.sum`                                | done (#773)                                                      |
| Override example of the user guide                               | done (#774)                                                      |

Gates on `main` **[verified]**: 283 tests pass, 6 are skipped (the tests of the missing-package case: all three optional packages are installed), coverage of `src` is 100 %, `ruff check` and `ty` pass, 25 doctests pass. `import hya`
takes 66 ms in total (27 ms of it is OmegaConf) and imports no optional package. `src` is 1,058
lines, about 200 of them executable; the rest is docstrings. `hya` works with OmegaConf 2.2.3,
2.3.0 and 2.4.0 and with Python 3.11, 3.12 and 3.14 under `python -W error` **[verified]**.

Probed and **correct**, so not to be touched: the 28 keys resolve for the documented inputs, with
config nodes as input (`ListConfig` into `hya.np.array`, `hya.torch.tensor`, `hya.max`, `hya.sum`,
`hya.len`, `hya.iter_join`, `hya.sha256`, `hya.add`), `hya.add` returns a new list and leaves
`conf.x` unchanged, `hya.path` accepts a `Path` and a `file://localhost/` URL, errors of the standard
library resolvers are the errors of the standard library, the dtype error lists the sorted names.

### 2.2 What is still wrong

#### False statements of the documentation

- **G1. P10 says "the original error as cause", and it is not [verified].** For
  `${hya.ceildiv:1,0}`, OmegaConf raises `InterpolationResolutionError` with `__cause__ is None`;
  the chain is `InterpolationResolutionError` (`__context__`) → `InterpolationResolutionError`
  (`__context__`) → `ZeroDivisionError`. The message does name the original type ("ZeroDivisionError
  raised while resolving interpolation"). The sentence is in `docs/docs/properties.md` (P10) and in
  the "Error Handling" section of `docs/docs/user_guide.md`. No test checks it (`grep cause tests`
  is empty). Violates P10 as written.
- **G2. `hya.ceildiv` says it is `math.ceil(dividend / divisor)` [verified].** For ints it is (and
  exact for big ints). For floats it returns a float: `${hya.ceildiv:11.0,4}` is `3.0`, while
  `math.ceil(11.0 / 4)` is `3`. The docstring and `docs/docs/resolvers.md` should say that the type
  of the result follows `//`.
- **G3. Two module docstrings describe the registration of before #770 [reading].**
  `hya/torch.py` ("The resolvers are registered only if the `torch` package is available") and
  `hya/braceexpand.py` ("The resolver is registered only if the `braceexpand` package is
  available"). The resolvers are always registered. `hya/numpy.py` was fixed, these two were
  missed. They are rendered by mkdocstrings in the reference.
- **G4. P8 promises more than the code can do [verified].** After `OmegaConf.clear_resolvers()`, if
  another source registers `hya.add` and then `get_default_registry().register_resolvers()` runs,
  the registry sees `_published["hya.add"] is resolver` and `OmegaConf.has_resolver` true, and
  skips the key **silently**: the other source's resolver stays, with no warning. Detecting it
  needs the private `BaseContainer._resolvers` of OmegaConf (the public API has no
  `get_resolver` in 2.4 and the stored value is a wrapper, not the function). The case needs a
  `clear_resolvers()` and an unrelated registration of a `hya.*` key between two `hya` calls;
  the registration made **before** `hya` is detected and warned (test
  `test_register_resolvers_key_of_another_source_is_not_replaced`). The fix is the wording of P8,
  not code (decision D5).

#### Missing feature

- **G5. The array and tensor resolvers cannot take a dtype [verified].**
  `${hya.torch.tensor:[1,2],${hya.torch.dtype:float32}}` raises
  `TypeError: to_tensor_resolver() takes 1 positional argument but 2 were given`. `hya.torch.dtype`
  exists next to `hya.torch.tensor` for this use, yet the two cannot be combined; a config that
  needs a `float32` tensor has to cast in code. The grammar has no keyword argument
  (`${hya.np.array:[1,2],dtype=float}` is a `GrammarParseError`), so the dtype must be a second
  positional argument. The change is not breaking: one argument is added after `data`, with a
  default.

#### Gates and tests

- **G6. `pyright --verifytypes` reports a false result as documented [verified].**
  `.venv/bin/pyright --verifytypes hya --ignoreexternal` (the command of `CLAUDE.md`) prints
  `error: No py.typed file found`, `Symbols exported by "hya": 0` and a score of 0 %, although
  `src/hya/py.typed` exists. The same command with the environment activated
  (`VIRTUAL_ENV=$PWD/.venv PATH=$PWD/.venv/bin:$PATH`) finds `src/hya`, exports 38 symbols and scores
  100 %; a non-editable install in another environment gives the same 100 %. `--pythonpath` does not
  help. So P12 holds, but the documented command does not prove it. Whether `inv types.check
--complete` (the CI job) runs `--verifytypes` with an activated environment is **not verified**:
  `invoke-tasklib` has no `verifytypes` string in the installed package.
- **G7. Four properties have no test that would fail if they were broken [reading, `grep` of
  `tests/`].** P3 (every key starts with `hya.`), P10 (the chain of G1), P15 (a `hya` output as
  the input of a `hya` resolver; only `hya.path` of `hya.path` is in the doctest), and P5 for
  the resolvers other than `hya.add` (`hya.mul`, `hya.iter_join`, `hya.sha256` on a config node).

### 2.3 Must not regress

All current keys keep working for the documented inputs. `import hya` stays free of warnings and of
optional imports (P2). The default registry stays a singleton with the same keys on every machine
(P9); a custom `ResolverRegistry` stays independent of it (P7). The doctests keep running.

---

## 3. Target architecture

### 3.1 Module layout

Unchanged. The package is small and each module has one role.

```text
src/hya/
├── __init__.py       # exports ResolverRegistry, get_default_registry; publishes the defaults (P1)
├── registry.py       # ResolverRegistry, _publish (the only place that knows the OmegaConf version)
├── default.py        # get_default_registry + the two tables (built-in, optional)
├── resolvers.py      # the resolvers with a hya behaviour: add, mul, ceildiv, pi, iter_join, sha256, path
├── braceexpand.py    # braceexpand_resolver (guarded import + fallback)             [docstring]
├── numpy.py          # to_array_resolver (guarded import + fallback)                [dtype]
├── torch.py          # to_tensor_resolver, torch_dtype_resolver (guarded import)    [dtype, docstring]
├── imports.py        # check_*/is_*_available
├── testing.py        # pytest markers for the optional packages (test support, imports pytest)
├── py.typed
└── utils/fallback/   # fake modules for the guarded imports
```

The guarded import with a fallback module in the three optional modules stays: it is a rule of
`CLAUDE.md`, and the modules are imported without their package by the documentation build
(mkdocstrings) and by a user who imports `hya.numpy` directly. The three mechanisms
(`is_*_available`, `check_*`, fallback) have each one job: choose the import, give the install hint,
keep the module importable (decision D6).

### 3.2 `ResolverRegistry`

The public API is final: `register`, `register_lazy`, `register_resolvers`, `has_resolver`, `state`
(read-only). Nothing changes in the code. The rules that the code follows:

1. `register(key, *, exist_ok=False)` is a decorator factory, so `registry.register("k")(fn)` is
   also the call form. A second registration of a key raises `RuntimeError` unless `exist_ok=True`.
2. `register_lazy(key, target, *, exist_ok=False)` registers a named callable that imports
   `"module:function"` on its first call. The callable takes `*args`: the arity is checked by the
   target at the call, which is why the signature does not show it (accepted: OmegaConf does not
   read it, because `annotation_validation` is `"off"`).
3. `register_resolvers(*, replace=False)` is idempotent and publishes through `_publish`, the single
   function that depends on the OmegaConf version (`register_resolver(..., annotation_validation=
"off")` from 2.4, `register_new_resolver` before). It skips a key that is unchanged and still in
   OmegaConf, skips with a warning a key that OmegaConf has from another source, and replaces only
   with `replace=True` (P8).

The wording of P8 changes to say "registered before" (G4); the limit is listed in "Not guaranteed".

### 3.3 Default registry

Unchanged: `_BUILTINS` (24 keys: 17 standard library callables, 7 functions of `resolvers.py`) and
`_OPTIONAL` (4 lazy keys) are two tables; `get_default_registry()` is a `@cache` function that builds
the registry from them; `hya/__init__.py` publishes it. The complete catalogue of the target:

| Group              | Keys                                                                                                                        | Implementation                                  |
| ------------------ | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- |
| Operators          | `hya.sub`, `hya.truediv`, `hya.floordiv`, `hya.neg`, `hya.pow`                                                              | `operator.*`                                    |
| Math               | `hya.sqrt`, `hya.exp`, `hya.log`, `hya.log10`, `hya.sinh`, `hya.asinh`                                                      | `math.*`                                        |
| Builtins           | `hya.max`, `hya.min`, `hya.len`, `hya.sum`, `hya.int`, `hya.float`                                                          | the builtin itself                              |
| Behaviour of `hya` | `hya.add`, `hya.mul` (do not modify the first argument), `hya.ceildiv`, `hya.pi`, `hya.iter_join`, `hya.sha256`, `hya.path` | functions of `resolvers.py`, 3 to 10 lines each |
| Optional (lazy)    | `hya.braceexpand`, `hya.np.array`, `hya.torch.tensor`, `hya.torch.dtype`                                                    | `hya.braceexpand`, `hya.numpy`, `hya.torch`     |

A resolver is added to this catalogue when a configuration needs it **and** no composition of the
existing keys gives it (decision D2 applies this rule to `abs`, `round`, `ceil`, `floor`, `mod`).
Every key costs one table row, one row of `docs/docs/resolvers.md` and one row of the integration
table of `tests/integration/test_resolvers.py` (which fails if a key is undocumented).

### 3.4 Resolvers with a `hya` behaviour

Unchanged, except the docstring of `hya.ceildiv` (G2):

```python
def ceildiv_resolver(dividend: float, divisor: float) -> float:
    r"""Compute the ceiling division of two numbers.

    The type of the result follows ``//``: an ``int`` for two integers (exact, whatever their size)
    and a ``float`` if one of them is a float (``11.0, 4`` gives ``3.0``).
    """
    return -(dividend // -divisor)
```

### 3.5 Optional resolvers: a `dtype` argument (G5, P13, P15)

The array and tensor resolvers take the dtype as an optional second argument. `dtype=None` is the
current behaviour, so the change is not breaking.

```python
# hya/numpy.py
def to_array_resolver(data: ArrayLike, dtype: str | None = None) -> np.ndarray:
    check_numpy()
    return np.array(data, dtype=dtype)


# hya/torch.py
def to_tensor_resolver(data: Any, dtype: torch.dtype | None = None) -> torch.Tensor:
    check_torch()
    return torch.tensor(data, dtype=dtype)
```

```yaml
weights: ${hya.np.array:[1,2,3],float32} # array([1., 2., 3.], dtype=float32)
mask: ${hya.torch.tensor:[1,0,1],${hya.torch.dtype:bool}} # tensor([ True, False,  True])
```

For numpy the dtype is the string that `np.array(dtype=...)` accepts, so no `hya.np.dtype` resolver
is needed. For torch the dtype is a `torch.dtype`, which is the output of `hya.torch.dtype`
(P15): the two resolvers compose and nothing else is added. `hya.torch.dtype` keeps its contract:
the name of an attribute of `torch` (`float32`, not `torch.float32`), the error lists the sorted
names (decision D3). `hya.braceexpand` and `hya.np.array`/`hya.torch.tensor` without `dtype` are
unchanged. The module docstrings of `hya.torch` and `hya.braceexpand` stop saying that the
resolvers are registered only if the package is available (G3).

### 3.6 Breaking changes considered and rejected

The brief allows breaking changes; none improves the package enough to pay its migration cost.

| Candidate                                                       | Why not                                                                                                                                |
| --------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- |
| `register(key, "module:function")` instead of `register_lazy`   | One function with two behaviours chosen by the type of an argument; the error messages of both get worse. `register_lazy` is 10 lines. |
| Remove `has_resolver` (use `key in registry.state`)             | It mirrors `OmegaConf.has_resolver`, costs 3 lines and is in the user guide. Removing it breaks code for no maintenance gain.          |
| Remove `check_*`, `is_*_available` and `utils.fallback`         | The install hint of P10 and the importable modules of section 3.1 need them; the rule is in `CLAUDE.md`.                               |
| Wrap resolver errors in a `hya` exception                       | Violates P10 and adds a layer between the user and the real error.                                                                     |
| Canonical (key-sorted) form for `hya.sha256` of a mapping       | The resolver is `str(obj)` on purpose (P4). A user who needs order-insensitivity sorts the keys in the configuration.                  |
| A `hya.np.dtype` resolver                                       | The string accepted by numpy is enough (section 3.5).                                                                                  |
| Eager registration of built-ins and lazy only for optional ones | Already the design; making the built-ins lazy too would cost an indirection per resolver for no import time gain (they are stdlib).    |

### 3.7 Dependencies and CI

Unchanged: `dependencies = ["omegaconf >=2.2,<3.0"]`, optional extras `braceexpand`, `numpy`,
`torch` read from `pyproject.toml`, the matrix of `dev/config/package_versions.json`
(`omegaconf` 2.2.3, 2.3.0, 2.4.0). One change in the gates (G6, section 5, PR 3): the
`--verifytypes` command must run with an activated environment, in `CLAUDE.md` and in the
`inv types.check --complete` job.

---

## 4. Public API after the change

```python
import hya

hya.ResolverRegistry
hya.get_default_registry()

registry = hya.get_default_registry()
registry.register(key, *, exist_ok=False)          # decorator factory
registry.register_lazy(key, target, *, exist_ok=False)
registry.register_resolvers(*, replace=False)
registry.has_resolver(key)
registry.state                                      # read-only mapping
```

| Item                         | Before                      | After                                                            |
| ---------------------------- | --------------------------- | ---------------------------------------------------------------- |
| `hya.np.array`               | `${hya.np.array:[1,2]}`     | same, and `${hya.np.array:[1,2],float32}`                        |
| `hya.torch.tensor`           | `${hya.torch.tensor:[1,2]}` | same, and `${hya.torch.tensor:[1,2],${hya.torch.dtype:float32}}` |
| `hya.np.array` signature     | `(data)`                    | `(data, dtype=None)`                                             |
| `hya.torch.tensor` signature | `(data)`                    | `(data, dtype=None)`                                             |
| Everything else              | unchanged                   | unchanged                                                        |

No key is removed, renamed or changed in behaviour. The migration page (`v0.4_to_v0.5.md`) gets one
row for the new `dtype` argument and no other row.

---

## 5. Changes to reach the target state

One branch and one pull request per logical change, each small and independent (no stack): they
touch different files, except the properties page, which only PR 1 edits.

| PR  | Branch                           | Change                                                                                                                                                                                                                                                                                                                                                               |
| --- | -------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `docs/fix-false-statements`      | G1: P10 of `properties.md` and the "Error Handling" section of `user_guide.md` (message names the exception, `__context__` chain). G2: docstring of `ceildiv_resolver` and its entry in `resolvers.md`. G3: module docstrings of `hya.torch` and `hya.braceexpand`. G4: wording of P8 and "Not guaranteed". P13 clarification, new P15, P12 (`--verifytypes` 100 %). |
| 2   | `test/enforce-properties`        | G7: the tests of section 6.2 (P3, P10, P15, P5). No change in `src`. Run them against `main` first: they must pass, because the code is right and only the documentation was wrong (the P10 test asserts the chain, so it fails if OmegaConf changes it).                                                                                                            |
| 3   | `feat/add-dtype-to-array-tensor` | G5: `dtype` argument of `to_array_resolver` and `to_tensor_resolver`, docstrings with a doctest, rows in `resolvers.md` and the user guide ("Data Type Specifications"), one row in the migration page, unit and integration tests of section 6.1.                                                                                                                   |
| 4   | `chore/verify-types-gate`        | G6: fix the command in `CLAUDE.md` (activated environment), and check what `inv types.check --complete` runs; if it does not run `--verifytypes` against an activated environment, make it do so. The PR description says which of the two cases it found.                                                                                                           |
| 5   | `chore/release-0-5-0`            | Version `0.5.0` in `pyproject.toml`, final migration page, tag `v0.5.0` (an exact tag; no floating tag). Done by the maintainer after PRs 1 to 4 are merged and CI is green.                                                                                                                                                                                         |

PRs 1 and 2 can be merged in any order; PR 3 should follow PR 1 (it edits the same docs pages).

---

## 6. Tests and gates

### 6.1 Tests for PR 3 (`dtype`)

Unit tests, one behaviour each, in `tests/unit/test_numpy.py` and `tests/unit/test_torch.py`:

- `to_array_resolver([1, 2])` has the default dtype (`int64`), `dtype=None` gives the same array.
- `to_array_resolver([1, 2], "float32")` has dtype `float32`, and the whole array equals
  `array([1.0, 2.0], dtype=float32)`.
- `to_array_resolver([1, 2], "nope")` raises `TypeError` (`match=r"data type 'nope' not understood"`).
- `to_tensor_resolver([1, 2])` has dtype `torch.int64`; with `torch.float32` it has `torch.float32`.
- Without the package, both raise the `RuntimeError` of `check_*` whatever `dtype` is (existing tests,
  patched `is_*_available`).

Integration tests (real OmegaConf, no patching) in `tests/integration/`:

- `${hya.np.array:[1,2],float32}` resolves to a `float32` array.
- `${hya.torch.tensor:[1,2],${hya.torch.dtype:float32}}` resolves to a `float32` tensor (the test
  that fails on `main` with the `TypeError` of G5; check it fails with `git stash push src`).
- `${hya.torch.tensor:${x},${hya.torch.dtype:float64}}` with `x: [1, 2]` does not modify `conf.x`.

### 6.2 Test of each property

| #   | Existing test (file `tests/integration/` unless said)                                                                                                                                   | To add (PR 2)                                                          |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------- |
| P1  | `test_registry::test_register_default_resolvers_after_clear_resolvers`, `test_default::test_import_hya_publishes_the_default_resolvers`                                                 |                                                                        |
| P2  | `test_default::test_import_hya_does_not_import_optional_packages`, `..._modules`, `test_registry::test_import_hya_emits_no_warning`                                                     |                                                                        |
| P3  |                                                                                                                                                                                         | every key of the default registry starts with `hya.`                   |
| P4  | review (a resolver of more than a few lines needs a reason in the PR)                                                                                                                   |                                                                        |
| P5  | `test_resolvers::test_add_resolver_does_not_modify_config_list`                                                                                                                         | `hya.mul`, `hya.iter_join`, `hya.sha256` leave the node unchanged      |
| P6  | `test_torch::test_dtype_resolver_error_lists_the_sorted_names`                                                                                                                          |                                                                        |
| P7  | `tests/unit/test_registry.py::test_resolver_registry_register_resolvers_registries_are_independent`                                                                                     |                                                                        |
| P8  | `test_registry::test_register_resolvers_override_warns`, `..._replace`, `..._twice_is_silent`, `..._key_of_another_source_is_not_replaced`                                              |                                                                        |
| P9  | `test_default::test_default_registry_keys_do_not_depend_on_the_installed_packages`                                                                                                      |                                                                        |
| P10 | `test_default::test_missing_package_error_says_how_to_install_it`, `test_resolvers::test_stdlib_resolver_error_is_the_error_of_the_stdlib`                                              | the original exception is in the `__context__` chain of the error      |
| P11 | `test_braceexpand::test_braceexpand_resolver_can_be_dumped` (the list case)                                                                                                             |                                                                        |
| P12 | `test_resolvers::test_default_resolvers_are_documented`, `test_documented_resolvers_exist`, the doctests, `--verifytypes`                                                               |                                                                        |
| P13 | `tests/unit/test_registry.py::test_resolver_registry_register_exist_ok_is_keyword_only`, `..._register_lazy_exist_ok_is_keyword_only`, `..._register_resolvers_replace_is_keyword_only` |                                                                        |
| P14 | CI matrix `ci-test-deps` (OmegaConf 2.2.3, 2.3.0, 2.4.0)                                                                                                                                |                                                                        |
| P15 | `hya.path` of `hya.path` (doctest)                                                                                                                                                      | `hya.add` of two config lists; `hya.torch.tensor` of `hya.torch.dtype` |

### 6.3 Gates (all of `CLAUDE.md`)

```shell
.venv/bin/ruff check src tests && .venv/bin/ruff format src tests
.venv/bin/inv types.check
VIRTUAL_ENV=$PWD/.venv PATH=$PWD/.venv/bin:$PATH .venv/bin/pyright --verifytypes hya --ignoreexternal
.venv/bin/pytest tests/unit tests/integration -q --cov=hya --cov-report=term-missing
.venv/bin/python -m pytest --xdoctest src/hya
```

Expected after the five PRs: ruff and ty clean, `--verifytypes` at 100 % (38 symbols, no new
public name), coverage 100 %, doctests pass, and the tests of PR 2 and PR 3 added. The CI matrix
runs the unit tests on OmegaConf 2.2.3, 2.3.0 and 2.4.0.

---

## 7. Evidence: a prototype of the `dtype` change

Throw-away copy of `src/hya` with the two edits of section 3.5, run with `python -W error`:

| OmegaConf | Python | `${hya.np.array:${x},float32}` | `${hya.torch.tensor:${x},${hya.torch.dtype:float32}}` | `${hya.np.array:[1,2]}` (no dtype) |
| --------- | ------ | ------------------------------ | ----------------------------------------------------- | ---------------------------------- |
| 2.2.3     | 3.12   | `float32` array                | `tensor([1., 2.])`                                    | `int64` array                      |
| 2.3.0     | 3.12   | `float32` array                | `tensor([1., 2.])`                                    | `int64` array                      |
| 2.4.0     | 3.14   | `float32` array                | `tensor([1., 2.])`                                    | `int64` array                      |

The size of the change is 2 changed signatures and 2 changed return lines. The real `src` also
passes `python -W error` on OmegaConf 2.2.3 with Python 3.11 (`hya.add`, `hya.int`, `hya.max`).

Probes behind section 2.2 (Python 3.14, OmegaConf 2.4.0):

| Probe                                                            | Result                                                                                 |
| ---------------------------------------------------------------- | -------------------------------------------------------------------------------------- |
| `${hya.ceildiv:1,0}`, then walk `__cause__` and `__context__`    | `__cause__` is `None`; chain: 2 × `InterpolationResolutionError` → `ZeroDivisionError` |
| `${hya.ceildiv:11.0,4}`                                          | `3.0` (`float`)                                                                        |
| `${hya.torch.tensor:[1,2],${hya.torch.dtype:float32}}` on `main` | `TypeError ... takes 1 positional argument but 2 were given`                           |
| `${hya.np.array:[1,2],dtype=float}`                              | `GrammarParseError` at `=`: the grammar has no keyword argument                        |
| `hya.add` registered by another source after `clear_resolvers()` | `register_resolvers()` is silent, the other resolver stays                             |
| `pyright --verifytypes hya --ignoreexternal` as in `CLAUDE.md`   | `No py.typed file found`, 0 symbols, 0 %                                               |
| same command with `VIRTUAL_ENV` and `PATH` set to `.venv`        | `src/hya` found, 38 symbols, 100 %                                                     |
| `${hya.torch.dtype:nope}`                                        | error of 685 characters listing 56 sorted dtype names                                  |

---

## 8. Decisions for the maintainers

Each has a recommendation; the target state above assumes the recommended answer.

| #   | Question                                                                          | Recommendation                                                                                                                                                    |
| --- | --------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1  | Add the `dtype` argument to `hya.np.array` and `hya.torch.tensor`?                | **Yes.** Not breaking, 4 changed lines, and it makes `hya.torch.dtype` useful next to `hya.torch.tensor`.                                                         |
| D2  | Add `hya.abs`, `hya.round`, `hya.ceil`, `hya.floor`, `hya.mod`?                   | **No for now.** Each is one stdlib callable, but nothing in the documentation needs one. Apply the rule of section 3.3 when a configuration does.                 |
| D3  | Should `hya.torch.dtype` also accept `torch.float32`?                             | **No.** Two spellings for one thing break P4; the error already lists the valid names.                                                                            |
| D4  | Should `hya.ceildiv` always return an `int`?                                      | **No.** `-(a // -b)` is exact and follows `//`; document the type (G2). `${hya.int:${hya.ceildiv:x,y}}` gives an `int` for floats.                                |
| D5  | Detect a resolver registered by another source after `hya` published?             | **No.** It needs the private `BaseContainer._resolvers`, which changes between OmegaConf releases (P14). Reword P8 and list it in "Not guaranteed".               |
| D6  | Drop `check_*` and the fallback modules?                                          | **No** (section 3.6). Revisit if `CLAUDE.md` stops requiring the guarded import.                                                                                  |
| D7  | Register the resolvers through a Hydra plugin so that `import hya` is not needed? | **Not now.** It adds a `hydra_plugins` namespace package and a dependency on Hydra internals for a gain of one import line; P1 (import is enough) is already met. |
| D8  | Where does the `--verifytypes` fix live (G6)?                                     | In `CLAUDE.md` and in the `inv types.check` task, whichever PR 4 finds missing. Do not add a `type: ignore` or lower the score: the 0 % is a wrong invocation.    |

---

## 9. Not covered

- **Thread-safety.** OmegaConf's resolver registry is a global dictionary; `hya` does not lock it.
- **Windows.** The package classifiers are Linux and macOS; `hya.path` is tested with POSIX paths.
- **YAML dump of object-valued resolvers (P11).** Use the value in code or
  `OmegaConf.to_container(cfg, resolve=True)`.
- **Resolver output cache.** OmegaConf caches resolved nodes; `replace=True` does not clear the
  cache of existing configurations (`OmegaConf.clear_cache(cfg)`), documented.
- **Keyword arguments in an interpolation.** The grammar of OmegaConf has none; positional only.
- **The Hydra release matrix.** P14 is checked against OmegaConf releases (2.2.3, 2.3.0, 2.4.0), not
  against Hydra itself; the Hydra examples of the user guide are not run in CI.
- **Performance.** A resolver is called once per resolution; nothing in `hya` is on a hot path, and
  no benchmark was made.

---

## Appendix: size of the package

| Item                         | Lines  | Note                                               |
| ---------------------------- | ------ | -------------------------------------------------- |
| `registry.py`                | 263    | `_publish`, `ResolverRegistry` (5 public members)  |
| `resolvers.py`               | 266    | 7 functions                                        |
| `imports.py`                 | 142    | 6 functions (3 packages)                           |
| `torch.py`                   | 113    | 3 functions                                        |
| `default.py`                 | 96     | 2 tables, `get_default_registry`                   |
| `braceexpand.py`, `numpy.py` | 65, 48 | 1 function each                                    |
| `testing.py`, `__init__.py`  | 46, 19 | pytest markers, exports                            |
| Top-level modules, total     | 1,058  | about 200 executable lines, the rest is docstrings |

`utils/` adds 6 lines and the three fallback modules about a dozen each. After the change: +2
signatures, +0 modules.

The target adds no module and no public name; the work is the correctness of the documentation, one
optional argument, and tests.
