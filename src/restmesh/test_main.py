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
            'want_ack': False,
            'port_num': 1
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        'status': 'success',
        'routing_mode': 'broadcast',
        'packet': {
            'id': 12345,
            'from': 0,
            'to': 0,
            'channel': 0,
            'port_num': 1,
            'text': 'Foo',
            'want_ack': False,
            'want_response': False
        },
        'on_response_callback_payload': None,
        'truncated': False
    }


# We only test regex subst here since the code is the same in each text_message
# endpoint.
@pytest.mark.parametrize('pattern_result', [
    ['Bar', 'Foo'],
    ['.*Foo.*', 'Bar'],
    ['\\s*Foo.*', 'Bar'],
])
def test_create_channel_text_message_regexsubst_ok_radio(
        client_radio_ok, mock_radio_ok, pattern_result):
    response = client_radio_ok.post(
        '/api/v1/channels/0/messages',
        json={
            'text': 'Foo',
            'want_ack': False,
            'port_num': 1,
            'regex_subst': {
                'pattern': pattern_result[0],
                'subst': 'Bar'
            },
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        'status': 'success',
        'routing_mode': 'broadcast',
        'packet': {
            'id': 12345,
            'from': 0,
            'to': 0,
            'channel': 0,
            'port_num': 1,
            'text': pattern_result[1],
            'want_ack': False,
            'want_response': False
        },
        'on_response_callback_payload': None,
        'truncated': False
    }


def test_create_channel_text_message_regexsubst_fail_ok_radio(
        client_radio_ok, mock_radio_ok):
    r"""Pass an invalid escape sequence in JSON to trigger an error."""
    payload: str = r"""{
        "text": "Foo",
        "want_ack': False,
        "port_num': 1,
        "regex_subst": {
            "pattern": ".*\s*Foo.*",
            "subst": "Bar"
        }
    }"""
    response = client_radio_ok.post(
        '/api/v1/channels/0/messages',
        content=payload,
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


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
            'want_ack': False,
            'port_num': 1
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        'status': 'success',
        'routing_mode': 'direct',
        'packet': {
            'id': 12345,
            'from': 0,
            'to': 0,
            'channel': 0,
            'port_num': 1,
            'text': 'Foo',
            'want_ack': False,
            'want_response': False
        },
        'on_response_callback_payload': None,
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
            'want_ack': False,
            'port_num': 1
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
            'id': 12345,
            'from': 0,
            'to': 0,
            'channel': 0,
            'port_num': 1,
            'text': 'Foo',
            'want_ack': True,
            'want_response': False
        },
        'on_response_callback_payload': None,
        'truncated': False
    }


@pytest.mark.parametrize('mock_radio_ok', [0x0123456], indirect=True)
def test_create_channel_text_message_minimal_garbage_ok_radio(
        client_radio_ok, mock_radio_ok):
    r"""Invalid payload key."""
    response = client_radio_ok.post(
        '/api/v1/channels/0/messages',
        json={
            'tExt': 'Foo',
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize('mock_radio_ok', [0x0], indirect=True)
@pytest.mark.parametrize('valid_node_target', [
    '!00000000',
    '0',
])
def test_create_node_text_message_minimal_garbage_ok_radio(
        client_radio_ok, mock_radio_ok, valid_node_target):
    r"""Invalid payload key."""
    response = client_radio_ok.post(
        f'/api/v1/nodes/{valid_node_target}/messages',
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
            'want_ack': False,
            'port_num': 1
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        'status': 'success',
        'routing_mode': 'broadcast',
        'packet': {
            'id': 12345,
            'from': 0,
            'to': 0,
            'channel': 0,
            'port_num': 1,
            'text': f'{"0"*191}<|TRUNC|>',
            'want_ack': False,
            'want_response': False
        },
        'on_response_callback_payload': None,
        'truncated': True
    }


@pytest.mark.parametrize('valid_node_target', [
    '!00000000',
    '0',
])
def test_create_node_text_message_truncated_ok_radio(client_radio_ok,
                                                     mock_radio_ok,
                                                     valid_node_target):
    response = client_radio_ok.post(
        f'/api/v1/nodes/{valid_node_target}/messages',
        json={
            'text': '0' * 201,
            'want_ack': False,
            'want_response': False,
            'port_num': 1
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        'status': 'success',
        'routing_mode': 'direct',
        'packet': {
            'id': 12345,
            'from': 0,
            'to': 0,
            'channel': 0,
            'port_num': 1,
            'text': f'{"0"*191}<|TRUNC|>',
            'want_ack': False,
            'want_response': False
        },
        'on_response_callback_payload': None,
        'truncated': True
    }


def test_create_channel_text_message_maximum_mtu_ok_radio(
        client_radio_ok, mock_radio_ok):
    response = client_radio_ok.post(
        '/api/v1/channels/0/messages',
        json={
            'text': '0' * 200,
            'want_ack': False,
            'port_num': 1
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        'status': 'success',
        'routing_mode': 'broadcast',
        'packet': {
            'id': 12345,
            'from': 0,
            'to': 0,
            'channel': 0,
            'port_num': 1,
            'text': f'{"0"*200}',
            'want_ack': False,
            'want_response': False
        },
        'on_response_callback_payload': None,
        'truncated': False
    }


@pytest.mark.parametrize('valid_node_target', [
    '!00000000',
    '0',
])
def test_create_node_text_message_maximum_mtu_ok_radio(client_radio_ok,
                                                       mock_radio_ok,
                                                       valid_node_target):
    response = client_radio_ok.post(
        f'/api/v1/nodes/{valid_node_target}/messages',
        json={
            'text': '0' * 200,
            'want_ack': False,
            'want_response': False,
            'port_num': 1
        },
    )
    assert response.status_code == status.HTTP_202_ACCEPTED
    assert response.json() == {
        'status': 'success',
        'routing_mode': 'direct',
        'packet': {
            'id': 12345,
            'from': 0,
            'to': 0,
            'channel': 0,
            'port_num': 1,
            'text': f'{"0"*200}',
            'want_ack': False,
            'want_response': False
        },
        'on_response_callback_payload': None,
        'truncated': False
    }


@pytest.mark.parametrize(
    'invalid_channel',
    [
        # Out of bounds.
        -10**6,
        -1,
        8,
        10**6,

        # Junk.
        'a',
        'foo',
        None,
        True,
        [],
    ])
def test_create_channel_text_message_invalid_channel_ok_radio(
        client_radio_ok, mock_radio_ok, invalid_channel):
    response = client_radio_ok.post(
        f'/api/v1/channels/{invalid_channel}/messages',
        json={
            'text': 'Foo',
            'want_ack': False,
            'port_num': 1
        },
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_CONTENT


@pytest.mark.parametrize(
    'invalid_port_num',
    [
        # Out of bounds.
        -1,
        512,

        # Junk.
        'a',
        None,
        True,
        [],
    ])
def test_create_channel_text_message_invalid_porntnum_ok_radio(
        client_radio_ok, mock_radio_ok, invalid_port_num):
    response = client_radio_ok.post(
        '/api/v1/channels/0/messages',
        json={
            'text': 'Foo',
            'port_num': invalid_port_num
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
