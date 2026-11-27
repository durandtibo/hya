# `hya`: target state and the changes to reach it

This document defines the properties `hya` should guarantee, the design that gives them, and the
changes to make to the current code (`main`, `6fa9b2f`, 0.5.0a0) to get there. The latest release
is `v0.4.0`. It replaces the previous review, whose plan is implemented (PRs #776 to #780).

## 1. Properties of the package

These are the rules `hya` guarantees in the target state. Each one is made true by the code and
checked by a test (section 8.2). The numbers are those of `docs/docs/properties.md`. The last column
compares with that page: **kept** (same statement, true today), **changed** (the statement or the
behaviour changes) or **new**.

| #   | Property                      | Statement                                                                                                                                                                                                                                                                              | Enforced by                           | Status  |
| --- | ----------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------- | ------- |
| P1  | **Import is enough**          | `import hya` publishes every default resolver to OmegaConf. No other call is needed, and `register_resolvers()` publishes them again after `OmegaConf.clear_resolvers()`.                                                                                                              | `hya/__init__.py`, `ResolverRegistry` | kept    |
| P2  | **Cheap import**              | `import hya` imports neither `numpy`, `torch` nor `braceexpand`, and emits no warning. The module of an optional resolver is imported on the first call of that resolver.                                                                                                              | `register_lazy`, import contracts     | kept    |
| P3  | **Namespaced**                | Every built-in key starts with `hya.`. Optional ones are grouped (`hya.np.*`, `hya.torch.*`). Nothing is registered outside this namespace.                                                                                                                                            | `hya.default`                         | kept    |
| P4  | **Thin resolvers**            | A resolver is a standard library callable or a function of a few lines with one documented behaviour. No hidden state, no I/O beyond what its name says (`hya.path` touches the file system).                                                                                          | code review                           | kept    |
| P5  | **Pure**                      | A resolver never modifies its arguments. A returned value can be an argument itself or one of its elements (`hya.add` of one value, `hya.max` of lists), exactly as `${x}` returns the node `x`: copy it before you mutate it.                                                         | the resolvers                         | changed |
| P6  | **Deterministic output**      | The same resolved arguments give the same output, including error messages (sorted, no set order), on every process and OmegaConf release. `hya.path` also depends on the file system (working directory, home directory, symbolic links), which is its purpose.                       | the resolvers                         | changed |
| P7  | **Explicit, strict registry** | A `ResolverRegistry` is a key to callable map. `register` adds, `register_resolvers` publishes. Every entry, from `register`, `register_lazy` or the constructor, has a callable value and a key that every supported OmegaConf can interpolate; anything else raises at registration. | `ResolverRegistry.register`           | changed |
| P8  | **Replace is explicit**       | `register_resolvers()` is idempotent. A key that changed since it was published, or that another source registered before the registry published it, is skipped with a warning unless `replace=True`.                                                                                  | `register_resolvers`                  | kept    |
| P9  | **One default registry**      | `get_default_registry()` returns one process-wide registry holding the built-in resolvers. It holds the same keys on every machine, whatever packages are installed. Users extend it or create their own registry.                                                                     | `functools.cache`                     | kept    |
| P10 | **Errors are OmegaConf's**    | A resolver raises standard exceptions only, so a failure surfaces as `InterpolationResolutionError` whose message names the original exception, found in the `__context__` chain (`__cause__` is `None`). A missing optional package says how to install it.                           | the resolvers                         | changed |
| P11 | **Any value out**             | A resolver may return any Python object (`Path`, `ndarray`, `Tensor`, `dtype`, list). Such values are for use in code: `OmegaConf.resolve` needs the `allow_objects` flag and `to_yaml` does not support them.                                                                         | documentation                         | changed |
| P12 | **Typed and documented**      | `py.typed`, `pyright --verifytypes` at 100 %, every public function, class, method and property documented with a doctest and shown in the reference, every resolver listed in `docs/resolvers.md`, and the documentation says nothing false.                                          | CI, tests                             | changed |
| P13 | **Keyword-only options**      | The options of the Python API are keyword-only (`exist_ok`, `replace`). The arguments of a resolver are positional (the grammar has no keyword syntax); an optional argument comes last and has a default.                                                                             | signatures                            | kept    |
| P14 | **Installs next to Hydra**    | `hya` accepts every OmegaConf release that a Hydra release accepts (`omegaconf>=2.2,<3.0`) and behaves the same on all of them. CI runs the tests on the oldest and the newest.                                                                                                        | `_publish`, CI matrix                 | changed |
| P15 | **Composable**                | A resolver accepts the values OmegaConf gives it and the output of another `hya` resolver. In particular `hya.torch.tensor` takes a tensor, an array, and a data type as a `torch.dtype` or as its name.                                                                               | the resolvers                         | changed |
| P16 | **Resolved input**            | A resolver that reads a whole value (`hya.sha256`, `hya.iter_join`, `hya.np.array`, `hya.torch.tensor`) reads its **resolved** content: interpolations are resolved at any depth, and a missing value (`???`) raises `MissingMandatoryValue`.                                          | `hya.utils.config.to_plain`           | new     |
| P17 | **Faithful hash**             | `hya.sha256` hashes the whole content of a value: a string as is, any other value as canonical JSON (sorted keys). Two such values with different JSON forms have different hashes, and a value without a JSON form raises instead of being hashed from a summary.                     | `sha256_resolver`                     | new     |

**Not guaranteed**, and documented as such:

- **Thread-safety** of registering while OmegaConf resolves (OmegaConf's resolver table is a global
  dictionary).
- **Detection of a registration made after `hya`'s.** A resolver that another source registers for a
  key `hya` already published is not detected: it needs the private `BaseContainer._resolvers`.
- **Type-tagged hashes.** `hya.sha256` of the string `[1]` equals the hash of the list `[1]`, an
  integer key equals the same string key, and a path or an enum equals its string in JSON. A mapping
  that mixes key types cannot be sorted and raises.
- **Special parameters of lazy resolvers.** A resolver registered with `register_lazy` cannot
  receive `_root_`, `_parent_` or `_node_`: OmegaConf reads them from the signature, which is not
  known before the import.
- **Caching.** OmegaConf calls the resolver at every access.

### Constraints of the design

1. **Simple and easy to maintain.** One registry, one registration rule, thin resolvers, one shared
   helper. No change adds a class or a layer.
2. **Breaking changes are accepted.** The future state matters more than the past one: no alias, no
   deprecation period. The release notes list the changes (section 5).
3. **The rules of `CLAUDE.md`**: lazy optional packages with fallbacks, shared helpers public in
   `hya.utils`, keyword-only options, no ignored lint or type issue.
4. **Behaviour before size.** A change is kept only if it fixes a reproduced defect or makes a
   property true.

---

## 2. Where `main` stands

Items are tagged **[verified]** (reproduced) or **[reading]** (from the code or documentation).
Probes ran on Python 3.14 with OmegaConf 2.4.0; the ones that depend on OmegaConf were repeated on
2.2.1 or 2.2.3, 2.3.0 or 2.3.1 as noted, in throw-away environments. Scripts and the prototype of
section 6 are not part of the repository. This review changes no file of `src`, `tests` or `docs`.

**The finding in one sentence:** the architecture is right and every gate is green, but the resolvers
that read whole values can return a **wrong result without any error**, the registry accepts entries
that cannot work, and a few statements of the documentation are false.

Gates on `main` **[verified]**: 316 tests pass and 6 are skipped (missing-package cases), coverage of
`src` is 100 %, 25 doctests pass, `ruff`, `ty` and `pyright --verifytypes` (100 %) pass, the 5
import contracts hold, `tests/package/checks.py --extra all` passes, `inv doc.build` and
`inv test.doctest-markdown` pass. So no existing gate sees the findings below.

### 2.1 Wrong results

| #   | Finding                                                                                                                                                                                                                                                                                              | Property | Status                                    |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ----------------------------------------- |
| F1  | **`hya.sha256` does not hash interpolated values.** With `x: ["${a}"]`, `${hya.sha256:${x}}` is the same hash for `a: 1` and `a: 2`, because `str(node)` prints the unresolved text. The same holds for a mapping. An experiment identifier built this way does not change when the experiment does. | P16, P17 | **[verified]** 2.2.1, 2.2.3, 2.3.0, 2.4.0 |
| F2  | **`hya.sha256` collides on large arrays and tensors.** Two arrays of 2,000 values that differ at index 1,000 have the same hash, with `hya.np.array` and with `hya.torch.tensor`: `str()` summarizes them with `...`. The hash also depends on the print options of NumPy and PyTorch.               | P6, P17  | **[verified]**                            |
| F3  | **`hya.sha256` silently hashes a missing value.** `x: ["???"]` gives a hash.                                                                                                                                                                                                                         | P16      | **[verified]**                            |
| F4  | **`hya.sha256` of a mapping depends on the key order**: `{a: 1, b: 2}` and `{b: 2, a: 1}` differ. Documented as a limit today, but it makes the hash of a configuration fragile.                                                                                                                     | P17      | **[verified]**                            |
| F5  | **`hya.iter_join` prints unresolved interpolations** of nested values: with `x: [["${a}"], 2]` the result is `['${a}']-2`. A literal list `[${x}]` does the same. Flat lists are resolved.                                                                                                           | P16      | **[verified]**                            |
| F6  | **`hya.path` drops the query and the fragment of a file URL**: `file:///data/run#1` gives `/data/run`. The module refuses to drop a host for this reason; a `#` in a file name loses data the same way.                                                                                              | P4       | **[verified]**                            |

### 2.2 Values that cannot be composed

| #   | Finding                                                                                                                                                                                                                                      | Property | Status         |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | -------------- |
| F7  | `hya.np.array` takes `float32`, `hya.torch.tensor` refuses it (`argument 'dtype' must be torch.dtype, not str`). The two sibling resolvers have different contracts.                                                                         | P15      | **[verified]** |
| F8  | `${hya.torch.tensor:${t}}` with `t` a tensor emits the "To copy construct from a tensor" `UserWarning`; with warnings as errors the interpolation fails.                                                                                     | P2, P15  | **[verified]** |
| F9  | `hya.torch.tensor` of a list with `???` fails with `could not determine the shape of object type 'ListConfig'` instead of saying that a value is missing (`hya.np.array` says it).                                                           | P16      | **[verified]** |
| F10 | `hya.torch.dtype` raises `InterpolationResolutionError` itself, the only resolver that raises an OmegaConf error: the message names no original exception, and a direct Python call raises an interpolation error outside any interpolation. | P10      | **[reading]**  |

### 2.3 A registry that accepts what cannot work

| #   | Finding                                                                                                                                                                                                                                                      | Property | Status                                   |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- | ---------------------------------------- |
| F11 | **`@registry.register` without a key does nothing, silently.** The function becomes the inner `wrap`, nothing is registered, and no error is raised until the interpolation fails elsewhere.                                                                 | P7       | **[verified]**                           |
| F12 | `ResolverRegistry({"a": 1})` accepts a non-callable: the constructor bypasses the check of `register`. The error appears in `register_resolvers()`, after the keys before it have been published.                                                            | P7       | **[verified]** / **[reading]** (partial) |
| F13 | `register` accepts keys that no interpolation can use (`bad key`, `1a`, `a..b`, `a:b`), published without error; the failure is a grammar error in a configuration. The accepted set also differs: `a-b` works on 2.3.0 and 2.4.0 and not on 2.2.1 or 2.2.3. | P7, P14  | **[verified]**                           |
| F14 | `register_lazy("k", "a:b:c")` is accepted and fails on the first call.                                                                                                                                                                                       | P7       | **[verified]**                           |

### 2.4 False or missing documentation

| #   | Finding                                                                                                                                                                                            | Status         |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------- |
| F15 | The user guide announces the error `Circular reference detected`; OmegaConf says `Recursive interpolation detected` (2.2.3 and 2.4.0).                                                             | **[verified]** |
| F16 | The "Registering Custom Resolvers" snippet of `index.md` uses `OmegaConf` without importing it: run alone, it raises a `NameError`.                                                                | **[verified]** |
| F17 | `get_started.md` and `CONTRIBUTING.md` give `make conda`, `make install` and `make unit-test-cov`: none of these targets exists. `CONTRIBUTING.md` also asks for `black .`; the project uses ruff. | **[verified]** |
| F18 | `CLAUDE.md` says that resolvers are registered with the `ResolverRegistry` of their module (`hya.numpy`, `hya.torch`): these modules have no registry, the keys are in `hya.default`.              | **[reading]**  |
| F19 | P12 does not hold: `ResolverRegistry.state` has no doctest, and the reference pages omit `hya.imports` and `hya.testing`.                                                                          | **[verified]** |
| F20 | P11 and the limits name `to_yaml` only. `OmegaConf.resolve(cfg)` also fails (`UnsupportedValueType`) for an array, a tensor or a dtype unless `cfg` has the `allow_objects` flag.                  | **[verified]** |

### 2.5 Right today, must not regress

All the keys resolve for the documented inputs. `import hya` is free of warnings and of optional
imports (84 ms in total, 35 ms of it OmegaConf). The default registry is a singleton with the same
keys on every machine. `register_resolvers()` is idempotent and publishes again after
`clear_resolvers()`. `hya.add` and `hya.mul` do not modify their arguments. `hya.np.array` already
resolves nested interpolations and reports a missing value. The multi-config Hydra example of the
user guide resolves with `hydra-core` 1.3.2 **[verified]**.

---

## 3. Target architecture

The architecture does not change. One module is added for the one rule that several resolvers share.

```text
src/hya/
├── __init__.py        # exports; publishes the default resolvers (P1)
├── registry.py        # ResolverRegistry, _publish (only place that knows the OmegaConf version)   [strict]
├── default.py         # get_default_registry + the two tables (built-in, optional)
├── resolvers.py       # add, mul, ceildiv, pi, iter_join, sha256, path                              [changed]
├── braceexpand.py     # braceexpand_resolver
├── numpy.py           # to_array_resolver
├── torch.py           # to_tensor_resolver, torch_dtype_resolver                                    [changed]
├── imports.py         # validate_*/is_*_available
├── testing.py         # pytest markers for the optional packages
├── py.typed
└── utils/
    ├── config.py      # to_plain                                                                    [new]
    └── fallback/      # fake modules for the guarded imports
```

### 3.1 One rule for reading configuration values

OmegaConf gives a resolver the configuration node itself (`ListConfig`, `DictConfig`), and a literal
such as `[${x}]` is a plain list that **contains** nodes. `str`, `json` and `torch` do not resolve
the interpolations of a node. One public helper does it, and every resolver that reads a whole value
as text or data goes through it:

```python
# hya/utils/config.py
def to_plain(value: Any) -> Any:
    """Return ``value`` with its configuration nodes converted to plain, resolved objects."""
    if OmegaConf.is_config(value):
        return OmegaConf.to_container(value, resolve=True, throw_on_missing=True)
    if isinstance(value, list):
        return [to_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: to_plain(item) for key, item in value.items()}
    return value
```

It returns new containers, so the input is never modified (P5). Other objects (tensors, paths,
tuples built by user code) pass through unchanged.

`hya.np.array` does **not** use it: NumPy reads a node item by item, which already resolves and
reports missing values, and converting first is 2.4 times slower (252 ms against 105 ms for 100,000
values **[verified]**). For `hya.torch.tensor` the conversion is faster than today (255 ms against
397 ms) and fixes F9. The test of P16 checks all four resolvers, whatever their implementation.

### 3.2 `hya.sha256` (F1 to F4)

```python
def sha256_resolver(obj: Any) -> str:
    value = to_plain(obj)
    if not isinstance(value, str):
        value = json.dumps(value, sort_keys=True, separators=(",", ":"), default=_encode_value)
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _encode_value(value: object) -> str:
    if isinstance(value, (PurePath, Enum)):
        return str(value)
    msg = f"hya.sha256 cannot hash a value of type {type(value).__name__}"
    raise TypeError(msg)
```

- A **string** is hashed as is: the result is the SHA-256 of the text, the same as other tools give,
  and every hash of a string is unchanged.
- **Anything else** is hashed from its canonical JSON: sorted keys, no space. The hash no longer
  depends on `repr`, on print options or on the OmegaConf release.
- An **array, tensor, dtype, set or bytes** raises a `TypeError`. A user who needs to hash an array
  hashes the list it is built from.

| Input            | Hash today (prefix) | Target (prefix) |
| ---------------- | ------------------- | --------------- |
| `mystring`       | `bd3ff475`          | unchanged       |
| `1`              | `6b86b273`          | unchanged       |
| `1.5`            | `9f29a130`          | unchanged       |
| `true`           | `3cbc87c7`          | `b5bea41b`      |
| `null`           | `dc937b59`          | `74234e98`      |
| `[1,2]`          | `3a316d6d`          | `49a64717`      |
| `{b: 2, a: 1}`   | `46e391c4`          | `43258cff`      |
| `${hya.path:/a}` | `6a50dc85`          | `54b379c9`      |

### 3.3 `hya.iter_join` (F5)

```python
def iter_join_resolver(iterable: Iterable[Any], separator: str) -> str:
    return separator.join(map(str, to_plain(iterable)))
```

The elements are still converted with `str` (P4): a nested list is printed as a Python list, now
with its resolved values. A missing value raised already for a flat list; it now raises at any depth.

### 3.4 `hya.torch.tensor` and `hya.torch.dtype` (F7 to F10)

```python
def to_tensor_resolver(data: Any, dtype: torch.dtype | str | None = None) -> torch.Tensor:
    validate_torch()
    if isinstance(dtype, str):
        dtype = torch_dtype_resolver(dtype)
    if isinstance(data, torch.Tensor):
        return data.detach().to(dtype=data.dtype if dtype is None else dtype, copy=True)
    return torch.tensor(to_plain(data), dtype=dtype)


def torch_dtype_resolver(target: str) -> torch.dtype:
    validate_torch()
    dtype = getattr(torch, target, None)
    if isinstance(dtype, torch.dtype):
        return dtype
    msg = f"Incorrect dtype {target}. The available dtypes are {_dtype_names()}"
    raise ValueError(msg)
```

- `${hya.torch.tensor:[1,2],float32}` now works, like `hya.np.array`. A `torch.dtype` still works.
- A tensor input is copied without a warning (P5: the result does not share memory).
- `hya.torch.dtype` raises a `ValueError`; through an interpolation it is still an
  `InterpolationResolutionError`, now of the same form as every other resolver error (P10).

### 3.5 `hya.path` (F6)

A `file:` URL with a query or a fragment raises, as a URL with a host does:

```python
if url.netloc not in ("", "localhost") or url.query or url.fragment:
    msg = f"A file URL with a host, a query or a fragment is not supported: '{path}'"
    raise ValueError(msg)
```

A literal `#` or `?` is written `%23` or `%3F` in a URL, or the path is given without `file:`.

### 3.6 `ResolverRegistry` (F11 to F14)

The public members stay: `register`, `register_lazy`, `register_resolvers`, `has_resolver`, `state`.
Every entry goes through `register`, which is the only place that validates:

```python
# A name that every supported OmegaConf can interpolate: identifiers joined by dots
_KEY = re.compile(r"[A-Za-z_]\w*(\.[A-Za-z_]\w*)*", re.ASCII)


class ResolverRegistry:
    def __init__(self, state: Mapping[str, Callable[..., Any]] | None = None) -> None:
        self._state: dict[str, Callable[..., Any]] = {}
        self._published: dict[str, Callable[..., Any]] = {}
        for key, resolver in (state or {}).items():
            self.register(key)(resolver)

    def register(self, key: str, *, exist_ok: bool = False) -> Callable[[F], F]:
        if not isinstance(key, str):
            msg = (
                f"The key must be a string, but received {type(key).__name__}. "
                "Use the decorator as @registry.register('my_key')."
            )
            raise TypeError(msg)
        if not _KEY.fullmatch(key):
            msg = f"Invalid resolver key '{key}': use names made of letters, digits and _, joined by dots"
            raise ValueError(msg)
        ...  # unchanged
```

`register_lazy` requires `function_name.isidentifier()` (F14). `register_resolvers` is unchanged:
with every entry valid, a publication cannot stop half way because of an entry.

### 3.7 Default registry and catalogue

Unchanged: 24 built-in keys and 4 lazy optional keys.

| Group              | Keys                                                                                     |
| ------------------ | ---------------------------------------------------------------------------------------- |
| Operators          | `hya.sub`, `hya.truediv`, `hya.floordiv`, `hya.neg`, `hya.pow`                           |
| Math               | `hya.sqrt`, `hya.exp`, `hya.log`, `hya.log10`, `hya.sinh`, `hya.asinh`                   |
| Builtins           | `hya.max`, `hya.min`, `hya.len`, `hya.sum`, `hya.int`, `hya.float`                       |
| Behaviour of `hya` | `hya.add`, `hya.mul`, `hya.ceildiv`, `hya.pi`, `hya.iter_join`, `hya.sha256`, `hya.path` |
| Optional (lazy)    | `hya.braceexpand`, `hya.np.array`, `hya.torch.tensor`, `hya.torch.dtype`                 |

A resolver is added when a configuration needs it **and** no composition of the existing keys gives
it.

---

## 4. Public API after the change

```python
import hya

hya.ResolverRegistry(state=None)  # entries are validated
hya.get_default_registry()

registry.register(key, *, exist_ok=False)  # decorator factory, validates the key
registry.register_lazy(key, target, *, exist_ok=False)
registry.register_resolvers(*, replace=False)
registry.has_resolver(key)
registry.state  # read-only mapping

hya.utils.config.to_plain(value)  # new
```

## 5. Behaviour changes for users

| Change                                                                     | Before                            | After                                        | What the user does                   | Breaking |
| -------------------------------------------------------------------------- | --------------------------------- | -------------------------------------------- | ------------------------------------ | -------- |
| `hya.sha256` of a value that is not a string, an integer or a finite float | hash of `str(obj)`                | hash of canonical JSON of the resolved value | recompute stored identifiers         | yes      |
| `hya.sha256` of an array, tensor, dtype, set, bytes                        | a hash (possibly colliding)       | `TypeError`                                  | hash the source list or string       | yes      |
| `hya.sha256`, `hya.iter_join`, `hya.torch.tensor` with a nested `???`      | a result, or an unclear error     | `MissingMandatoryValue`                      | set the value                        | yes      |
| `hya.iter_join` of nested nodes                                            | unresolved text                   | resolved values                              | nothing                              | yes      |
| `hya.path` of a file URL with `?` or `#`                                   | text silently dropped             | `ValueError`                                 | percent-encode, or pass a plain path | yes      |
| `hya.torch.tensor` second argument                                         | `torch.dtype`                     | `torch.dtype` or its name                    | nothing                              | no       |
| `hya.torch.tensor` of a tensor                                             | copy with a warning               | copy                                         | nothing                              | no       |
| Unknown name in `hya.torch.dtype`, direct Python call                      | `InterpolationResolutionError`    | `ValueError`                                 | catch `ValueError`                   | yes      |
| Registry key outside `identifier(.identifier)*`, for example `a-b`         | accepted                          | `ValueError`                                 | rename the key (for example `a_b`)   | yes      |
| Non-string key, non-callable value in the constructor                      | accepted, fails later or silently | `TypeError` at registration                  | fix the call                         | yes      |

The release notes of `v0.5.0` take this table.

---

## 6. Evidence: a prototype of the changes

The code of section 3 (with minimal docstrings) was applied to a throw-away copy of `src/hya` and
`tests`. **[verified]**

| Check                                                    | Result                                                                                   |
| -------------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Probes of F1 to F9, F11 to F13 with `python -W error`    | fixed, OmegaConf 2.4.0 (all) and 2.2.1, 2.2.3, 2.3.1 (those that need no NumPy or torch) |
| Hashes of `sha256` edge inputs on the four releases      | identical                                                                                |
| Existing unit and integration tests                      | 315 pass, 6 skipped, 1 fails                                                             |
| The failing test                                         | `test_path_resolver_file_url_with_a_host_raises`: it matches the old message (3.5)       |
| Existing doctests                                        | 25 pass                                                                                  |
| `ruff check`, `ruff format --check`, `ty check` on `src` | pass, with no `noqa` (the `dtype` check is written to satisfy rule `TRY004`)             |
| Size of the change in `src`                              | 47 lines added, 15 removed, 1 new module                                                 |

`pyright --verifytypes` and the import contracts were not run on the prototype.

Cost, per access of an interpolation over a list of 10,000 values (OmegaConf calls the resolver at
each access):

| Resolver               | `main`  | Prototype |
| ---------------------- | ------- | --------- |
| `hya.sha256` (list)    | 1.2 ms  | 25 ms     |
| `hya.iter_join` (list) | 11 ms   | 25 ms     |
| `hya.sha256` (string)  | 0.14 ms | 0.14 ms   |

The cost is that of resolving about 2.5 µs per value, which `main` skips and is why its hash is wrong.
It is accepted: configurations of this size are rare, and correctness comes first.

---

## 7. Changes to reach the target state

One branch and one pull request per logical change. Each pull request updates the pages it affects
(`properties.md`, `design.md`, `resolvers.md`, `user_guide.md`, docstrings), adds its tests, and
states its behaviour changes. Stacked pull requests are based on the previous branch.

| PR       | Branch                               | Base | Change                                                                                                                                                                                                                                                           | Breaking |
| -------- | ------------------------------------ | ---- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- |
| 1 (#793) | `docs/fix-false-statements`          | main | F15 to F20: error message of the guide, import in the `index.md` snippet, commands of `get_started.md` and `CONTRIBUTING.md` (`inv env.install`, `inv test.unit`, ...), sentence of `CLAUDE.md`, doctest of `state`, reference pages, wording of P5, P6 and P11. | no       |
| 2 (#794) | `bugfix/hash-resolved-values`        | PR 1 | F1 to F4: `hya.utils.config.to_plain`, canonical `sha256`; P16 and P17; rewrite the `sha256` notes of `design.md` and the limits.                                                                                                                                | yes      |
| 3 (#795) | `bugfix/join-resolved-values`        | PR 2 | F5: `iter_join` uses `to_plain`.                                                                                                                                                                                                                                 | yes      |
| 4 (#796) | `bugfix/copy-tensor-input`           | PR 3 | F8, F9: tensor input and `to_plain` in `to_tensor_resolver`.                                                                                                                                                                                                     | yes      |
| 5 (#797) | `feat/accept-dtype-name-in-tensor`   | PR 4 | F7: the `dtype` name; P15.                                                                                                                                                                                                                                       | no       |
| 6 (#798) | `bugfix/raise-value-error-for-dtype` | PR 5 | F10: `ValueError` in `torch_dtype_resolver`; P10.                                                                                                                                                                                                                | yes      |
| 7 (#799) | `bugfix/validate-registry-entries`   | PR 6 | F11 to F14: validation in `register`, constructor, `register_lazy`; P7, P14; the new limit on lazy resolvers.                                                                                                                                                    | yes      |
| 8        | `bugfix/reject-file-url-query`       | main | F6: query and fragment of a file URL.                                                                                                                                                                                                                            | yes      |

PR 2 is first by value: it is the only family of silent wrong results used for identifiers. After the
eight pull requests are merged and CI is green, the maintainer sets the version `0.5.0` and creates
the exact tag `v0.5.0` with the table of section 5 in the release notes.

---

## 8. Tests and gates

### 8.1 Tests of each change

Unit tests mirror the source tree, with one behaviour per test and literal expected values. Each bug
fix has a regression test that fails with `git stash push src`.

| PR  | Unit tests                                                                                                                                                                                                                                                     | Integration tests (real OmegaConf, no patching)                                                           |
| --- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------- |
| 2   | `tests/unit/utils/test_config.py`: node, nested node in a list and in a dict, scalar and object passthrough, empty containers, missing value, input not modified. `_encode_value`: path, enum, other type. `sha256`: literals per type, key order, mixed keys. | hash changes with an interpolated value (flat, mapping, literal `[${x}]`); `???` raises; an array raises. |
| 3   | nested node resolved, empty iterable, string iterable unchanged.                                                                                                                                                                                               | `x: [["${a}"], 2]` gives `[1]-2`; nested `???` raises.                                                    |
| 4   | tensor input keeps the dtype, takes a new one, does not share memory, no warning.                                                                                                                                                                              | tensor of `${hya.torch.tensor:...}` under `filterwarnings=error`; `???` raises `MissingMandatoryValue`.   |
| 5   | name, `torch.dtype`, `None`, unknown name.                                                                                                                                                                                                                     | `${hya.torch.tensor:[1,2],float32}`.                                                                      |
| 6   | direct call raises `ValueError` with the sorted names.                                                                                                                                                                                                         | the interpolation error names `ValueError`.                                                               |
| 7   | parametrised valid and invalid keys; key that is a function; constructor with a non-callable and with an invalid key; invalid lazy targets; state unchanged after an error.                                                                                    | every accepted key form resolves, on each OmegaConf of the CI matrix (P14).                               |
| 8   | query, fragment, `%23` accepted.                                                                                                                                                                                                                               | the interpolation raises.                                                                                 |

The tests of a missing optional package keep their behaviour: `validate_torch()` runs first.

### 8.2 Test of each property

| #                 | Test                                                                                              |
| ----------------- | ------------------------------------------------------------------------------------------------- |
| P1, P2, P3, P9    | existing: `tests/integration/test_default.py`, `test_registry.py`, `tests/unit/test_default.py`   |
| P4                | code review                                                                                       |
| P5, P10, P12, P13 | existing: `tests/integration/test_resolvers.py`, unit tests, CI; PRs 1, 4 and 6 add their cases   |
| P6, P17           | PR 2: literal hashes, so a change of the canonical form fails a test on every CI job              |
| P7, P14           | PR 7, and the `omegaconf` matrix of `dev/config/package_versions.json`                            |
| P8                | existing: `tests/integration/test_registry.py`                                                    |
| P11               | existing doctests; PR 1 adds the `allow_objects` case                                             |
| P15               | PRs 4 and 5                                                                                       |
| P16               | PRs 2 to 4, plus one parametrised test over the four resolvers (`???` and a nested interpolation) |

### 8.3 Gates (all of `CLAUDE.md`)

```shell
.venv/bin/ruff check src tests && .venv/bin/ruff format src tests
.venv/bin/inv types.check
VIRTUAL_ENV=$PWD/.venv PATH=$PWD/.venv/bin:$PATH .venv/bin/pyright --verifytypes hya --ignoreexternal
.venv/bin/pytest tests/unit tests/integration -q --cov=hya --cov-report=term-missing
.venv/bin/python -m pytest --xdoctest src/hya
```

Expected after each pull request: all green, coverage 100 %, no `noqa`, no `pragma: no cover` added.
The five import contracts hold (`hya.utils.config` imports only OmegaConf).

---

## 9. Decisions for the maintainers

Each has a recommendation; the target state assumes it.

| #   | Question                                                                             | Recommendation                                                                                                                                                                                                   |
| --- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| D1  | Hash a string as is, or as JSON too?                                                 | **As is.** It keeps every hash of a string and matches other SHA-256 tools. JSON for strings would remove the `[1]` string and list collision, but changes the most common identifiers.                          |
| D2  | Should `hya.sha256` hash arrays and tensors from their bytes?                        | **No.** It needs a format for dtype and shape and two optional packages in a standard library resolver. Raise, and hash the source value.                                                                        |
| D3  | Which keys does the registry accept?                                                 | **`identifier(.identifier)*`, ASCII**, the set that 2.2 to 2.4 all interpolate. Accepting `-` would make a key work or not according to the installed release (P14).                                             |
| D4  | Remove `ResolverRegistry` and publish with `OmegaConf` directly?                     | **No.** It would delete most of `registry.py`, but P7 to P9, publishing again after `clear_resolvers()` and the lazy optional resolvers are the value of the package beyond a list of functions.                 |
| D5  | Make `register` publish at once, so `register_resolvers()` is not needed?            | **No.** Two explicit steps are P7 and P8; the error of a forgotten call names the missing key.                                                                                                                   |
| D6  | Remove `has_resolver` (`key in registry.state`)?                                     | **No.** It costs three lines and mirrors OmegaConf; removing it improves nothing.                                                                                                                                |
| D7  | Require two arguments in `hya.add` and `hya.mul` so the result is never an argument? | **No.** It would not cover `hya.max` and would differ from `${x}`; P5 states the behaviour.                                                                                                                      |
| D8  | Convert the input of `hya.np.array` with `to_plain` too, for uniformity?             | **No.** It is already correct and the conversion is 2.4 times slower; the property test of P16 protects it.                                                                                                      |
| D9  | Move `pytest` out of the `all` extra (the built metadata of `hya[all]` requires it)? | **No for now.** The extra is generated from all extras by `hatchling-autoextras-hook`; removing the `testing` extra would break the use of `hya.testing`. Say in `get_started.md` that `all` includes it (PR 1). |
| D10 | Add `hya.abs`, `hya.round`, `hya.mod`, or expose `use_cache`?                        | **No.** Nothing in the documentation needs them; apply the rule of section 3.7 when a configuration does.                                                                                                        |

---

## 10. Not covered

- **Thread-safety** of OmegaConf's global resolver table.
- **Windows.** The classifiers are Linux and macOS; `hya.path` and the hashes of paths are checked
  with POSIX paths only. A path hashes to its string, which differs between platforms.
- **The Hydra release matrix.** P14 is checked against OmegaConf releases; only one Hydra example
  was run (1.3.2), and Hydra is not tested in CI.
- **The documentation snippets.** `inv test.doctest-markdown` runs `pycon` examples only, so F16 was
  invisible to it. Running every `python` block needs a fixture for files and Hydra; not proposed.
- **CI workflows, release process and tooling configuration**, aligned with `coola` in #787 to #789.

---

## Appendix: size of the package

| Item               | Lines today | Change                                       |
| ------------------ | ----------- | -------------------------------------------- |
| Top-level modules  | 1,081       | validation, `_encode_value`, tensor branches |
| `utils/config.py`  | 0           | new, one function and its docstring          |
| Executable lines   | about 200   | about 30 more (47 added, 15 removed)         |
| Public names added | n/a         | `to_plain`                                   |

The prototype counts exclude the docstrings that the pull requests add.
