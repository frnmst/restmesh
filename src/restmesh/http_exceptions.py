# SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)
#
# SPDX-License-Identifier: GPL-3.0-or-later

from fastapi import HTTPException, status

RADIO_UNAVAILABLE_503 = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail='Meshtastic radio interface is not initialized or unavailable.')

RADIO_PROTOCOL_ERROR_503 = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail='Radio hardware protocol error.')

QUEUE_FULL_429 = HTTPException(
    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
    detail='Unable to handle more requests, queue full.')

RADIO_USB_OR_SERIAL_FAILURE_503 = HTTPException(
    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
    detail=
    'Local serial device communication failed. Check USB physical connection.')
