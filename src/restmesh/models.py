# SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)
#
# SPDX-License-Identifier: GPL-3.0-or-later

import re2 as re
from pydantic import BaseModel, Field, field_validator


class RegexSubst(BaseModel):
    pattern: str = Field(description='A regex pattern to be matched against',
                         default='')
    subst: str = Field(description='What to replace the regex pattern with',
                       default='')

    @field_validator('pattern')
    @classmethod
    def validate_regex(cls, v: str) -> str:
        try:
            re.compile(v)
        except re.error:
            raise ValueError('Invalid regex syntax')
        return v
