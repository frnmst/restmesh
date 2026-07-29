# SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)
#
# SPDX-License-Identifier: GPL-3.0-or-later

import json
from pathlib import Path

from restmesh.main import app


def main():
    openapi_file = Path('openapi.json')
    with open(openapi_file, 'w', encoding='utf-8') as f:
        json.dump(app.openapi(), f, indent=2)


if __name__ == '__main__':
    main()
