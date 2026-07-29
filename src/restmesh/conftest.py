# SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)
#
# SPDX-License-Identifier: GPL-3.0-or-later

from unittest.mock import MagicMock, patch

import meshtastic.protobuf.mesh_pb2
import pytest
from fastapi.testclient import TestClient

from .main import app

# Block the physical serial device connection globally for all tests.
mock_serial_patch = patch('meshtastic.serial_interface.SerialInterface')
mock_serial_class = mock_serial_patch.start()


# Teardown when pytest finishes.
def pytest_sessionfinish(session, exitstatus):
    mock_serial_patch.stop()


@pytest.fixture
def mock_radio_ok(request):
    """Reset the radio mock parameters to a pristine state before each test.

    By default, it acts as a healthy connected radio.
    """
    radio_mock = MagicMock()

    # Configure default valid packet responses.
    fake_packet = meshtastic.protobuf.mesh_pb2.MeshPacket()
    fake_packet.id = 12345
    fake_packet.to = getattr(request, 'param', 0xffffffff)

    # Reset standard behaviors.
    radio_mock.sendText.return_value = fake_packet
    radio_mock.sendText.side_effect = None
    mock_serial_class.return_value = radio_mock

    return radio_mock


@pytest.fixture
def client_radio_ok(mock_radio_ok):
    """Inject the active mock_radio object into the FastAPI app state."""
    app.state.radio = mock_radio_ok
    with TestClient(app) as test_client:
        yield test_client
    app.state.radio = None


@pytest.fixture
def client_radio_disconnected():
    """Radio is disconnected."""
    mock_serial_class.return_value = None
    app.state.radio = None
    with TestClient(app) as test_client:
        yield test_client
