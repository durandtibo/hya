# Properties

These are the rules `hya` guarantees. Each one is enforced by the code or by a test of the
repository. The [Design Choices](design.md) page explains the reasons and the trade-offs.

| #   | Property                      | Statement                                                                                                                                                                                                                                                                                                                                                                            |
| --- | ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| P1  | **Import is enough**          | `import hya` registers every available default resolver with OmegaConf. No other call is needed, and `register_resolvers()` publishes them again after `OmegaConf.clear_resolvers()`.                                                                                                                                                                                                |
| P2  | **Cheap import**              | `import hya` imports neither `numpy`, `torch` nor `braceexpand`, and emits no warning. The module of an optional resolver is imported on the first call of that resolver.                                                                                                                                                                                                            |
| P3  | **Namespaced**                | Every built-in key starts with `hya.`. Optional ones are grouped (`hya.np.*`, `hya.torch.*`). Nothing is registered outside this namespace.                                                                                                                                                                                                                                          |
| P4  | **Thin resolvers**            | A resolver is a standard library callable or a function of a few lines with one documented behaviour. No hidden state, no I/O beyond what its name says (`hya.path` touches the file system).                                                                                                                                                                                        |
| P5  | **Pure**                      | A resolver never modifies its arguments. A returned value can be an argument itself or one of its elements (`hya.add` of one value, `hya.max` of several values), exactly as `${x}` returns the node `x`: copy it before you mutate it.                                                                                                                                              |
| P6  | **Deterministic output**      | The same resolved arguments give the same output, including error messages (sorted, no set order), on every process and OmegaConf release. `hya.path` also depends on the file system (working directory, home directory, symbolic links), which is its purpose.                                                                                                                     |
| P7  | **Explicit, strict registry** | A `ResolverRegistry` is a key to callable map. `register` adds, `register_resolvers` publishes. Every entry, from `register`, `register_lazy` or the constructor, has a callable value and a key that every supported OmegaConf can interpolate; anything else raises at registration.                                                                                               |
| P8  | **Replace is explicit**       | `register_resolvers()` is idempotent. It never silently keeps a stale resolver: a key that changed since it was published, or that another source registered before the registry published it, is skipped with a warning unless `replace=True`.                                                                                                                                      |
| P9  | **One default registry**      | `get_default_registry()` returns one process-wide registry holding the built-in resolvers. It holds the same keys on every machine, whatever packages are installed. Users extend it or create their own registry.                                                                                                                                                                   |
| P10 | **Errors are OmegaConf's**    | A resolver raises standard exceptions only, so a failure surfaces as `InterpolationResolutionError` whose message names the original exception, found in the `__context__` chain (`__cause__` is `None`). A missing optional package says how to install it.                                                                                                                         |
| P11 | **Any value out**             | A resolver may return any Python object (`Path`, `ndarray`, `Tensor`, `dtype`, list). Such values are for use in code: for an array, a tensor or a data type, `OmegaConf.resolve` needs the `allow_objects` flag and `to_yaml` does not support them.                                                                                                                                |
| P12 | **Typed and documented**      | The package has a `py.typed` file, `pyright --verifytypes` scores 100 %, every public function, class, method and property is documented with a doctest and shown in the reference, every resolver is listed in the [resolvers](resolvers.md) page, and the documentation says nothing false.                                                                                        |
| P13 | **Keyword-only options**      | The options of the Python API are keyword-only (`exist_ok`, `replace`). The arguments of a resolver are positional, because the interpolation grammar has no keyword syntax; an optional argument of a resolver comes last and has a default.                                                                                                                                        |
| P14 | **Installs next to Hydra**    | `hya` accepts every OmegaConf release that a Hydra release accepts (`omegaconf>=2.2,<3.0`) and behaves the same on all of them. CI runs the tests on the oldest and the newest.                                                                                                                                                                                                      |
| P15 | **Composable**                | A resolver accepts the values OmegaConf gives it (`str`, `int`, `float`, `bool`, `None`, `list`, `dict`, `ListConfig`, `DictConfig`) and the output of another `hya` resolver (a `Path` for `hya.path`, a tensor, an array or a `torch.dtype` for `hya.torch.tensor`). In particular `hya.torch.tensor` takes a tensor, an array, and a data type as a `torch.dtype` or as its name. |
| P16 | **Resolved input**            | A resolver that reads a whole value (`hya.sha256`, `hya.iter_join`, `hya.np.array`, `hya.torch.tensor`) reads its **resolved** content: interpolations are resolved at any depth, and a missing value (`???`) raises `MissingMandatoryValue`.                                                                                                                                        |
| P17 | **Faithful hash**             | `hya.sha256` hashes the whole content of a value: a string as is, any other value as canonical JSON (sorted keys). Two such values with different JSON forms have different hashes, and a value without a JSON form raises instead of being hashed from a summary.                                                                                                                   |

## Details

- **P2.** The optional resolvers are registered lazily (`ResolverRegistry.register_lazy`): the key
  is always in the registry, and the module is imported when OmegaConf calls the resolver for the
  first time. `import hya` does not look for the packages on disk.
- **P7.** A key is made of names joined by dots, where a name is made of ASCII letters, digits and
  `_` and does not start with a digit. OmegaConf 2.3 and later can interpolate a `-` too, but
  OmegaConf 2.2 cannot, so `hya` rejects it (P14). A registry is independent of the other
  registries.
- **P8.** After `import hya`, the default resolvers are already published, so
  `registry.register_resolvers()` is silent. Overriding a built-in
  (`registry.register("hya.add", exist_ok=True)`) warns until `register_resolvers(replace=True)` is
  called. OmegaConf caches the resolved nodes of a configuration: `replace=True` does not clear the
  cache of the existing configurations (`OmegaConf.clear_cache(cfg)`).
- **P9.** The optional keys are registered whether or not the package is installed, so the registry
  has the same keys on every machine.
- **P10.** A missing configuration value (`???`) is reported by the exceptions of OmegaConf
  (`MissingMandatoryValue`, which the message names). `hya` adds no exception class of its own and
  no wrapper.
- **P10.** With a missing package, the resolver raises a `RuntimeError` that says how to install it
  (`pip install torch`); OmegaConf reports it as an `InterpolationResolutionError`.
- **P10.** With OmegaConf 2.4 and later, the validation of the annotations is off for the resolvers
  published by `hya`: the annotations are documentation for readers and type checkers, not a runtime
  contract.
- **P11.** Use such a value in code (`cfg.key`, or `OmegaConf.to_container(cfg, resolve=True)`).
  To resolve a whole configuration in place, give it the `allow_objects` flag, when you create it
  (`OmegaConf.create(..., flags={"allow_objects": True})`) or around the call
  (`with flag_override(cfg, "allow_objects", True): OmegaConf.resolve(cfg)`, with
  `from omegaconf import flag_override`).

## Limits

`hya` does not provide the following.

- **Thread-safety** of registering resolvers while OmegaConf resolves interpolations. The resolver
  table of OmegaConf is a global dictionary.
- **Detection of a conflicting registration.** A resolver that another source registers after `hya`
  published the same key is not detected: it needs the private `BaseContainer._resolvers` of
  OmegaConf, which changes between releases.
- **Type-tagged hashes.** `hya.sha256` of the string `[1]` equals the hash of the list `[1]`, an
  integer key equals the same string key, and a path or an enum equals its string in JSON. A mapping
  that mixes key types cannot be sorted and raises.
- **Special parameters of lazy resolvers.** A resolver registered with `register_lazy` cannot
  receive `_root_`, `_parent_` or `_node_`: OmegaConf reads them from the signature, which is not
  known before the import.
- **Caching of the output of the resolvers.** OmegaConf does not cache it: every access of an
  interpolation calls the resolver again.
- **Export of objects.** `OmegaConf.to_yaml(resolve=True)` does not support an array, a tensor or
  a data type, and `OmegaConf.resolve` needs the `allow_objects` flag for them (P11).
