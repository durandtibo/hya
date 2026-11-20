# Properties

These are the rules `hya` guarantees. Each one is enforced by the code or by a test of the
repository.

| #   | Property                   | Statement                                                                                                                                                                                                                                                                                                                      |
| --- | -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| P1  | **Import is enough**       | `import hya` registers every available default resolver with OmegaConf. No other call is needed, and `register_resolvers()` publishes them again after `OmegaConf.clear_resolvers()`.                                                                                                                                          |
| P2  | **Cheap import**           | `import hya` imports neither `numpy`, `torch` nor `braceexpand`, and emits no warning. The module of an optional resolver is imported on the first call of that resolver.                                                                                                                                                      |
| P3  | **Namespaced**             | Every built-in key starts with `hya.`. Optional ones are grouped (`hya.np.*`, `hya.torch.*`). Nothing is registered outside this namespace.                                                                                                                                                                                    |
| P4  | **Thin resolvers**         | A resolver is a standard library callable or a function of a few lines with one documented behaviour. No hidden state, no I/O beyond what its name says (`hya.path` touches the file system).                                                                                                                                  |
| P5  | **Pure**                   | A resolver never modifies its arguments. Interpolating a config node into a resolver cannot change the config.                                                                                                                                                                                                                 |
| P6  | **Deterministic output**   | The same arguments give the same output, including inside error messages (sorted, no set order).                                                                                                                                                                                                                               |
| P7  | **Explicit registry**      | A `ResolverRegistry` is a plain key to callable map. `register` adds, `register_resolvers` publishes to OmegaConf. Registries are independent of each other.                                                                                                                                                                   |
| P8  | **Replace is explicit**    | `register_resolvers()` is idempotent. It never silently keeps a stale resolver: a key that changed since it was published, or that another source registered before the registry published it, is skipped with a warning unless `replace=True`.                                                                                |
| P9  | **One default registry**   | `get_default_registry()` returns one process-wide registry holding the built-in resolvers. It holds the same keys on every machine, whatever packages are installed. Users extend it or create their own registry.                                                                                                             |
| P10 | **Errors are OmegaConf's** | A failing resolver surfaces as `InterpolationResolutionError`. The message names the original exception and the original exception is in its `__context__` chain (not its `__cause__`). `hya` adds no wrapper of its own. A missing optional package gives an error that says how to install it, through an interpolation too. |
| P11 | **Any value out**          | A resolver may return any Python object (`Path`, `ndarray`, `Tensor`, `dtype`, list). Such values are for use in code and are not meant for `OmegaConf.to_yaml`.                                                                                                                                                               |
| P12 | **Typed and documented**   | The package has a `py.typed` file, `pyright --verifytypes` scores 100 %, every public name is documented with a doctest, and every resolver is listed in the [resolvers](resolvers.md) page.                                                                                                                                   |
| P13 | **Keyword-only options**   | The options of the Python API are keyword-only (`exist_ok`, `replace`). The arguments of a resolver are positional, because the interpolation grammar has no keyword syntax; an optional argument of a resolver comes last and has a default.                                                                                  |
| P14 | **Installs next to Hydra** | `hya` accepts every OmegaConf release that a Hydra release accepts (`omegaconf>=2.2,<3.0`). CI runs the tests on the oldest and the newest OmegaConf.                                                                                                                                                                          |
| P15 | **Composable**             | A resolver accepts the values OmegaConf gives it (`str`, `int`, `float`, `bool`, `None`, `list`, `dict`, `ListConfig`, `DictConfig`) and the output of another `hya` resolver (a `Path` for `hya.path`, a `torch.dtype` for `hya.torch.tensor`).                                                                               |

## Details

- **P2.** The optional resolvers are registered lazily (`ResolverRegistry.register_lazy`): the key
  is always in the registry, and the module is imported when OmegaConf calls the resolver for the
  first time. `import hya` does not look for the packages on disk.
- **P9.** The optional keys are registered whether or not the package is installed, so the registry
  has the same keys on every machine.
- **P10.** With a missing package, the resolver raises a `RuntimeError` that says how to install it
  (`pip install torch`); OmegaConf reports it as an `InterpolationResolutionError`.
- **P8.** After `import hya`, the default resolvers are already published, so
  `registry.register_resolvers()` is silent. Overriding a built-in
  (`registry.register("hya.add", exist_ok=True)`) warns until `register_resolvers(replace=True)` is
  called. OmegaConf caches the resolved nodes of a configuration: `replace=True` does not clear the
  cache of the existing configurations (`OmegaConf.clear_cache(cfg)`).
- **P10.** OmegaConf validation of the annotations (OmegaConf 2.4 and later) is off for the
  resolvers published by `hya`: the annotations are documentation for readers and type checkers, not
  a runtime contract.
- **P11.** The value of an interpolation of a resolver that returns an object cannot always be
  written in YAML: use the value in code, or `OmegaConf.to_container(cfg, resolve=True)`.

## Not guaranteed

- Thread-safety of registering resolvers while OmegaConf resolves interpolations (the registry of
  OmegaConf is a global dictionary).
- Detection of a resolver that another source registers after `hya` published the same key (it needs the private `BaseContainer._resolvers` of OmegaConf, which changes between releases).
- The textual form of `hya.sha256` for an input whose `str()` OmegaConf changes: the hash is of `str(obj)`, so two mappings with the same items in another order have different hashes.
- Caching of the output of the resolvers (OmegaConf default: no cache).
- Support of `OmegaConf.to_yaml(resolve=True)` for resolvers that return objects (P11).
