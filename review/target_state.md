# hya: target state and the changes to reach it

This document proposes a target state for the `hya` package (0.4.0 → 0.5.0, breaking changes
accepted) and a plan of small pull requests to reach it. The aim: **one registry, one
registration rule, thin resolvers, nothing heavy at import time**.

Evidence comes from probes run on `main` (commit `08207d9`, Python 3.14, OmegaConf 2.4.0, numpy
and torch installed). Items are tagged **[verified]** (reproduced) or **[reading]** (from the
code).

---

## 0. Constraints

1. **Simple and easy to maintain.** The package is 1,334 lines of `src`, 573 of them in
   `resolvers.py`, most of which wrap one stdlib call. Remove code instead of adding layers.
2. **Breaking changes are fine.** No compatibility shims for our own API, no deprecation period.
   The future state matters more than the past one.
3. **Follow `CLAUDE.md`.** Lazy optional imports, `from __future__ import annotations` and
   `__all__` in every module, keyword-only options, Google docstrings with doctests, one
   behaviour per test, 100% coverage, patched tests backed by integration tests.
4. **OmegaConf requires `>=2.4,<3.0`** (maintainer decision). The target uses the 2.4 API
   (`OmegaConf.register_resolver`) with no compatibility shim, and `dev/config/package_versions.json`
   keeps only the 2.4 versions. Consequence: users must have a Hydra release that accepts
   OmegaConf 2.4 (`hydra-core` 1.3 declares `<2.4` **[reading, to verify]**); say so in the
   release notes.
5. **Optional libraries** (`braceexpand`, `numpy`, `torch`) stay optional and are managed as in
   `coola`: `is_*_available` / `check_*` in `hya.imports`, a guarded import with a
   `hya.utils.fallback` module in the module that uses the library, and **lazy registration** of
   the optional resolvers (section 3.4). Missing package ⇒ the resolver is not registered.
6. **Release.** The next stable release is 0.5.0 (`pyproject.toml` is at `0.5.0a0`; the last
   release is 0.4.0). The request said "0.0.5"; read as a typo, to confirm.

---

## 1. Properties of the package

These are the rules the package guarantees. Each one is enforced by code or by a test (section 8).
Where `main` violates one, section 2 says so.

| #   | Property                    | Statement                                                                                                                                                               |
| --- | --------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P1  | **Import is enough**        | `import hya` registers every available default resolver with OmegaConf. No other call is needed.                                                                        |
| P2  | **Cheap import**            | `import hya` imports neither `numpy`, `torch` nor `braceexpand`, and emits no warning. The module of an optional resolver is imported on the first call of that resolver.  |
| P3  | **Namespaced**              | Every built-in key starts with `hya.`. Optional ones are grouped (`hya.np.*`, `hya.torch.*`). Nothing is registered outside this namespace.                             |
| P4  | **Thin resolvers**          | A resolver is a stdlib function or a function of a few lines with one documented behaviour. No hidden state, no I/O beyond what its name says (`hya.path` touches the file system).     |
| P5  | **Pure**                    | A resolver never modifies its arguments. Interpolating a config node into a resolver cannot change the config.                                                           |
| P6  | **Deterministic output**    | Same arguments ⇒ same output, including inside error messages (sorted, no set order).                                                                                   |
| P7  | **Explicit registry**       | A `ResolverRegistry` is a plain key → callable map. `register` adds, `register_resolvers` publishes to OmegaConf. Registries are independent of each other.              |
| P8  | **Replace is explicit**     | `register_resolvers()` is idempotent. It never silently keeps a stale resolver: a key that changed since it was published, or that another source registered, is skipped with a warning unless `replace=True`. |
| P9  | **One default registry**    | `get_default_registry()` returns one process-wide registry holding the built-in resolvers. Users extend it or create their own registry.                                  |
| P10 | **Errors are OmegaConf's**  | A failing resolver surfaces as `InterpolationResolutionError` with the original error as cause. `hya` adds no wrapper of its own. A missing optional package says how to install it. |
| P11 | **Any value out**           | A resolver may return any Python object (`Path`, `ndarray`, `Tensor`, `dtype`, list). Such values are for use in code and are not meant for `OmegaConf.to_yaml`.        |
| P12 | **Typed and documented**    | `py.typed`, `pyright --verifytypes` clean, every public name documented with a doctest, every resolver listed in `docs/` with its signature and one example.             |
| P13 | **Keyword-only options**    | Options are keyword-only (`exist_ok`). Positional arguments are the data.                                                                                               |

**Not guaranteed:** thread-safety of registering while OmegaConf resolves (OmegaConf's registry is
a global dict); caching of resolver outputs (OmegaConf default: none); support of
`OmegaConf.to_yaml(resolve=True)` for object-valued resolvers (P11).

---

## 2. Findings on the current code

### Bugs (behaviour is wrong)

- **B1. `hya.add` modifies its first argument [verified].** The loop is `output += arg`. With
  `x: [1, 2]` and `k: ${hya.add:${x},[3]}`, reading `conf.k` gives `[1, 2, 3]` **and `conf.x`
  becomes `[1, 2, 3]`**. `hya.mul` has the same pattern (`output *= arg`). Violates P5.
- **B2. Overriding a resolver silently does nothing [verified].** `registry.register("hya.add",
  exist_ok=True)` then `registry.register_resolvers()` leaves the old resolver: `register_resolvers`
  skips every key for which `OmegaConf.has_resolver(key)` is true (`registry.py:142`), and the
  built-ins were registered at import. The user guide shows exactly this as a feature
  ("Overriding Existing Resolvers"). Violates P8.
- **B3. `hya.to_path` truncates paths [verified].** It parses its input as a URL:
  `${hya.to_path:/a?b}` returns `/a` (the `?b` is read as a query). `${hya.to_path:http://h/p}`
  silently returns `/p`. `hya.path` and `hya.to_path` differ only by this URL step, and
  `hya.path:/a%20b` keeps `%20` while `hya.to_path:/a%20b` decodes it. Two near-identical
  resolvers with different quoting rules.
- **B4. `hya.torch.dtype` error message is unordered [verified].** The message embeds a `set` of
  dtypes, so the order changes between runs. Violates P6.

### Design problems

- **D1. `import hya` is slow [verified].** 0.59 s, of which 0.52 s is `import torch`.
  `hya.torch` and `hya.numpy` import their library at module level when it is installed
  (`if TYPE_CHECKING or is_torch_available(): import torch`), and `hya.default` imports those
  modules. Violates P2. `coola` has the same guarded import in its modules but never imports
  them at `import coola`, because its registry registers optional modules lazily; `hya` should do
  the same (section 3.4).
- **D2. `import hya` emits one warning per resolver [verified].** OmegaConf 2.4 deprecates
  `register_new_resolver` (`UserWarning`, from `registry.py:143`). Three more warnings say
  "cannot resolve annotations for runtime validation" for `hya.iter_join`, `hya.braceexpand` and
  `hya.np.array`, because their annotations (`Iterable`, `Iterator`, `ArrayLike`) are imported
  under `TYPE_CHECKING` only. Calling `hya.log:1` warns "expected float, got int", because
  OmegaConf 2.4 validates annotations at call time and `int` is not `float` to it. Violates P2.
- **D3. Most of `resolvers.py` is wrappers [reading].** `asinh`, `exp`, `log`, `log10`, `sinh`,
  `sqrt`, `floordiv`, `truediv`, `sub`, `neg`, `pow`, `len`, `max`, `min` each take 20 to 30 lines
  (docstring + doctest) to call one stdlib function. Their annotations are also the source of the
  `float`/`int` warnings in D2.
- **D4. `hya.braceexpand` returns a one-shot generator [verified].** Stored in the config it is
  consumed once per access, has no `len`, cannot be indexed and cannot be dumped. The other
  list-like resolvers return real lists.
- **D5. `default.py` is 157 lines for a table [reading].** Three near-identical `_add_*_resolvers`
  functions, three local imports with `# noqa: PLC0415`, three `# pragma: no cover`, and a
  module-level side effect (`get_default_registry().register_resolvers()` at the bottom), so
  importing `hya.default` alone registers resolvers. The docstring of `get_default_registry`
  claims the registry is "initially empty"; it is not.
- **D6. The registry API is loose [reading].** `register(key, exist_ok=False)` takes a positional
  boolean (violates P13). `state` returns the live dict, so `registry.state[...] = ...` bypasses
  every check. `ResolverRegistry` is not exported from `hya`.
- **D7. `hya.imports` repeats itself [reading].** Six functions share one pattern
  (`find_spec` / raise `RuntimeError` with install hint). Acceptable, but each `check_*` message
  is hand-written; one private helper would halve the file. Low priority, no behaviour change.

### Documentation problems [verified unless noted]

- **U1.** The user guide's "Overriding Existing Resolvers" does not work (B2).
- **U2.** "Cache expensive computations" claims an interpolation reuses a cached result. OmegaConf
  does not cache resolver output by default (`use_cache=False`) **[reading]**; each access calls
  the resolver again.
- **U3.** The troubleshooting section shows `ImportError: braceexpand is required to use
  hya.braceexpand resolver`. The real error is `RuntimeError: 'braceexpand' package is required but
  not installed...`. And when the package is missing the resolver is not registered, so the user
  sees `UnsupportedInterpolationType`, not an import error. The "Error Handling" example catches
  `InterpolationResolutionError`, which is not what a missing `torch` raises.
- **U4.** The `hya.path` docstring says `~` "may not work" in interpolations. It works when quoted:
  `${hya.path:"~/x"}` → `/Users/.../x`. Unquoted it is a grammar error. Say so.
- **U5.** The user guide computes `warmup_steps: ${hya.mul:100000,0.1}  # 10000`; the value is
  `10000.0`. Use `ceildiv`/`floordiv` or show the float.
- **U6.** `get_default_registry` docstring: "initially empty" is wrong (D5).

### Must not regress

All current resolver keys keep working for the documented inputs (except the changes of section 5).
Doctests keep running. The default registry stays a singleton. A custom `ResolverRegistry` stays
independent of the default one.

---

## 3. Target architecture

### 3.1 Module layout

```text
src/hya/
├── __init__.py       # exports ResolverRegistry, get_default_registry; registers the defaults (P1)
├── registry.py       # ResolverRegistry
├── default.py        # get_default_registry (+ the table of built-in resolvers)
├── resolvers.py      # only resolvers with hya-specific behaviour (add, mul, ceildiv, ...)
├── braceexpand.py    # braceexpand_resolver (guarded import + fallback, as today)
├── numpy.py          # to_array_resolver (guarded import + fallback, as today)
├── torch.py          # to_tensor_resolver, torch_dtype_resolver (guarded import + fallback)
├── imports.py        # check_*/is_*_available (unchanged API)
├── testing.py        # pytest markers (unchanged)
└── utils/fallback/   # fake modules for the guarded imports (unchanged)
```

Nothing is removed from `hya/utils/`. `CLAUDE.md` needs no change.

### 3.2 `ResolverRegistry`

```python
class ResolverRegistry:
    def __init__(self, state: Mapping[str, Callable[..., Any]] | None = None) -> None: ...

    @property
    def state(self) -> Mapping[str, Callable[..., Any]]:  # read-only view (MappingProxyType)
        ...

    def has_resolver(self, key: str) -> bool: ...

    def register(self, key: str, *, exist_ok: bool = False) -> Callable[[F], F]: ...

    def register_lazy(self, key: str, target: str, *, exist_ok: bool = False) -> None:
        """Register ``"module:function"``; the module is imported on the first call."""

    def register_resolvers(self, *, replace: bool = False) -> None:
        """Publish the resolvers of the registry to OmegaConf."""
```

Changes:

- `exist_ok` is keyword-only (P13). `state` is a read-only view; the guide stops showing
  mutation through it.
- `register_resolvers(*, replace=False)` (decision D2, alternative chosen). The registry
  remembers what it published (`_published: dict[str, Callable]`):

  ```python
  def register_resolvers(self, *, replace: bool = False) -> None:
      for key, resolver in self._state.items():
          if self._published.get(key) is resolver:
              continue  # already published, nothing to do: calling twice changes nothing
          if OmegaConf.has_resolver(key) and not replace:
              warnings.warn(
                  f"A resolver is already registered in OmegaConf for '{key}': not replaced. "
                  "Use register_resolvers(replace=True) to replace it.",
                  stacklevel=2,
              )
              continue
          OmegaConf.register_resolver(
              key, resolver, replace=replace, annotation_validation="off"
          )
          self._published[key] = resolver
  ```

  - Calling it twice is silent (idempotent). After `import hya`, the guide's custom-resolver
    example (`registry.register("double")` then `registry.register_resolvers()`) is silent: the
    `hya.*` keys are unchanged and already published.
  - Overriding a built-in (`register("hya.add", exist_ok=True)`) now **warns** instead of being
    ignored (B2), and `register_resolvers(replace=True)` makes it take effect.
  - A key registered in OmegaConf by something else (another registry, user code) is not
    overwritten unless `replace=True`.
  - `annotation_validation="off"` fixes D2: the annotations of `hya` resolvers are documentation
    for readers and type checkers (they use `TYPE_CHECKING` imports on purpose), not a runtime
    contract.
  - No shim: OmegaConf `>=2.4` is required (constraint 4), so `register_new_resolver` (deprecated)
    is not used. OmegaConf's per-config cache of already-resolved nodes is not cleared by
    `replace=True` (`OmegaConf.clear_cache(cfg)`); document it.
- The constructor keeps copying its input, so `ResolverRegistry(table)` is how `default.py`
  builds the default registry.

### 3.3 Default registry

```python
_BUILTINS: dict[str, Callable[..., Any]] = {
    "hya.add": resolvers.add_resolver,
    "hya.sub": operator.sub,
    ...
}

# (key, "module:function", required package)
_OPTIONAL: tuple[tuple[str, str, Callable[[], bool]], ...] = (
    ("hya.braceexpand", "hya.braceexpand:braceexpand_resolver", is_braceexpand_available),
    ("hya.np.array", "hya.numpy:to_array_resolver", is_numpy_available),
    ("hya.torch.tensor", "hya.torch:to_tensor_resolver", is_torch_available),
    ("hya.torch.dtype", "hya.torch:torch_dtype_resolver", is_torch_available),
)


@cache
def get_default_registry() -> ResolverRegistry:
    registry = ResolverRegistry(_BUILTINS)
    for key, target, is_available in _OPTIONAL:
        if is_available():
            registry.register_lazy(key, target)
    return registry
```

`default.py` no longer imports `hya.braceexpand`, `hya.numpy` or `hya.torch`: no local imports, no
`noqa`, no `pragma: no cover`. The side effect moves from `default.py` to `hya/__init__.py`:

```python
from hya.default import get_default_registry
from hya.registry import ResolverRegistry

get_default_registry().register_resolvers()
```

### 3.4 Lazy registration of the optional resolvers (P2), as in coola

`coola` registers its optional testers as `"module:function"` strings and imports the module only
when it is first needed (`register_lazy`), after checking the package with `find_spec`
(`package_available`). `hya` does the same. The modules `hya.numpy`, `hya.torch` and
`hya.braceexpand` keep their guarded import and fallback:

```python
if TYPE_CHECKING or is_torch_available():
    import torch
else:  # pragma: no cover
    from hya.utils.fallback.torch import torch
```

`register_lazy` stores a small closure, because OmegaConf needs a callable at registration time:

```python
def register_lazy(self, key: str, target: str, *, exist_ok: bool = False) -> None:
    module_name, _, function_name = target.partition(":")

    def resolver(*args: Any) -> Any:
        return getattr(import_module(module_name), function_name)(*args)

    self.register(key, exist_ok=exist_ok)(resolver)
```

- The first call of `${hya.torch.tensor:...}` imports `hya.torch` and so torch (0.5 s, once);
  `import hya` does not.
- `register_lazy` needs its own tests (the target string is split, the module is not imported at
  registration, the first call imports it, a bad target raises on the call), and an integration
  test that resolves a real `${hya.np.array:[1,2]}` through the lazy callable. To verify in PR 4:
  OmegaConf accepts a `*args` closure (it only inspects the parameter names `_parent_`, `_root_`
  and `_node_` **[reading]**).
- The resolver functions in `hya.numpy`, `hya.torch` and `hya.braceexpand` keep `check_*()` for
  direct calls without the package.
- Alternative not taken: `lazy_exports` (PEP 562) as in `coola.utils.imports.lazy`. `hya` has
  no lazy public names; its only lazy items are resolvers.

### 3.5 Resolvers

**Resolvers that are exactly a stdlib callable are registered as that callable**, with no wrapper
function, no docstring to maintain and no test of someone else's code:

| Key             | Callable           | Key            | Callable           |
| --------------- | ------------------ | -------------- | ------------------ |
| `hya.sub`       | `operator.sub`     | `hya.exp`      | `math.exp`         |
| `hya.truediv`   | `operator.truediv` | `hya.log`      | `math.log`         |
| `hya.floordiv`  | `operator.floordiv` | `hya.log10`   | `math.log10`       |
| `hya.neg`       | `operator.neg`     | `hya.sqrt`     | `math.sqrt`        |
| `hya.pow`       | `operator.pow`     | `hya.sinh`     | `math.sinh`        |
| `hya.len`       | `len`              | `hya.asinh`    | `math.asinh`       |
| `hya.max`       | `max`              | `hya.min`      | `min`              |

Built-in callables have no `TYPE_CHECKING`-only annotations, so they cannot trigger the D2
warnings. The behaviour and the error messages are the stdlib's. `docs/resolvers.md` lists each
key with its callable and one example (the doctests move there; they are run by `xdoctest` on the
Markdown or by the integration table of section 8).

**Resolvers with hya behaviour stay as functions in `resolvers.py`** (about 130 lines):

| Key             | Function                                         | Behaviour                                                                                               |
| --------------- | ------------------------------------------------ | ------------------------------------------------------------------------------------------------------- |
| `hya.add`       | `add_resolver(first, *others)`                   | `functools.reduce(operator.add, others, first)`. Does not modify its arguments (B1). Needs ≥1 argument. |
| `hya.mul`       | `mul_resolver(first, *others)`                   | `functools.reduce(operator.mul, others, first)`. Numbers; no in-place repetition of a config list.      |
| `hya.ceildiv`   | `ceildiv_resolver(dividend, divisor)`            | `-(dividend // -divisor)`.                                                                              |
| `hya.pi`        | `pi_resolver()`                                  | `math.pi` (a resolver with no argument; `${hya.pi:}`).                                                  |
| `hya.iter_join` | `iter_join_resolver(iterable, separator)`        | `separator.join(map(str, iterable))`.                                                                   |
| `hya.sha256`    | `sha256_resolver(obj)`                           | SHA-256 hex digest of `str(obj)`; documented as such.                                                   |
| `hya.path`      | `path_resolver(path)`                            | See below.                                                                                              |

`hya.path` replaces both `hya.path` and `hya.to_path` (B3):

```python
def path_resolver(path: str) -> Path:
    """Return the absolute path: expand ``~``, resolve, and read ``file://`` URLs."""
    if path.startswith("file:"):
        path = unquote(urlparse(path).path)
    return Path(path).expanduser().resolve()
```

Only a `file:` URL is decoded; any other string is a plain path, so `/a?b` and `/a%20b` stay as
written. Tilde needs quotes in an interpolation: `${hya.path:"~/data"}` (documented, U4).

**Optional resolvers:**

- `hya.braceexpand` returns `list[str]` (D4): `list(braceexpand.braceexpand(pattern))`. The result
  is a `ListConfig`, so it has a length, can be indexed, is re-iterable and can feed
  `hya.iter_join`. Cost: the whole expansion is built eagerly (see decision D3).
- `hya.np.array`, `hya.torch.tensor`: unchanged behaviour, lazy import.
- `hya.torch.dtype`: unchanged behaviour. The error lists the available dtype **names, sorted**
  (B4) instead of a set of objects. `get_dtypes` becomes private (`_dtype_names`) because the
  public function has no other use than the message; it returns `sorted(...)` of attribute names
  whose value is a `torch.dtype`.

### 3.6 Size effect (estimates)

| File                   | Now  | Target | Note                                              |
| ---------------------- | ---- | ------ | ------------------------------------------------- |
| `resolvers.py`         | 573  | ~130   | 14 wrappers removed, `to_path` merged             |
| `default.py`           | 157  | ~70    | table + three `if`                                |
| `registry.py`          | 143  | ~170   | `register_lazy`, `_published`, read-only state    |
| `braceexpand.py`       | 51   | ~45    | list result                                       |
| `numpy.py`             | 48   | ~48    | unchanged                                         |
| `torch.py`             | 117  | ~100   | sorted names                                      |
| `imports.py`           | 142  | ~142   | unchanged (D7 optional)                           |
| **`src` total**        | 1334 | ~770   |                                                   |

Unit tests shrink by the same logic: 48 tests of stdlib wrappers in `tests/unit/test_resolvers.py`
become about 15 (one per remaining function and edge).

---

## 4. Public API after the change

```python
import hya

hya.get_default_registry()
hya.ResolverRegistry          # new top-level export

from hya.registry import ResolverRegistry          # still valid
from hya.imports import check_numpy, is_numpy_available   # unchanged (and torch, braceexpand)
from hya.testing import numpy_available, ...        # unchanged
```

Resolver functions stay importable from `hya.resolvers`, `hya.numpy`, `hya.torch`,
`hya.braceexpand` for direct calls. Removed: `hya.resolvers.{asinh,exp,floordiv,len,log,log10,max,
min,neg,pow,sinh,sqrt,sub,truediv}_resolver`, `hya.resolvers.to_path_resolver`,
`hya.torch.get_dtypes`. New: `ResolverRegistry.register_lazy`, `register_resolvers(*, replace=False)`.

---

## 5. Behaviour changes (for the release notes)

| Change                                              | Before                                                        | After                                                          |
| --------------------------------------------------- | ------------------------------------------------------------- | -------------------------------------------------------------- |
| `hya.add` does not modify its arguments (B1)        | `conf.x` changed when read through `${hya.add:${x},[3]}`      | `conf.x` unchanged                                             |
| `hya.mul` on a list and an int                      | repeats the list (in place)                                   | `TypeError` from OmegaConf (`ListConfig` has no `*`). Numbers only |
| `register_resolvers(*, replace=False)`              | existing key skipped silently                                 | skipped with a warning; `replace=True` replaces                |
| `register(key, exist_ok)`                           | positional allowed                                            | `exist_ok` keyword-only                                        |
| `registry.state`                                    | live `dict`                                                   | read-only mapping                                              |
| `hya.to_path` removed                               | URL parsed for every input                                    | use `hya.path` (decodes `file://` only)                        |
| `hya.braceexpand`                                   | generator                                                     | `list[str]`                                                    |
| `hya.torch.dtype` error                             | unordered set of dtypes                                       | sorted names                                                   |
| `import hya`                                        | 0.59 s, imports torch/numpy, emits warnings                   | no numpy/torch import, no warning                              |
| OmegaConf requirement                               | `>=2.2,<3.0`                                                  | `>=2.4,<3.0`                                                   |
| `hya.max:1` / `hya.sqrt:...` messages               | hya wrapper's error                                           | stdlib's error                                                 |

---

## 6. Documentation

- `docs/resolvers.md` is rebuilt from one table (key, callable or function, arguments, example),
  grouped as today (arithmetic, math, comparison, constants, paths, utilities, optional). Examples
  are doctests.
- Add a short **Properties** page (section 1) to the user guide, and link it from `index.md`.
- Fix U1 to U6. Add the OmegaConf 2.4 note (annotation validation is off) and the cache note
  (`OmegaConf.clear_cache`) to the registry section.
- Add `docs/migration/v0.4_to_v0.5.md` generated from section 5.
- `docs/refs/`: keep `registry.md` and `resolvers.md`; add `hya` (top-level exports) and
  remove nothing else.
- Update `README.md` ("Available Resolvers" count, example of `register_resolvers`).

---

## 7. Migration plan

One branch and one PR per row, branch names per `CLAUDE.md`. Rows 3 to 5 are stacked; the others
branch from `main`.

| # | PR   | Branch                                  | Content                                                                                                                           | Breaking |
| - | ---- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 1 | #754 | `docs/fix-user-guide`                   | Fix U2 to U6 (what is false today). Mark the override example as "fixed in the next PR" or hold U1 for PR 3.                      | no       |
| 2 | #755 | `bugfix/add-mul-no-mutation`            | B1: `add`/`mul` with `functools.reduce`; regression test (`conf.x` unchanged), checked to fail without the fix.                    | yes (list `*`) |
| 3 | #756 | `bugfix/register-resolvers-replace`     | B2 and D2: require `omegaconf>=2.4` (`pyproject.toml`, `dev/config/package_versions.json`, README table), `OmegaConf.register_resolver` with `annotation_validation="off"`, `register_resolvers(*, replace=False)` with `_published` and the warning, keyword-only `exist_ok`, read-only `state`, export `ResolverRegistry`. Integration test of an override and `-W error` import. | yes |
| 4 | #757 | `perf/lazy-optional-resolvers`          | D1, D5: `register_lazy`; table-based `default.py` that no longer imports the optional modules; registration moved to `__init__`. The optional modules keep their guarded imports and fallbacks. | no (internal) |
| 5 | #758 | `refactor/stdlib-resolvers`             | D3: register stdlib callables, delete 14 wrappers and their tests, rewrite `resolvers.md` table, add the integration table test. | yes (imports of removed functions) |
| 6 | #759 | `refactor/merge-path-resolvers`         | B3: `hya.path` handles `file:`; remove `hya.to_path`.                                                                              | yes      |
| 7 | #760 | `feat/braceexpand-list`                 | D4 and B4: list result, sorted dtype names, private `_dtype_names`.                                                                | yes      |
| 8 | #761 | `docs/properties-and-migration`         | Properties page, migration page, README, final pass on the guide. Release as `0.5.0` (confirm the number).                                       | no       |

Each PR updates the docs it touches and runs: `ruff check`, `ruff format`, `inv types.check`,
`pyright --verifytypes hya --ignoreexternal`, the unit tests of the changed modules,
`pytest --xdoctest src/hya`, coverage of the changed code.

---

## 8. Tests and gates

**Integration (`tests/integration/`), no patching**

- **Resolver table** (`test_resolvers.py`): one parametrized test over
  `(expression, expected)` for every key of the default registry, using real OmegaConf
  resolution. Plus one test that the set of registered keys equals the documented set (guards P3 and
  the docs table).
- **Import** (subprocess, `python -X importtime` not needed): `import hya` leaves `numpy`,
  `torch` and `braceexpand` out of `sys.modules` (P2) and `python -W error -c "import hya"`
  exits 0 (D2).
- **Override** (P8): register `hya.add` with `exist_ok=True`; `register_resolvers()` warns and keeps
  the old resolver (`pytest.warns` with `match`); `register_resolvers(replace=True)` installs the
  new one; calling it twice is silent.
- **Purity** (P5): `${hya.add:${x},[3]}` leaves `x` unchanged.
- **Optional packages**: with the package, resolvers work; without it (`*_not_available`
  markers) the key is absent and the direct function call raises `RuntimeError` with the install
  hint.

**Unit (`tests/unit/`), one behaviour per test**

- `test_registry.py`: `register` (new key, duplicate raises, `exist_ok`, non-callable raises,
  returns the function), `has_resolver`, `state` is read-only and does not alias the input dict,
  `register_resolvers` with a patched `OmegaConf` for both API branches (the real branch is covered
  by the integration test above), whole `state` against a literal.
- `test_default.py`: the default registry is a singleton; the keys match a literal set for each
  combination of available packages (patched `is_*_available`); no key outside `hya.`.
- `test_resolvers.py`: `add`/`mul` (several args, one arg, no mutation, strings, lists for
  `add`), `ceildiv` (ints, floats, negative, zero divisor), `pi`, `iter_join` (empty, one item,
  non-string items), `sha256` (known digest, non-string), `path` (plain, `~`, relative, `file://`,
  `file://` with `%20`, `?` and `%` kept, trailing slash).
- `test_braceexpand.py`, `test_numpy.py`, `test_torch.py`: result type and value, error with the
  package missing (patched `check_*`), unknown dtype message equals a literal with sorted names.

**Gates**

- Coverage 100% of `src/hya`, no `pragma: no cover` (the three in `default.py` disappear).
- `pytest --xdoctest src/hya` and the docs build.
- `ty`, `pyright --verifytypes hya --ignoreexternal`, `ruff`, `make lint`.
- Import time: a manual benchmark noted in the PR 4 description (target: below 0.1 s with torch
  installed). Not an automated gate: timings vary across CI runners.

---

## 9. Decisions for the maintainer

| ID  | Question                                                        | Recommendation                                                                                                           | Alternative                                                         |
| --- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------- |
| D1  | Register stdlib callables directly (section 3.5)?               | **Yes.** About 300 fewer lines, no copy of stdlib docs, no annotation warnings.                                          | Keep one wrapper per resolver, with docstring and doctest in `src`. |
| D2  | `register_resolvers` replaces existing OmegaConf resolvers?     | **Decided: alternative.** `replace: bool` keyword, default `False`, with a warning when a key is skipped (section 3.2).  | Always replace; simpler, but overwrites resolvers of other sources. |
| D3  | `hya.braceexpand` returns a list?                               | **Yes** (re-iterable, indexable, typed like the other list resolvers).                                                   | Keep the generator for huge expansions, documented as one-shot.     |
| D4  | Drop `hya.to_path` and fold `file:` into `hya.path`?            | **Yes** (B3).                                                                                                            | Keep both, but make `to_path` parse `file:` only.                   |
| D5  | How are optional dependencies managed?                          | **Decided: as in coola**: guarded imports + fallbacks in the modules, lazy registration of the optional resolvers (3.4). | Lazy `import_module` in each resolver; drops the fallback package.  |
| D6  | OmegaConf requirement?                                          | **Decided: `>=2.4,<3.0`**, no shim (constraint 4).                                                                       | Keep `>=2.2` with a `register_new_resolver` fallback.               |
| D7  | `annotation_validation="off"` for all registered resolvers?     | **Yes.** `hya` annotations are not a runtime contract; users' own resolvers in the default registry are published the same way. | Per-key option on `register`; more API for little value.     |
| D8  | Keep import-time registration (P1)?                             | **Yes.** It is the documented way (`import hya`), and Hydra users rely on it.                                            | Explicit `hya.register()`; cleaner, but breaks every user config.   |
| D9  | `hya.mul` stops repeating lists?                                | **Yes.** In-place repetition of a config list is the same bug as B1.                                                     | Special-case `ListConfig * int` with `list(x) * n`.                 |

---

## 10. Not covered

- New resolvers (`hya.abs`, `hya.round`, `hya.cosh`, `hya.tanh`, `hya.env_path`, ...). The set is
  oddly partial (`sinh`/`asinh` but no `cosh`), but the stdlib-alias table makes adding one a
  one-line change; decide separately, with a use case.
- `use_cache=True` for expensive resolvers (`hya.sha256`, `hya.np.array`). OmegaConf's cache is
  keyed on the argument text, not the value, which is wrong for interpolations.
- Supporting `numpy`/`torch` resolvers that accept `dtype` or `device` arguments
  (`hya.torch.tensor:[1,2],dtype=...`). OmegaConf resolvers take positional arguments only.
- Auto-discovery of resolvers through entry points (a plugin group), as in other packages. The
  registry already lets a project register its own resolvers in two lines.
- The GitHub Actions workflows: aligned with `coola` in #751 and unchanged here. PR 3 edits
  `dev/config/package_versions.json` (OmegaConf versions) and PR 4 must keep the "required
  dependencies only" CI job green.
