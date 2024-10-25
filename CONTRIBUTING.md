# Contributing to street-view-green-view

_...Work in progress..._

## Development

### Code style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and automatic code formatting.

You can run linting with the following shell commands or use the `make lint` shortcut:

```bash
ruff format --check src
ruff check src
```

To format, run the following shell commands or `make format`:

```bash
ruff format src
ruff check src --fix
```

### Commits

Please follow the [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/) specification when creating your commit messages.

## For maintainers

### Checkout a PR branch from a fork

To check out a pull request branch from a fork, first install the [GitHub CLI](https://cli.github.com/).

Then, from the repository, you can run, for example:

```bash
gh pr checkout 2
```

where the final number should be the PR number.

If you don't want to use the GitHub CLI, this can also be done using just regular git. See [this StackOverflow answer](https://stackoverflow.com/a/71787682).
