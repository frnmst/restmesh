<!--
SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)

SPDX-License-Identifier: GPL-3.0-or-later
-->

# Contributing

<!--TOC-->

- [Contributing](#contributing)
  - [Method](#method)
  - [AI Policy](#ai-policy)

<!--TOC-->

If you want to contribute, please follow these simple policies.

## Method

1. add a new endpoint or fix
2. add unit tests by mocking the radio
  - valid cases
  - edge cases
  - invalid cases
3. create a pull request on the `dev` branch

## AI Policy

restmesh is human-authored, AI-assisted code: I don't reject the use of LLMs,
but all its outputs are thoroughly checked. LLMs can be used for
brainstorming, and specific domain problem solving, but its outputs must always
be challenged to provide better quality code and compared with the official
documentation and best practices. An LLM should be used as a more powerful
search engine: that's it.

Remember that LLMs have varying degrees of sycophancy so prompts must be
adapted to mitigate that.

No kind of AI agents can be involved and all commits must be signed by humans.

All the LLMs used by the autor are lighter, accountless, free-to-use,
cloud models. If the author could self-host a better local AI model that
actually works on cheaper hardware he would do that instead.

The author feels this is the best compromise right now until things get
clearer.
