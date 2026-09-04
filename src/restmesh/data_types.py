# SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)
#
# SPDX-License-Identifier: GPL-3.0-or-later
"""Bastic data types."""

import logging
from contextvars import ContextVar
from typing import Annotated, Literal

from fastapi import Path
from pydantic import BeforeValidator, Field, TypeAdapter, ValidationError

from . import models

# Thread safe variable.
truncated_message: ContextVar[bool] = ContextVar('truncated_message',
                                                 default=False)

# See:
# https://github.com/meshtastic/protobufs/blob/master/meshtastic/mesh.proto
NodeNum = Annotated[int,
                    Field(strict=True,
                          ge=0,
                          le=(2**32) - 1,
                          description='The 32-bit integer node number')]

# Should be an 8 char HEX integer.
NodeId = Annotated[
    str,
    Field(strict=True,
          pattern=r'^![0-9a-f]{8}$',
          description=
          "The 8-character lowercase hex string node ID starting with '!'")]

node_id_adapter = TypeAdapter(NodeId)
node_num_adapter = TypeAdapter(NodeNum)


def parse_and_validate_node(v: any) -> str | int:
    r"""Validate and transform the incoming route string using strict NodeId or NodeNum rules."""
    v_str = str(v).strip()

    # Parse as NodeId if it starts with the '!' character.
    if v_str.startswith('!'):
        try:
            return node_id_adapter.validate_python(v_str)
        except ValidationError:
            raise ValueError(
                f'Invalid NodeId format: \'{v_str}\'. Must be an 8-character lowercase hex string starting with \'!\'.'
            )

    # Parse as NodeNum if it consists only of digits.
    if v_str.isdigit():
        try:
            return node_num_adapter.validate_python(int(v_str))
        except ValidationError:
            raise ValueError(
                f'Invalid NodeNum value: \'{v_str}\'. Must be a 32-bit integer between 0 and {(2 * 32) - 1}.'
            )

    # Fallback error if the input format matches neither type pattern.
    raise ValueError(
        f'Invalid node target structure: \'{v_str}\'. Provide a hex NodeId or a numeric NodeNum.'
    )


NodeTarget = Annotated[
    str | int,
    BeforeValidator(parse_and_validate_node),
    Path(
        description=
        'Target destination: can be a lowercase hex string NodeId (e.g. !2c3b4f5a) or a numeric NodeNum < 2^32 (e.g. 60).'
    ),
    Field(
        description=
        'Target destination: can be a lowercase hex string NodeId (e.g. !2c3b4f5a) or a numeric NodeNum < 2^32 (e.g. 60).',
        json_schema_extra={
            'examples': [{
                'summary': 'Hexadecimal NodeId',
                'description':
                "The 8-character lowercase hex string node ID starting with '!'",
                'value': '!2c3b4f5a'
            }, {
                'summary': 'Decimal NodeNum',
                'description': 'The 32-bit integer node number',
                'value': 123456789
            }]
        })]

# Channels are from 0 to 7.
# See:
# https://python.meshtastic.org/node.html
ChannelIndex = Annotated[
    int,
    Path(description='The channel index (0 to 7)'),
    Field(ge=0, le=7, description='The channel index (0 to 7)')]

# See
# https://github.com/meshtastic/protobufs/blob/master/meshtastic/portnums.proto
PortNum = Annotated[int,
                    Field(strict=True,
                          ge=0,
                          le=511,
                          description='Protobuf application port number')]


# Before validators.
def truncate_to_meshtastic_mtu(v: str) -> str:
    """Truncate the string to 200 bytes (237 bytes is the theoretical limit)."""
    # Safe limit.
    MAX_BYTES: int = 200
    SUFFIX: str = '<|TRUNC|>'
    suffix_len = len(SUFFIX.encode('utf-8'))

    if len(v.encode('utf-8')) <= MAX_BYTES:
        # v is not truncated.
        return v

    # v is truncated from now on.
    allowed_bytes: int = MAX_BYTES - suffix_len

    # Avoid truncating at a multi-byte character.
    encoded = v.encode('utf-8')[:allowed_bytes]
    truncated_str: str = encoded.decode('utf-8', errors='ignore')
    logging.info(len(f'{truncated_str}{SUFFIX}'))

    truncated_message.set(True)

    return f'{truncated_str}{SUFFIX}'


TextMessagePayload = Annotated[
    str,
    Field(
        strict=True,
        description=
        'UTF-8 text to the mesh. This API limits it to 200 bytes for safety, although [the default Meshtastic MTU is 237 bytes](https://buf.build/meshtastic/protobufs/docs/86640f20db7b9b5be42949d18e8d96ad10d47a68%3Ameshtastic#meshtastic.Constants)'
    )]

WantAck = Annotated[
    bool,
    Field(
        strict=True,
        default=False,
        description=
        "`true` if you want the message sent in a reliable manner (with retries and ack/nak provided for delivery). Meshtastic's firmware will handle the retries. will [See this also](https://python.meshtastic.org/mesh_interface.html#meshtastic.mesh_interface.MeshInterface.sendText)"
    )]

WantResponse = Annotated[
    bool,
    Field(
        strict=True,
        default=True,
        description=
        '`true` if you want the service on the other side to send an application layer response. [See this also](https://python.meshtastic.org/mesh_interface.html#meshtastic.mesh_interface.MeshInterface.sendText)'
    )]

# See
# https://github.com/caronc/apprise/blob/4162f39efba5481bad2b61c2e85e05061542f470/apprise/plugins/custom_json.py#L89
AppriseJsonSchemaVersion = Annotated[
    str, Field(description='Apprise JSON schema version')]

AppriseNotificationType = Annotated[
    Literal['info', 'warning', 'success', 'failure'] | None,
    Field(default='info', description='Unused parameter')]

AppriseNotificationTitle = Annotated[
    str | None, Field(default='', description='Unused parameter')]

MeshActionResponseStatus = Annotated[
    Literal['success'],
    Field(description='Always return "success"')]

MeshActionResponseRoutingMode = Annotated[
    Literal['broadcast', 'direct'],
    Field(description='Message routing type')]

MeshActionResponseTruncated = Annotated[
    bool,
    Field(
        strict=True,
        default=False,
        description='Message was truncated to Meshtastic MTU before being sent'
    )]

RegexSubst = Annotated[
    models.RegexSubst,
    Field(
        description=
        'Clean the text input using a regex pattern via the safer [google-re2 Python module](https://pypi.org/project/google-re2/) to avoid [catastrophic backtracking](https://www.regular-expressions.info/catastrophic.html). The standard `re` Python module is vulnerable to DoS'
    )]
