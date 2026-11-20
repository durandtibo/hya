# Contributing

Thanks for your interest in contributing to `shared-makefiles`!

## Getting started

1. Fork the repo and clone your fork.
2. Create a branch for your change.
3. Run `make install-tools` to install the formatting/linting tools used by this repo
   (`prettier`, `yamllint`, `mbake`, `checkmake`, `shellcheck`, `shfmt`, `markdownlint`,
   `actionlint`).

## Making changes

- Each `.mk` file is self-contained and include-guarded — keep that property when editing or
  adding one (see [`README.md`](README.md#design) for the design conventions: include guards,
  on-demand tool install, configurable path variables).
- Add a `## description` comment to any new `.PHONY` target so it shows up in `make help`.
- If you add or change a variable, document it in the relevant table in `README.md`.
- Run `make format` and `make lint` before committing.

## Testing

CI ([`.github/workflows/ci.yaml`](.github/workflows/ci.yaml)) runs `make lint` and
`make format` (including on-demand tool installation) across an Ubuntu/macOS matrix. Make sure
both pass locally first:

```shell
make lint
make format
```

## Submitting a pull request

- Fill in the [PR template](.github/PULL_REQUEST_TEMPLATE.md) checklist.
- Keep PRs focused — one logical change per PR.
- Make sure CI is green before requesting a review.

## Reporting bugs and requesting features

Use the issue templates under
[`.github/ISSUE_TEMPLATE`](.github/ISSUE_TEMPLATE): `bug-report.yml` or `feature-request.yml`.

## Security issues

Please don't open a public issue for security vulnerabilities — see [`SECURITY.md`](SECURITY.md)
for how to report them privately.
