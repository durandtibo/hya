# Using with Hydra

`hya` is designed to be used with [Hydra](https://github.com/facebookresearch/hydra). Hydra is not
a dependency of `hya`: install it with `pip install hydra-core`.

Add `import hya` to the module of your application. It registers the resolvers before Hydra
resolves the configuration.

> **Python 3.14:** with `hydra-core` 1.3.8, an application decorated with `@hydra.main` stops with
> `ValueError: badly formed help string` before your code runs. The error comes from Hydra, not
> from `hya`. Use Python 3.11 to 3.13 with this Hydra release.

## Basic Example

**config.yaml:**

```yaml
dataset:
  name: mnist
  train_samples: 60000
  val_samples: 10000
  total_samples: ${hya.add:${dataset.train_samples},${dataset.val_samples}}

model:
  type: cnn
  channels: [32, 64, 128]
  num_layers: ${hya.len:${model.channels}}

training:
  batch_size: 64
  epochs: 10
  steps_per_epoch: ${hya.ceildiv:${dataset.train_samples},${training.batch_size}}

paths:
  root: /data
  train: ${hya.iter_join:[${paths.root},${dataset.name},train],/}
  val: ${hya.iter_join:[${paths.root},${dataset.name},val],/}

experiment:
  name: ${dataset.name}_${model.type}
  version: ${hya.sha256:${experiment.name}}
```

**train.py:**

```python
import hya
import hydra
from omegaconf import DictConfig


@hydra.main(version_base=None, config_path=".", config_name="config")
def train(cfg: DictConfig):
    print(f"Dataset: {cfg.dataset.name}")
    print(f"Total samples: {cfg.dataset.total_samples}")
    print(f"Model layers: {cfg.model.num_layers}")
    print(f"Steps per epoch: {cfg.training.steps_per_epoch}")
    print(f"Train path: {cfg.paths.train}")
    print(f"Experiment version: {cfg.experiment.version}")


if __name__ == "__main__":
    train()
```

## Multiple Configuration Files

You can use `hya` resolvers across multiple configuration files. The files of the groups are in
the `model/` and `optimizer/` directories, next to `config.yaml`, and each one is composed under the
name of its directory, so a reference starts with that name (`${model.depth}`):

**config.yaml:**

```yaml
defaults:
  - model: resnet
  - optimizer: adam
  - _self_

experiment:
  name: ${model.name}_${optimizer.name}
  seed: 42
  version: ${hya.sha256:${experiment.name}_${experiment.seed}}
```

**model/resnet.yaml:**

```yaml
name: resnet
depth: 50
width_multiplier: 1.0
effective_depth: ${hya.mul:${model.depth},${model.width_multiplier}}
```

**optimizer/adam.yaml:**

```yaml
name: adam
lr: ${hya.pow:10,-4} # 0.0001
betas: [0.9, 0.999]
```

## Command Line Overrides

The values that a resolver reads can be overridden, and the computed values follow. With the
configuration of the previous section:

```shell
python train.py model.depth=101
```

An override can call a resolver. Quote it, so the shell does not read `$` and the braces:

```shell
python train.py 'experiment.seed=${hya.add:40,3}'
```

A [multi-run](https://hydra.cc/docs/tutorials/basic/running_your_app/multi-run/) resolves the
resolvers in each job:

```shell
python train.py -m model.depth=18,34
```

## Output Directory

The configuration of Hydra can use the resolvers too, for example to name the output directory
after a hash. Add to `config.yaml`:

```yaml
hydra:
  run:
    dir: outputs/${hya.sha256:${experiment.name}}
```

## Resolving the Whole Configuration

Hydra gives your function a configuration with unresolved interpolations. To fail early, for
example before a long training, resolve a copy at the start of the application:

```python
from omegaconf import DictConfig, OmegaConf


def check_config(cfg: DictConfig) -> None:
    # Raises if an interpolation cannot be resolved or if a value is missing (???)
    OmegaConf.to_container(cfg, resolve=True, throw_on_missing=True)
```
