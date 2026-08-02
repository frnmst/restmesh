<!--
SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)

SPDX-License-Identifier: GPL-3.0-or-later
-->

# Contributing

<!--TOC-->

- [Contributing](#contributing)
  - [Method](#method)
    - [Unit tests](#unit-tests)
  - [AI Policy](#ai-policy)

<!--TOC-->

If you want to contribute, please follow these simple policies.

## Method

1. add a new endpoint or fix
2. add unit tests by mocking the radio
  - valid cases
  - edge cases
  - invalid cases
3. run the [unit tests](#unit-tests)
3. create a pull request on the `dev` branch

### Unit tests

1. install the Python versions listed in the
   [pyproject.toml](pyproject.toml) `tool.tox.env_list` entry: use
   [ASDF](https://asdf-vm.com/guide/getting-started.html)
2. install the development environment as shown in the python-makefile[^1]
   repository (see footnotes)
3. run the tests with TOX:

   ```shell
   make tox
   ```

4. all tests must pass

## AI Policy

restmesh is human-authored, AI-assisted code: LLM use is not blanket-banned,
but all its outputs must be thoroughly checked. LLMs can be used for
brainstorming, and specific domain problem solving, but its outputs must always
be challenged to provide better quality code and compared with the official
documentation and best practices. In this project an LLM should be used as a
more powerful search engine: that's it.

Remember that LLMs have varying degrees of sycophancy so prompts must be
adapted to mitigate that.

No kind of automated AI agent can be involved, and all commits must be signed
by real humans.

All the LLMs used by the authors must be lighter, accountless, free-to-use,
cloud models, even better if free (libre) and self-hosted.

If these indications are not followed, your contribution cannot be merged in
the codebase.

[^1]: [Codeberg](https://codeberg.org/frnmst/python-makefile),
      [Framagit](https://framagit.org/frnmst/python-makefile),
      [Self-hosted Forgejo](https://repos.franco.net.eu.org/frnmst/python-makefile)
