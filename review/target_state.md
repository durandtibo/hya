# `hya`: target state and the changes to reach it

This document defines the properties `hya` should guarantee, the design that gives them, and the
changes to make to the current code (`main`, `e398f72`, 0.5.0a0) to get there. The latest release
is `v0.4.0`. It replaces the previous review, whose plan is implemented (PRs #793 to #800).

Items tagged **[verified]** were reproduced; **[reading]** comes from the code or the
documentation. This review changes no file of `src`, `tests` or `docs`.

## 1. Properties of the package

These are the rules `hya` guarantees in the target state. Each one is made true by the code and
checked by a test (section 8.2). The numbers are those of `docs/docs/properties.md`. The last
column compares with that page: **kept** (same statement, true today), **fixed** (same statement,
not true today) or **changed** (the statement changes).

| #   | Property                      | Statement                                                                                                                                                                                                                                                                                                                                                                                                    | Enforced by                           | Status  |
| --- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------- | ------- |
| P1  | **Import is enough**          | `import hya` publishes every default resolver to OmegaConf. No other call is needed, and `register_resolvers()` publishes them again after `OmegaConf.clear_resolvers()`.                                                                                                                                                                                                                                    | `hya/__init__.py`, `ResolverRegistry` | kept    |
| P2  | **Cheap import**              | `import hya` imports neither `numpy`, `torch` nor `braceexpand`, and emits no warning when no other source has registered a `hya.` key. The module of an optional resolver is imported on the first call of that resolver.                                                                                                                                                                                   | `register_lazy`, import contracts     | changed |
| P3  | **Namespaced**                | Every built-in key starts with `hya.`. Optional ones are grouped (`hya.np.*`, `hya.torch.*`). Nothing is registered outside this namespace.                                                                                                                                                                                                                                                                  | `hya.default`                         | kept    |
| P4  | **Thin resolvers**            | A resolver is a standard library callable or a function of a few lines with one documented behaviour. No hidden state, no I/O beyond what its name says. A resolver written by `hya` raises on an input it cannot honour instead of guessing or dropping a part of it.                                                                                                                                       | the resolvers                         | changed |
| P5  | **Pure**                      | A resolver never modifies its arguments. A resolver written by `hya` returns a new list, dictionary or array and never a container of an argument; `hya.torch.tensor` returns a copy (`hya.add` of a single other object returns it). A standard library callable can return an argument or one of its elements (`hya.max` of several values), as `${x}` returns the node `x`: copy it before you mutate it. | the resolvers                         | changed |
| P6  | **Deterministic output**      | The same resolved arguments give the same output, including error messages (sorted, no set order), on every process and OmegaConf release. The type of the result of a resolver written by `hya` does not depend on how an argument is written (a literal or a reference). `hya.path` also depends on the file system, which is its purpose.                                                                 | the resolvers                         | changed |
| P7  | **Explicit, strict registry** | A `ResolverRegistry` is a key to callable map. `register` adds, `register_resolvers` publishes. The constructor takes a mapping or `None`. Every entry has a callable value and a key that every supported OmegaConf can interpolate, and every lazy target is `module:function` made of names; anything else raises at registration.                                                                        | `ResolverRegistry`                    | changed |
| P8  | **Replace is explicit**       | `register_resolvers()` is idempotent. A key that changed since it was published, or that another source registered before the registry published it, is skipped unless `replace=True`; one warning lists the skipped keys, after the other keys are published. With `replace=True`, every key of the registry is published, whatever OmegaConf holds.                                                        | `register_resolvers`                  | changed |
| P9  | **One default registry**      | `get_default_registry()` returns one process-wide registry holding the built-in resolvers. It holds the same keys on every machine, whatever packages are installed. Users extend it or create their own registry.                                                                                                                                                                                           | `functools.cache`                     | kept    |
| P10 | **Errors are OmegaConf's**    | A resolver raises standard exceptions only, so a failure surfaces as `InterpolationResolutionError` whose message names the original exception, found in the `__context__` chain (`__cause__` is `None`). A missing optional package says how to install it.                                                                                                                                                 | the resolvers                         | kept    |
| P11 | **Any value out**             | A resolver may return any Python object (`Path`, `ndarray`, `Tensor`, `dtype`, list). Such values are for use in code: for an array, a tensor or a data type, `OmegaConf.resolve` needs the `allow_objects` flag and `to_yaml` does not support them.                                                                                                                                                        | documentation                         | kept    |
| P12 | **Typed and documented**      | `py.typed`, `pyright --verifytypes` at 100 %, every public function, class, method and property documented with a doctest and shown in the reference, every default key listed in `docs/resolvers.md`, and the documentation says nothing false.                                                                                                                                                             | CI, tests                             | fixed   |
| P13 | **Keyword-only options**      | The options of the Python API are keyword-only (`exist_ok`, `replace`). The arguments of a resolver are positional (the grammar has no keyword syntax); an optional argument comes last and has a default.                                                                                                                                                                                                   | signatures                            | kept    |
| P14 | **Installs next to Hydra**    | `hya` accepts every OmegaConf release that a Hydra release accepts (`omegaconf>=2.2,<3.0`) and behaves the same on all of them. CI runs the tests on the oldest and the newest.                                                                                                                                                                                                                              | `_publish`, CI matrix                 | kept    |
| P15 | **Composable**                | A resolver written by `hya` accepts the values OmegaConf gives it, from a writable or a read-only configuration, and the output of another `hya` resolver of a type it takes, without a warning. `hya.np.array` and `hya.torch.tensor` take a tensor (on the CPU, without gradient for NumPy) and an array.                                                                                                  | the resolvers                         | fixed   |
| P16 | **Resolved input**            | A resolver written by `hya` that reads a list or a mapping (`hya.add`, `hya.sha256`, `hya.iter_join`, `hya.np.array`, `hya.torch.tensor`) reads its **resolved** content: interpolations are resolved at any depth, and a missing value (`???`) raises `MissingMandatoryValue`.                                                                                                                              | `hya.utils.config.to_plain`           | fixed   |
| P17 | **Faithful hash**             | `hya.sha256` hashes the whole content of a value: a string as is, any other value as canonical JSON (sorted keys, no space, non-ASCII escaped). Two such values with different JSON forms have different hashes, and a value without a JSON form (a non-finite float included) raises.                                                                                                                       | `sha256_resolver`                     | fixed   |

**Not guaranteed**, and documented as such:

- **Thread-safety** of registering while OmegaConf resolves (OmegaConf's resolver table is a global
  dictionary).
- **Detection of a registration made after `hya`'s.** `register_resolvers()` without `replace=True`
  keeps silently a resolver that another source registered over a published key: detecting it needs
  the private `BaseContainer._resolvers`.
- **Type-tagged hashes.** `hya.sha256` of the string `[1]` equals the hash of the list `[1]`, an
  integer key equals the same string key, and an enum that is also an `int` or a `str` equals its
  value. A mapping that mixes key types cannot be sorted and raises.
- **Special parameters of lazy resolvers** (`_root_`, `_parent_`, `_node_`): OmegaConf reads them
  from the signature, which is not known before the import.
- **Warnings of the libraries** for inputs they discourage, for example `torch.tensor` of a list of
  NumPy arrays.
- **Caching.** OmegaConf calls the resolver at every access.

### Constraints of the design

1. **Simple and easy to maintain.** One registry, one registration rule, thin resolvers, one shared
   helper. No change adds a class, a module or a public name.
2. **Breaking changes are accepted.** The future state matters more than the past one: no alias, no
   deprecation period. The release notes list the changes (section 5).
3. **The rules of `CLAUDE.md`**: lazy optional packages with fallbacks, shared helpers public in
   `hya.utils`, keyword-only options, no ignored lint or type issue.
4. **Behaviour before size.** A change is kept only if it fixes a reproduced defect or makes a
   property true.

---

## 2. Where `main` stands

**The finding in one sentence:** the architecture is right and every gate is green, but two calls
can **do the wrong thing without any error** (`hya.np.array` of a mapping,
`register_resolvers(replace=True)`), and a few edges of the resolvers contradict P4, P6, P7, P15 or
P17.

Gates on `main` **[verified]** (Python 3.14, OmegaConf 2.4.0, NumPy 2.5.5, PyTorch 2.15.0, macOS):
590 tests pass and 6 are skipped (missing-package cases), coverage of `src` is 100 %, 28 doctests
pass, `ruff`, `ty` and `pyright --verifytypes` (100 %) pass, the 5 import contracts hold,
`tests/package/checks.py --extra all` has no failure, `inv doc.build` and
`inv test.doctest-markdown` pass. So no existing gate sees the findings below. The probes that
depend on OmegaConf were repeated on 2.2.1 and 2.3.1 where noted, in throw-away environments.

### 2.1 Silent wrong results

| #   | Finding                                                                                                                                                                                                                                                                                                                                                                  | Property | Status                             |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- | ---------------------------------- |
| F1  | **`hya.np.array` of a mapping node returns an array of its keys**: `x: {a: "???"}` gives `array(['a'])`. The values are dropped and the missing value is ignored. A literal mapping gives an object array instead, and `hya.torch.tensor` raises.                                                                                                                        | P16, P6  | **[verified]** 2.2.1, 2.3.1, 2.4.0 |
| F2  | **`register_resolvers(replace=True)` ignores a key the registry already published.** After another source replaces it, `replace=True` publishes nothing and says nothing: the other resolver stays. The docstring says the resolvers "replace the resolvers that OmegaConf already has"; P8 says a stale resolver is never kept silently.                                | P8       | **[verified]** 2.2.1, 2.3.1, 2.4.0 |
| F3  | **`hya.sha256` hashes non-finite floats** as `NaN` and `Infinity`, which are not JSON. P17 says a value without a JSON form raises.                                                                                                                                                                                                                                      | P17      | **[verified]** 2.2.1, 2.3.1, 2.4.0 |
| F4  | **`hya.path` accepts what it cannot convert.** `''` and `file:` give the working directory (an empty `${data_dir}` points at it); `s3://b/k` and `http://host/path` give `<cwd>/s3:/b/k`; `file:///a%ff` silently becomes `/a` followed by the replacement character. In the other direction, `file://LOCALHOST/a` is rejected although a host name is case-insensitive. | P4       | **[verified]** 2.4.0               |

The plain-path reading of `http://host/path` is tested today
(`test_path_resolver_url_is_not_parsed_when_it_is_not_a_file_url`) and documented ("any other
string is a plain path"): changing it is a design change, not only a bug fix (D4).

### 2.2 `hya.add` and composition

| #   | Finding                                                                                                                                                                                                                                                       | Property | Status                             |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------- | ---------------------------------- |
| F5  | **The type of `hya.add` of lists depends on how they are written**: `${hya.add:[0],[1]}` returns a `list`, `${hya.add:[0],${x}}` a `ListConfig`, and `${hya.add:${x}}` the node `x` itself, so mutating the result mutates the configuration.                 | P5, P6   | **[verified]** 2.2.1, 2.3.1, 2.4.0 |
| F6  | **`hya.add` fails on a read-only configuration**: `ReadonlyConfigError raised while resolving interpolation`, because `ListConfig.__add__` copies the flags of the node.                                                                                      | P15      | **[verified]** 2.2.1, 2.3.1, 2.4.0 |
| F7  | `hya.add` of two lists of 10,000 values takes 420 ms per access; adding the resolved plain lists takes 51 ms.                                                                                                                                                 | n/a      | **[verified]** 2.4.0               |
| F8  | **`${hya.np.array:${t}}` with `t` a tensor emits a `DeprecationWarning`** (`__array__ implementation doesn't accept a copy keyword`). With warnings as errors the interpolation fails. The same problem was fixed for `hya.torch.tensor` of a tensor in #796. | P15      | **[verified]** 2.4.0               |

### 2.3 Edges of the registry

| #   | Finding                                                                                                                                                                                                                                                                              | Property | Status         |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------- | -------------- |
| F9  | The constructor accepts any falsy object (`ResolverRegistry([])`, `ResolverRegistry(0)`), and a list of pairs raises an `AttributeError` about `items`.                                                                                                                              | P7       | **[verified]** |
| F10 | `register_lazy` raises an `AttributeError` for a target that is not a string, and accepts `.numpy:to_array_resolver` and `a b:c`, which fail on the first call.                                                                                                                      | P7       | **[verified]** |
| F11 | `register_resolvers()` warns once per skipped key, during the loop. With warnings as errors it stops half way (of `z.a`, `z.b`, `z.c` with `z.b` taken, `z.c` is not published). Importing `hya` again after removing it from `sys.modules` emits one warning for every default key. | P8       | **[verified]** |

### 2.4 Documentation, tests and dead code

| #   | Finding                                                                                                                                                                                                                                                      | Status         |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------- |
| F12 | `resolvers.md` and the docstring of `sha256_resolver` say an enum is written as its string. An `IntEnum` or a `str` enum is written as its **value** (`str(D.A)` is `D.A`, the hash is the one of `"a"`).                                                    | **[verified]** |
| F13 | `default_image: ${hya.np.array:${data.shape}}` (`resolvers.md`) and `dummy_input: ${hya.torch.tensor:${data.input_shape}}` (`user_guide.md`) read as an image or an input **of that shape**; the result is the three shape values (`tensor([3, 224, 224])`). | **[verified]** |
| F14 | The readme gives `pip install hya[all]` without quotes: zsh answers `no matches found`.                                                                                                                                                                      | **[verified]** |
| F15 | The circular reference example of `user_guide.md` defines `x` and `y` twice in one YAML block, which cannot be loaded (the "type errors" block does the same with `result`).                                                                                 | **[verified]** |
| F16 | P12 says every resolver is listed in `resolvers.md`, and no test checks it. `tests/integration/test_reference.py` checks a hand-written list of modules.                                                                                                     | **[reading]**  |
| F17 | `hya.resolvers` defines a `logger` that nothing uses.                                                                                                                                                                                                        | **[reading]**  |

### 2.5 Right today, must not regress

All the default keys resolve for the documented inputs. Apart from F13 and F15, the single-file YAML
examples of `index.md`, `user_guide.md` and `resolvers.md` resolve to the documented values, and an
application built from the multi-config Hydra example of the user guide runs with `hydra-core` 1.3.2
**[verified]**. `import hya` is free of warnings and of optional imports and costs about 16 ms on
top of OmegaConf. The default registry is a singleton with the same keys on every machine.
`register_resolvers()` is idempotent and publishes again after `clear_resolvers()`.

---

## 3. Target architecture

The architecture does not change, and no module or public name is added.

```text
src/hya/
├── __init__.py        # exports; publishes the default resolvers (P1)
├── registry.py        # ResolverRegistry, _publish (only place that knows the OmegaConf version)  [changed]
├── default.py         # get_default_registry + the two tables (built-in, optional)
├── resolvers.py       # add, mul, ceildiv, pi, iter_join, sha256, path                             [changed]
├── braceexpand.py     # braceexpand_resolver
├── numpy.py           # to_array_resolver                                                          [changed]
├── torch.py           # to_tensor_resolver, torch_dtype_resolver
├── imports.py         # validate_*/is_*_available
├── testing.py         # pytest markers for the optional packages
├── py.typed
└── utils/
    ├── config.py      # to_plain
    └── fallback/      # fake modules for the guarded imports
```

### 3.1 The contract of a resolver written by `hya`

A standard library resolver is the callable itself, with its behaviour (P4). A resolver written by
`hya` follows four rules:

1. **Read resolved input.** An argument that is a list or a mapping goes through
   `hya.utils.config.to_plain` before it is used (P16). This one rule fixes F1 and F5 to
   F7: no resolver computes on a configuration node.
2. **Return a new list, dictionary, array or tensor** (P5).
3. **Raise rather than guess or drop** a part of the input (P4).
4. **Keep no state** (P6).

`hya.mul` and `hya.ceildiv` take numbers and `hya.path` takes one path, so rule 1 does not apply to
them.

### 3.2 `hya.add` (F5 to F7)

```python
def add_resolver(first: Any, *others: Any) -> Any:
    return reduce(operator.add, map(to_plain, others), to_plain(first))
```

Lists give a new plain `list`, whatever the way they are written. Numbers and strings are
unchanged. `${hya.add:${x}}` returns a copy of `x`. A nested missing value raises at any depth. The
elements of the result are the resolved values: it no longer holds interpolations.

### 3.3 `hya.np.array` (F1, F8)

```python
def to_array_resolver(data: ArrayLike, dtype: str | None = None) -> np.ndarray:
    validate_numpy()
    return np.asarray(to_plain(data), dtype=dtype).copy(order="K")
```

- A mapping node is converted like a literal mapping (NumPy's object array), so `???` raises and no
  value is dropped.
- `np.asarray` does not pass the `copy` argument that `Tensor.__array__` does not accept, and
  `copy` keeps the result independent of an input array (P5), with its memory order.
- `hya.torch.tensor` already follows the contract and does not change.

### 3.4 `hya.sha256` (F3)

```python
value = json.dumps(
    value, sort_keys=True, separators=(",", ":"), allow_nan=False, default=_encode_value
)
```

A non-finite float raises a `ValueError`. Every other hash is unchanged. The format does not change
otherwise; the documentation states it precisely (non-ASCII characters are escaped, and an enum that
is also an `int` or a `str` is written as its value, F12).

### 3.5 `hya.path` (F4)

```python
# A URL with an authority, such as "s3://bucket": it is never a local path
_URL: re.Pattern[str] = re.compile(r"\s*[A-Za-z][A-Za-z0-9+.-]+://")


def path_resolver(path: str | os.PathLike[str]) -> Path:
    path = os.fspath(path)
    if not path:
        msg = "The path is empty"
        raise ValueError(msg)
    url = urlparse(path)
    if url.scheme == "file":
        if url.netloc.lower() not in ("", "localhost") or "?" in path or "#" in path:
            msg = f"A file URL with a host, a query or a fragment is not supported: '{path}'"
            raise ValueError(msg)
        if not url.path:
            msg = f"The file URL has no path: '{path}'"
            raise ValueError(msg)
        path = unquote(url.path, errors="strict")
    elif _URL.match(path):
        msg = f"Only a file URL can be converted to a path, but received '{path}'"
        raise ValueError(msg)
    return Path(path).expanduser().resolve()
```

A scheme needs two characters or more, so a Windows drive (`C://x`) is not read as a URL. A relative
file URL (`file:my/path`), a plain path with a colon (`a:b`) and `.` stay valid.

### 3.6 `ResolverRegistry` (F2, F9 to F11)

```python
def __init__(self, state: Mapping[str, Callable[..., Any]] | None = None) -> None:
    self._state: dict[str, Callable[..., Any]] = {}
    self._published: dict[str, Callable[..., Any]] = {}
    if state is not None:
        if not isinstance(state, Mapping):
            msg = f"The state must be a mapping, but received {type(state).__name__}"
            raise TypeError(msg)
        for key, resolver in state.items():
            self.register(key)(resolver)


def register_resolvers(self, *, replace: bool = False) -> None:
    skipped: list[str] = []
    for key, resolver in self._state.items():
        if not replace and OmegaConf.has_resolver(key):
            if self._published.get(key) is not resolver:
                skipped.append(key)
            continue
        _publish(key, resolver, replace=replace)
        self._published[key] = resolver
    if skipped:
        keys = ", ".join(f"'{key}'" for key in skipped)
        warnings.warn(
            f"A resolver is already registered in OmegaConf for {keys}: not replaced. "
            "Use register_resolvers(replace=True) to replace it.",
            stacklevel=2,
        )
```

With `replace=True` there is no shortcut: every key is published. Publishing the same callable
again changes nothing, so the call stays idempotent.

`register_lazy` checks its target before it registers it:

```python
if not isinstance(target, str):
    msg = f"The target must be a string, but received {type(target).__name__}"
    raise TypeError(msg)
module_name, _, function_name = target.partition(":")
if not _KEY.fullmatch(module_name) or not function_name.isidentifier():
    ...  # the ValueError of today
```

`_KEY` is the pattern of dotted ASCII names that keys use already. The existence of the module and
of the function is still checked on the first call, which is what lazy means.

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

The signatures do not change.

```python
import hya

hya.ResolverRegistry(state=None)  # a mapping or None
hya.get_default_registry()

registry.register(key, *, exist_ok=False)  # decorator factory
registry.register_lazy(key, target, *, exist_ok=False)
registry.register_resolvers(*, replace=False)
registry.has_resolver(key)
registry.state  # read-only mapping

hya.utils.config.to_plain(value)
```

## 5. Behaviour changes for users

| Change                                          | Before                             | After                               | What the user does              | Breaking |
| ----------------------------------------------- | ---------------------------------- | ----------------------------------- | ------------------------------- | -------- |
| `register_resolvers(replace=True)`              | skips the keys it published before | publishes every key                 | nothing                         | yes      |
| Warning of `register_resolvers()`               | one per skipped key                | one that lists the keys             | update a filter that counts     | yes      |
| `hya.np.array` of a mapping node                | array of the keys                  | object array, as for a literal      | `${oc.dict.keys:x}` for keys    | yes      |
| `hya.np.array` with a nested `???` in a mapping | a result                           | `MissingMandatoryValue`             | set the value                   | yes      |
| `hya.sha256` of `nan` or `inf`                  | a hash                             | `ValueError`                        | hash a string                   | yes      |
| `hya.add` of lists                              | `list` or `ListConfig`             | `list` of resolved values           | use `cfg.key[0]`, not node APIs | yes      |
| `hya.add` of one list                           | the node itself                    | a copy                              | mutate `x` directly             | yes      |
| `hya.path` of `''` or `file:`                   | the working directory              | `ValueError`                        | write `.`                       | yes      |
| `hya.path` of `scheme://...` other than `file:` | a path under the working directory | `ValueError`                        | write `./scheme:/...`           | yes      |
| `hya.path` of a file URL with invalid UTF-8     | replacement characters             | `ValueError` (`UnicodeDecodeError`) | fix the URL                     | yes      |
| `hya.path` of `file://LOCALHOST/a`              | `ValueError`                       | `/a`                                | nothing                         | no       |
| Constructor of a registry with a non-mapping    | accepted or `AttributeError`       | `TypeError`                         | pass a mapping                  | yes      |
| `register_lazy` with an invalid target          | accepted or `AttributeError`       | `ValueError` or `TypeError`         | fix the target                  | yes      |

`v0.5.0` is not released yet, so its release notes take this table **and** the changes of the
previous plan (PRs #793 to #800).

---

## 6. Evidence: a prototype of the changes

The code of section 3 (without docstring updates) was applied to a throw-away copy of `src/hya`;
the script and the probes are not part of the repository. **[verified]**

| Check                                                             | Result                                                           |
| ----------------------------------------------------------------- | ---------------------------------------------------------------- |
| Probes of F1 to F6 and F8 to F11, with warnings as errors         | fixed, with the same results on OmegaConf 2.2.1, 2.3.1 and 2.4.0 |
| Existing unit and integration tests (2.4.0)                       | 588 pass, 6 skipped, 2 fail                                      |
| `test_path_resolver_url_is_not_parsed_when_it_is_not_a_file_url`  | fails as intended (3.5, D4)                                      |
| `test_add_resolver_of_one_value_returns_the_node_itself`          | fails as intended (3.2)                                          |
| Existing doctests                                                 | 28 pass                                                          |
| `ruff check`, `ruff format --check`, `ty check`, pyright on `src` | pass (`--verifytypes` 100 %), with no `noqa`                     |
| Import contracts                                                  | 5 kept                                                           |
| Size of the change in `src`                                       | 41 lines added, 19 removed                                       |

Cost per access of an interpolation over lists of 10,000 values (OmegaConf 2.4.0):

| Resolver                   | `main` | Prototype |
| -------------------------- | ------ | --------- |
| `hya.np.array` (list node) | 11 ms  | 26 ms     |
| `hya.add` (two list nodes) | 420 ms | 51 ms     |

`hya.np.array` pays for resolving the node first, as `hya.sha256`, `hya.iter_join` and
`hya.torch.tensor` already do (about 25 ms each). The previous review refused this cost because the
resolver was thought to be correct; F1 shows it is not (D1).

---

## 7. Changes to reach the target state

One branch and one pull request per logical change. The pull requests are stacked in the order of
the table: the changes do not depend on each other, but several edit the same pages. Once one is
merged, the next one is retargeted to `main` and `origin/main` is merged into it. Each one updates
the pages it affects (`properties.md`, `design.md`, `resolvers.md`, `user_guide.md`, docstrings),
adds its tests, and states its behaviour changes. They are listed by value.

| Order    | Branch                               | Change                                                                                                                                    | Properties | Breaking |
| -------- | ------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------- | ---------- | -------- |
| 1 (#803) | `bugfix/resolve-mapping-in-np-array` | F1, F8: `to_plain` and the copy in `to_array_resolver`; add `hya.np.array` to the P16 statement of the pages.                             | P15, P16   | yes      |
| 2 (#804) | `bugfix/replace-published-resolvers` | F2, F11: the loop of `register_resolvers` and its single warning; P2 and P8.                                                              | P2, P8     | yes      |
| 3 (#805) | `bugfix/reject-non-finite-hash`      | F3, F12: `allow_nan=False`; the exact format of the hash and the enum note.                                                               | P17        | yes      |
| 4 (#807) | `bugfix/return-plain-list-from-add`  | F5 to F7: `to_plain` in `add_resolver`; the contract of section 3.1 in `design.md`; P5, P6, P16.                                          | P5, P6     | yes      |
| 5 (#808) | `bugfix/reject-invalid-path`         | F4: section 3.5; P4.                                                                                                                      | P4         | yes      |
| 6 (#809) | `bugfix/validate-registry-arguments` | F9, F10: constructor and `register_lazy`; P7.                                                                                             | P7         | yes      |
| 7 (#810) | `docs/fix-resolver-examples`         | F13 to F15: rename or replace the shape examples, quote `'hya[all]'`, split the YAML blocks.                                              | P12        | no       |
| 8        | `test/check-resolver-catalogue`      | F16: every default key is in `resolvers.md`; the reference lists every module found with `pkgutil`, except `hya.utils` and its fallbacks. | P12        | no       |
| 9        | `chore/remove-unused-logger`         | F17.                                                                                                                                      | n/a        | no       |

After they are merged and CI is green, the maintainer sets the version `0.5.0` and creates the exact
tag `v0.5.0` with the release notes of section 5.

---

## 8. Tests and gates

### 8.1 Tests of each change

Unit tests mirror the source tree, with one behaviour per test and literal expected values. Each bug
fix has a regression test that fails with `git stash push src`.

| Order | Unit tests                                                                                                                                                                              | Integration tests (real packages, no patching)                                                           |
| ----- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- |
| 1     | mapping node, literal mapping, nested `???`, input array not shared, memory order kept, tensor with and without `dtype` without a warning.                                              | `${hya.np.array:${hya.torch.tensor:[1,2]}}`; `x: {a: "???"}` raises.                                     |
| 2     | `replace=True` publishes a key published before; second call silent; one warning with every skipped key; all other keys published when warnings are errors.                             | another source replaces a published key, `replace=True` restores it, on each OmegaConf of the CI matrix. |
| 3     | parametrised `nan`, `inf`, `-inf`, nested in a list and in a mapping; the string `"nan"` hashes; literal hash of an `IntEnum`, a `str` enum and a non-ASCII list.                       | the interpolation raises.                                                                                |
| 4     | literal and node operands in both orders give a `list`; one operand is copied; input not modified; nested `???`; numbers and strings unchanged. Replace the test that expects the node. | read-only configuration; relative interpolation inside an operand.                                       |
| 5     | `''`, `file:`, `s3://`, a URL after spaces, invalid UTF-8, `LOCALHOST`; `.`, `a:b`, `C://x`, `file:my/path` accepted. Replace the test of the `http` URL.                               | `${hya.path:''}` raises.                                                                                 |
| 6     | constructor with a list, `0`, a string; `None` and an empty mapping; non-string target; relative and invalid module names; state unchanged after an error.                              | covered by the existing registry tests.                                                                  |

PRs 7 to 9 change documentation, tests and one unused name; PR 8 is itself the test.

### 8.2 Test of each property

| #              | Test                                                                                            |
| -------------- | ----------------------------------------------------------------------------------------------- |
| P1, P2, P3, P9 | existing: `tests/integration/test_default.py`, `test_registry.py`, `tests/unit/test_default.py` |
| P4             | code review; PR 5 adds the rejected paths                                                       |
| P5, P6         | existing purity tests; PR 4 adds the type and copy cases                                        |
| P7             | existing key and value tests; PR 6                                                              |
| P8             | existing registry tests; PR 2                                                                   |
| P10, P11, P13  | existing unit tests, doctests and signatures                                                    |
| P12            | CI (`pyright`, doctests, `doc.build`), `test_reference.py`; PR 8                                |
| P14            | the `omegaconf` matrix of `dev/config/package_versions.json`                                    |
| P15            | existing tensor tests; PRs 1 and 4                                                              |
| P16            | one parametrised test over the five resolvers (`???` and a nested interpolation), PRs 1 and 4   |
| P17            | existing literal hashes; PR 3                                                                   |

### 8.3 Gates (all of `CLAUDE.md`)

```shell
.venv/bin/ruff check src tests && .venv/bin/ruff format src tests
.venv/bin/inv types.check
VIRTUAL_ENV=$PWD/.venv PATH=$PWD/.venv/bin:$PATH .venv/bin/pyright --verifytypes hya --ignoreexternal
.venv/bin/pytest tests/unit tests/integration -q --cov=hya --cov-report=term-missing
.venv/bin/python -m pytest --xdoctest src/hya
```

Expected after each pull request: all green, coverage 100 %, no `noqa`, no `pragma: no cover` added.
The five import contracts hold (`hya.numpy` imports `hya.utils.config`, which is allowed).

---

## 9. Decisions for the maintainers

Each has a recommendation; the target state assumes it.

| #   | Question                                                                                   | Recommendation                                                                                                                                                                                                                                   |
| --- | ------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| D1  | Convert the input of `hya.np.array` with `to_plain`, although it is slower?                | **Yes** (it reverses the previous D8). Treating only `DictConfig` apart would miss a mapping nested in a list and add a second rule.                                                                                                             |
| D2  | `hya.np.array` of a mapping: object array or error?                                        | **Object array**, NumPy's behaviour (P4), now the same for a node and a literal.                                                                                                                                                                 |
| D3  | `hya.add` returns plain lists: convert in `hya.mul`, `hya.max` or `hya.sum` too?           | **No.** `hya.mul` takes numbers (repeating a list stays unsupported), and the others are standard library callables with no wrapper (P4).                                                                                                        |
| D4  | Should `hya.path` reject `scheme://` strings?                                              | **Yes.** A remote URL turned into a local path is never what the configuration means, and the failure appears far from the cause. Alternative: keep "any other string is a plain path" and fix only the empty path, the UTF-8 and the host case. |
| D5  | Enter the enums of a hash as their string, so that `IntEnum` follows the other enums?      | **No.** `json` writes them as values before `default` is called, so it needs a traversal of the whole value to change a rare case. Document it.                                                                                                  |
| D6  | Write non-ASCII characters as is in the hash (`ensure_ascii=False`)?                       | **No.** It changes existing hashes for no defect. Pin the escaped form with a literal test.                                                                                                                                                      |
| D7  | Reject a string or a mapping in `hya.iter_join` (it joins the characters or the keys)?     | **No.** It is what `separator.join` does (P4). Document it.                                                                                                                                                                                      |
| D8  | Replace `register_lazy` and the fallback modules by imports inside the optional resolvers? | **No.** It would remove code and the special-parameter limit, but a local import violates `ruff` `PLC0415` (checked), which `CLAUDE.md` forbids to ignore, and `importlib.import_module` loses the types.                                        |
| D9  | Remove `ResolverRegistry` and publish with `OmegaConf` directly?                           | **No.** P7 to P9, publishing again after `clear_resolvers()` and the lazy resolvers are the value of the package beyond a list of functions.                                                                                                     |
| D10 | Add resolvers (`hya.abs`, `hya.round`, `hya.mod`) or expose `use_cache`?                   | **No.** Nothing in the documentation needs them; apply the rule of section 3.7 when a configuration does.                                                                                                                                        |

---

## 10. Not covered

- **Thread-safety** of OmegaConf's global resolver table.
- **Two registries holding the same callable.** The second `register_resolvers()` warns, because
  telling the two apart from a foreign resolver needs the private table of OmegaConf.
- **Windows.** The classifiers are Linux and macOS; paths and their hashes are checked with POSIX
  paths only.
- **Devices.** Tensors on an accelerator were not probed.
- **The Hydra release matrix.** Only `hydra-core` 1.3.2 was run, and Hydra is not tested in CI.
- **The YAML examples of the documentation** are not run by any gate (`inv test.doctest-markdown`
  runs `pycon` examples only). F13 and F15 were found with a throw-away script; testing them needs
  expected values in a machine-readable form, which is not proposed.
- **CI workflows, release process and tooling configuration**, aligned with `coola` in #787 to #789.

---

## Appendix: size of the change

| Item               | Change                                                                      |
| ------------------ | --------------------------------------------------------------------------- |
| `registry.py`      | argument checks; no shortcut in the publication loop with `replace=True`    |
| `resolvers.py`     | `to_plain` in `add`, `allow_nan=False`, path checks, unused logger removed  |
| `numpy.py`         | two lines and one import                                                    |
| Executable lines   | 41 added, 19 removed in the prototype, docstrings excluded from the changes |
| Public names added | none                                                                        |
