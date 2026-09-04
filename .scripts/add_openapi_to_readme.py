# SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)
#
# SPDX-License-Identifier: GPL-3.0-or-later

import os
import pathlib
import re


def main():
    readme_path = pathlib.Path('API.md')
    docs_path = pathlib.Path('openapi.md')
    openapi_path = pathlib.Path('openapi.json')

    if readme_path.is_file() and docs_path.is_file():
        content = readme_path.read_text(encoding='utf-8')
        generated_docs = docs_path.read_text(encoding='utf-8')

        pattern = r'(<!-- START_API_DOCS -->)(.*?)(<!-- END_API_DOCS -->)'

        new_content = re.sub(
            pattern,
            lambda m: ''.join([
                m.group(1), os.linesep, generated_docs, os.linesep,
                m.group(3)
            ]),
            content,
            flags=re.DOTALL)
        readme_path.write_text(new_content, encoding='utf-8')
        docs_path.unlink(missing_ok=True)
    else:
        raise FileNotFoundError

    openapi_path.unlink(missing_ok=True)


if __name__ == '__main__':
    main()
