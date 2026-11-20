# Properties

These are the rules `hya` guarantees. Each one is enforced by the code or by a test of the
repository.

| #   | Property                   | Statement                                                                                                                                                                                                      |
| --- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| P1  | **Import is enough**       | `import hya` registers every available default resolver with OmegaConf. No other call is needed.                                                                                                               |
| P2  | **Cheap import**           | `import hya` imports neither `numpy`, `torch` nor `braceexpand`, and emits no warning. The module of an optional resolver is imported on the first call of that resolver.                                      |
| P3  | **Namespaced**             | Every built-in key starts with `hya.`. Optional ones are grouped (`hya.np.*`, `hya.torch.*`). Nothing is registered outside this namespace.                                                                    |
| P4  | **Thin resolvers**         | A resolver is a standard library callable or a function of a few lines with one documented behaviour. No hidden state, no I/O beyond what its name says (`hya.path` touches the file system).                  |
| P5  | **Pure**                   | A resolver never modifies its arguments. Interpolating a config node into a resolver cannot change the config.                                                                                                 |
| P6  | **Deterministic output**   | The same arguments give the same output, including inside error messages (sorted, no set order).                                                                                                               |
| P7  | **Explicit registry**      | A `ResolverRegistry` is a plain key to callable map. `register` adds, `register_resolvers` publishes to OmegaConf. Registries are independent of each other.                                                   |
| P8  | **Replace is explicit**    | `register_resolvers()` is idempotent. It never silently keeps a stale resolver: a key that changed since it was published, or that another source registered, is skipped with a warning unless `replace=True`. |
| P9  | **One default registry**   | `get_default_registry()` returns one process-wide registry holding the built-in resolvers. Users extend it or create their own registry.                                                                       |
| P10 | **Errors are OmegaConf's** | A failing resolver surfaces as `InterpolationResolutionError` with the original error as cause. `hya` adds no wrapper of its own. Calling the function of a missing optional package says how to install it.   |
| P11 | **Any value out**          | A resolver may return any Python object (`Path`, `ndarray`, `Tensor`, `dtype`, list). Such values are for use in code and are not meant for `OmegaConf.to_yaml`.                                               |
| P12 | **Typed and documented**   | The package has a `py.typed` file, every public name is documented with a doctest, and every resolver is listed in the [resolvers](resolvers.md) page.                                                         |
| P13 | **Keyword-only options**   | Options are keyword-only (`exist_ok`, `replace`). Positional arguments are the data.                                                                                                                           |
| P14 | **Installs next to Hydra** | `hya` accepts every OmegaConf release that a Hydra release accepts (`omegaconf>=2.2,<3.0`). CI runs the tests on the oldest and the newest OmegaConf.                                                          |

## Details

- **P2.** The optional resolvers are registered lazily (`ResolverRegistry.register_lazy`): the key
  is in the registry only if the package is installed, and the module is imported when OmegaConf
  calls the resolver for the first time. With a missing package the key is not registered, so
  OmegaConf raises `UnsupportedInterpolationType`.
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
- Caching of the output of the resolvers (OmegaConf default: no cache).
- Support of `OmegaConf.to_yaml(resolve=True)` for resolvers that return objects (P11).
