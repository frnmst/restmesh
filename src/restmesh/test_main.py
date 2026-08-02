# SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)
#
# SPDX-License-Identifier: GPL-3.0-or-later

import pytest
from fastapi import status

from .meshtastic import MeshInterface


###########
# Channel #
###########
def test_create_channel_text_message_ok_radio(client_radio_ok, mock_radio_ok):
    response = client_radio_ok.post(
        '/api/v1/channels/0/messages',
        json={
            'text': 'Foo',
            'wantAck': False,
            'portNum': 1
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        'status': 'success',
        'routing_mode': 'broadcast',
        'packet': {
            'id': 0,
            'from': 0,
            'to': 0,
            'channel': 0,
            'portnum': 1,
            'text': 'Foo',
            'wantAck': False,
            'wantResponse': False
        },
        'onResponse_callback_payload': None,
        'truncated': False
    }


@pytest.mark.parametrize('mock_radio_ok', [0x0], indirect=True)
@pytest.mark.parametrize('valid_node_target', [
    '!00000000',
    '0',
])
def test_create_node_text_message_ok_radio(client_radio_ok, mock_radio_ok,
                                           valid_node_target):
    response = client_radio_ok.post(
        f'/api/v1/nodes/{valid_node_target}/messages',
        json={
            'text': 'Foo',
            'wantAck': False,
            'portNum': 1
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        'status': 'success',
        'routing_mode': 'direct',
        'packet': {
            'id': 0,
            'from': 0,
            'to': 0,
            'channel': 0,
            'portnum': 1,
            'text': 'Foo',
            'wantAck': False,
            'wantResponse': True
        },
        'onResponse_callback_payload': None,
        'truncated': False
    }


@pytest.mark.parametrize('mock_radio_ok', [0x0], indirect=True)
@pytest.mark.parametrize(
    'invalid_node_target',
    [
        # Valid hex string too short.
        '!0123456',

        # Valid hex string too long.
        '!012345678',

        # Invalid hex.
        '!abcdeffg',
        '-a',

        # Out of bounds nodenum.
        f'{-1}',
        f'{2**32}'
    ])
def test_create_node_text_message_invalid_node_target_ok_radio(
        client_radio_ok, mock_radio_ok, invalid_node_target):
    response = client_radio_ok.post(
        f'/api/v1/nodes/{invalid_node_target}/messages',
        json={
            'text': 'Foo',
            'wantAck': False,
            'portNum': 1
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize('mock_radio_ok', [0x0123456], indirect=True)
def test_create_channel_text_message_minimal_ok_radio(client_radio_ok,
                                                      mock_radio_ok):
    response = client_radio_ok.post(
        '/api/v1/channels/0/messages',
        json={
            'text': 'Foo',
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        'status': 'success',
        'routing_mode': 'broadcast',
        'packet': {
            'id': 0,
            'from': 0,
            'to': 0,
            'channel': 0,
            'portnum': 1,
            'text': 'Foo',
            'wantAck': False,
            'wantResponse': False
        },
        'onResponse_callback_payload': None,
        'truncated': False
    }


@pytest.mark.parametrize('mock_radio_ok', [0x0123456], indirect=True)
def test_create_channel_text_message_minimal_garbage_ok_radio(
        client_radio_ok, mock_radio_ok):
    response = client_radio_ok.post(
        '/api/v1/channels/0/messages',
        json={
            'tExt': 'Foo',
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_channel_text_message_truncated_ok_radio(
        client_radio_ok, mock_radio_ok):
    response = client_radio_ok.post(
        '/api/v1/channels/0/messages',
        json={
            'text': '0' * 201,
            'wantAck': False,
            'portNum': 1
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        'status': 'success',
        'routing_mode': 'broadcast',
        'packet': {
            'id': 0,
            'from': 0,
            'to': 0,
            'channel': 0,
            'portnum': 1,
            'text': f'{"0"*191}<|TRUNC|>',
            'wantAck': False,
            'wantResponse': False
        },
        'onResponse_callback_payload': None,
        'truncated': True
    }


def test_create_channel_text_message_maximum_mtu_ok_radio(
        client_radio_ok, mock_radio_ok):
    response = client_radio_ok.post(
        '/api/v1/channels/0/messages',
        json={
            'text': '0' * 200,
            'wantAck': False,
            'portNum': 1
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        'status': 'success',
        'routing_mode': 'broadcast',
        'packet': {
            'id': 0,
            'from': 0,
            'to': 0,
            'channel': 0,
            'portnum': 1,
            'text': f'{"0"*200}',
            'wantAck': False,
            'wantResponse': False
        },
        'onResponse_callback_payload': None,
        'truncated': False
    }


def test_create_channel_text_message_wrong_channel_lt_0_ok_radio(
        client_radio_ok, mock_radio_ok):
    response = client_radio_ok.post(
        '/api/v1/channels/-1/messages',
        json={
            'text': 'Foo',
            'wantAck': False,
            'portNum': 1
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    'invalid_portnum',
    [
        # Out of bounds.
        -1,
        512,
    ])
def test_create_channel_text_message_invalid_porntnum_ok_radio(
        client_radio_ok, mock_radio_ok, invalid_portnum):
    response = client_radio_ok.post(
        '/api/v1/channels/0/messages',
        json={
            'text': 'Foo',
            'portNum': invalid_portnum
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_channel_text_message_wrong_channel_gt_7_ok_radio(
        client_radio_ok, mock_radio_ok):
    response = client_radio_ok.post(
        '/api/v1/channels/8/messages',
        json={
            'text': 'Foo',
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_channel_text_message_wrong_channel_non_int_ok_radio(
        client_radio_ok, mock_radio_ok):
    response = client_radio_ok.post(
        '/api/v1/channels/foo/messages',
        json={
            'text': 'Foo',
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


def test_create_channel_message_disconnected_radio(client_radio_disconnected):
    response = client_radio_disconnected.post(
        '/api/v1/channels/0/messages',
        json={
            'text': 'Foo',
        },
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {
        'detail':
        'Meshtastic radio interface is not initialized or unavailable.'
    }


def test_create_channel_message_protocol_error(client_radio_ok, mock_radio_ok):
    mock_radio_ok.sendText.side_effect = MeshInterface.MeshInterfaceError(
        'Meshtastic error')
    response = client_radio_ok.post(
        '/api/v1/channels/0/messages',
        json={
            'text': 'Foo',
        },
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {'detail': 'Radio hardware protocol error.'}


def test_create_channel_message_generic_error(client_radio_ok, mock_radio_ok):
    mock_radio_ok.sendText.side_effect = Exception('Meshtastic error')
    response = client_radio_ok.post(
        '/api/v1/channels/0/messages',
        json={
            'text': 'Foo',
        },
    )
    assert response.status_code == status.HTTP_503_SERVICE_UNAVAILABLE
    assert response.json() == {
        'detail':
        'Local serial device communication failed. Check USB physical connection.'
    }
