r"""Define the tasks that are executed with invoke."""

from __future__ import annotations

import sys

from invoke import Context, Task
from invoke_tasklib import make_ns
from invoke_tasklib.config import load_config
from invoke_tasklib.output import step
from invoke_tasklib.runner import run

__all__ = ["ns"]

ns = make_ns()


def verify(c: Context) -> None:
    r"""Verify that the public API of the package is fully typed."""
    package = load_config(c).package.import_name
    with step(c, "🔬 Verifying the public types with pyright...", "✅ Type verification passed"):
        # pyright finds the installed package only with an activated environment
        run(
            c,
            ["pyright", "--verifytypes", package, "--ignoreexternal"],
            env={"VIRTUAL_ENV": sys.prefix},
        )


ns.collections["types"].add_task(Task(verify, name="verify"))
