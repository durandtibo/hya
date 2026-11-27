# Design Choices

This page explains how `hya` is designed and why. Each choice has a cost, so each section states
the trade-off and what to do when the choice does not fit your project. The rules that follow from
these choices are listed in [Properties](properties.md).

## Resolvers are standard library callables when possible

`hya.sub`, `hya.sqrt`, `hya.max`, `hya.len`, `hya.int`, ... are registered as the callable itself
(`operator.sub`, `math.sqrt`, `max`, `len`, `int`), with no wrapper.

- **Benefit:** the behaviour, the accepted arguments and the error messages are the ones of the
  standard library, which you already know and which are documented. There is no `hya` code to read
  or to trust.
- **Cost:** `hya` cannot smooth the rough edges of a callable. `hya.max` takes the arguments of
  `max` (`${hya.max:10,25,15}`), and `hya.log` raises the `ValueError` of `math.log` for a value
  outside its domain.
- **If it does not fit:** register your own resolver (see
  [Custom Resolvers](user_guide.md#custom-resolvers)).

A resolver is a function of a few lines only when no standard library callable has the behaviour
(`hya.add`, `hya.mul`, `hya.ceildiv`, `hya.path`, `hya.iter_join`, `hya.sha256`, `hya.pi`).

## The set of resolvers is small

`hya` has one resolver for one operation that a configuration needs, not a copy of the standard
library. For example, there is no `hya.abs`, `hya.round` or `hya.mod`, and there is no `bool` or
`str` cast (`bool("false")` is `True`, and an interpolation already produces a string).

- **Benefit:** the whole library fits in one page and each key has one meaning.
- **Cost:** an operation that is missing needs a custom resolver (two lines, see
  [Custom Resolvers](user_guide.md#custom-resolvers)).

## Optional resolvers are always registered, and imported lazily

`hya.braceexpand`, `hya.np.array`, `hya.torch.tensor` and `hya.torch.dtype` are in the registry on
every machine. Their module, and so `numpy`, `torch` or `braceexpand`, is imported when OmegaConf
calls the resolver for the first time (`ResolverRegistry.register_lazy`).

- **Benefit:** `import hya` is fast and does not import `numpy`, `torch` or `braceexpand`. The
  registry has the same keys everywhere, so a configuration that is valid on one machine fails with
  the same error on another machine that lacks the package.
- **Cost:** a missing package is detected when the resolver is called, not when `hya` is imported
  or when the configuration is loaded.
- **If it does not fit:** call the resolver once at start up, or check the package with
  `hya.imports` before you load the configuration.

A lazy resolver cannot receive the special parameters of OmegaConf (`_root_`, `_parent_`,
`_node_`): OmegaConf reads them from the signature of the function, which is not known before the
import. Register such a resolver with `register`.

A missing package raises a `RuntimeError` that says how to install it
(`'torch' package is required but not installed. ... pip install torch`).

## Every key lives in the `hya.` namespace

Built-in keys start with `hya.`, and optional ones are grouped by package (`hya.np.*`,
`hya.torch.*`).

- **Benefit:** `hya` never collides with the resolvers of OmegaConf (`oc.*`), of Hydra
  (`hydra`) or of your project.
- **Cost:** the keys are longer than `add` or `mul`.
- **If it does not fit:** register an alias in your own registry, for example `my.add`.

## Importing `hya` registers the resolvers

`import hya` publishes the default resolvers to OmegaConf. No other call is needed.

- **Benefit:** the common case is one line, in a script or in a Hydra application.
- **Cost:** importing a package has a side effect on a global (the resolver table of OmegaConf).
  The import must happen before the configuration is resolved, so a module that only loads a YAML
  file still needs `import hya`.
- **If it does not fit:** build a `ResolverRegistry` of your own and call `register_resolvers()` when
  you decide to. Importing `hya` still publishes the default resolvers.

Hydra has a plugin mechanism that could remove the import. `hya` does not use it: it needs a
`hydra_plugins` namespace package and a dependency on Hydra internals for the gain of one line.

## The registry rejects what cannot work

Every entry of a `ResolverRegistry` is added by `register`, including the ones of the constructor
and of `register_lazy`. It raises at once for a value that is not callable, a key that is not a
string (`@registry.register` used without a key) and a key that is not made of names joined by dots.

- **Benefit:** the error points at the line that registers, not at a configuration that fails to
  parse later, and `register_resolvers()` cannot stop half way because of an entry.
- **Cost:** a key such as `my-key`, which OmegaConf 2.3 and later can interpolate, is rejected,
  because OmegaConf 2.2 cannot interpolate it and `hya` behaves the same on all of them.
- **If it does not fit:** register such a resolver with `OmegaConf` directly.

## The registry is explicit about replacing

A `ResolverRegistry` is a map from a key to a callable, with two separate steps: `register` adds a
callable to the registry, and `register_resolvers` publishes the registry to OmegaConf. Both refuse
to replace silently:

- `register(key)` raises a `RuntimeError` if the key exists, unless `exist_ok=True`.
- `register_resolvers()` skips, with a warning, a key that OmegaConf already has, unless
  `replace=True`.

- **Benefit:** a typo or an import-order accident cannot swap a resolver without a trace, and
  `register_resolvers()` can be called as often as you like (it is idempotent).
- **Cost:** overriding a built-in takes two opt-ins (`exist_ok=True`, then `replace=True`).
- **Limit:** `hya` cannot detect that another source registered a key in OmegaConf _after_ `hya`
  published it. Doing so needs private OmegaConf attributes that change between releases.

## Errors are the ones of OmegaConf

A resolver raises standard exceptions only, and OmegaConf reports a failure as an
`InterpolationResolutionError`. `hya` does not wrap the error in an exception of its own, and no
resolver raises an OmegaConf error of its own accord: a direct Python call of
`torch_dtype_resolver` raises a plain `ValueError`.

- **Benefit:** there is no extra layer between you and the real error. The message names the
  original exception, which is in the `__context__` chain of the error (`__cause__` is `None`).
- **Cost:** you cannot catch "any `hya` error" with one `except` clause; you catch the OmegaConf
  error and inspect its context.

## Resolvers are pure and can return any object

A resolver never modifies its arguments: `${hya.add:${x},[3]}` returns a new list and leaves `x`
unchanged. It does not copy what it returns: `${hya.add:${x}}` is the node `x` itself, as `${x}`
is, so copy such a value before you mutate it. A resolver may return any Python object (`Path`,
`ndarray`, `Tensor`, `dtype`, list).

- **Benefit:** a configuration can carry the objects your code needs, with no conversion step.
- **Cost:** an array, a tensor or a data type is not a value of a configuration. Use it in code, or
  with `OmegaConf.to_container(cfg, resolve=True)`. `OmegaConf.resolve` needs the `allow_objects`
  flag for it, and `OmegaConf.to_yaml` with `resolve=True` does not support it.

## Arguments are positional

The arguments of a resolver are positional, because the interpolation grammar has no keyword
syntax. An optional argument comes last and has a default (`${hya.np.array:[1,2],float32}`). The
options of the Python API (`exist_ok`, `replace`) are keyword-only.

- **Benefit:** the YAML and the Python API each use the form that is natural to them, and an option
  cannot be swapped with another by position.
- **Cost:** a resolver with many options would be hard to read; `hya` keeps resolvers to a few
  arguments.

## Annotations are documentation, not validation

With OmegaConf 2.4 and later, `hya` publishes resolvers with `annotation_validation="off"`. The
type annotations describe the resolver for readers and type checkers; OmegaConf does not check them
at call time.

- **Benefit:** the same resolver behaves the same on every supported OmegaConf release (2.2 to
  2.4), and a resolver that accepts several types is not rejected by an annotation.
- **Cost:** a wrong type fails inside the resolver (for example a `TypeError`) instead of in a
  validation step.

## The hash reads the whole value

`hya.sha256` is meant for identifiers, so two different values must not share a hash by accident.
It resolves the configuration nodes of its argument (`hya.utils.config.to_plain`, which
`hya.iter_join`, `hya.np.array` and `hya.torch.tensor` use too), then hashes a string as is and any
other value as canonical JSON (sorted keys, no space).

- **Benefit:** the hash follows the interpolated values, does not depend on the order of the keys,
  on `repr`, on the print options of NumPy or PyTorch, or on the OmegaConf release, and the hash of
  a string is the one that other SHA-256 tools give.
- **Cost:** the type of a value is not part of the hash (the string `[1]` and the list `[1]` have the
  same hash), a value without a JSON form raises instead of being hashed, and resolving a large list
  at each access takes time.
- **If it does not fit:** hash the value in your code, or register your own resolver.

An array or a tensor is not hashed from its bytes: it would need a format for the data type and the
shape, and two optional packages in a resolver of the standard library. Hash the value the array is
built from.

## Some behaviours follow Python on purpose

- **`hya.ceildiv` follows `//`.** It computes `-(a // -b)`, which is exact for integers of any size.
  The result is an `int` for two integers and a `float` for a float. Use
  `${hya.int:${hya.ceildiv:x,y}}` to force an `int`.
- **`hya.torch.dtype` accepts names, not `torch.float32`.** There is one spelling for one thing,
  and the error for an unknown name lists the valid names, sorted. `hya.torch.tensor` accepts the
  same names.
- **`hya.np.array` takes the data type as a string.** The string that NumPy accepts is enough, so
  there is no `hya.np.dtype` resolver. `hya.torch.tensor` takes the name too, so the two resolvers
  have the same contract, and also a `torch.dtype`, such as the output of `hya.torch.dtype`.
- **`hya.path` reads `file:` URLs only.** A string that starts with `file:` is decoded as a URL; any
  other string is a plain path, so `/data/a%20b` keeps its `%20`. A file URL with a host other than
  `localhost`, a query or a fragment raises a `ValueError` instead of dropping it: write a `?` or a
  `#` of a file name as `%3F` or `%23`.
- **`hya.braceexpand` returns a list.** It has a length, can be indexed and can be read several
  times, at the cost of building the whole expansion at once.

## Compatibility with Hydra

`hya` accepts every OmegaConf release that Hydra 1.3 accepts (`omegaconf>=2.2,<3.0`), so it can be
installed next to any `hydra-core` 1.3 release. The only code that depends on the OmegaConf version
is the function that publishes a resolver (`register_resolver` in 2.4 and later,
`register_new_resolver` before).
