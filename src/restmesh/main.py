# SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)
#
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import asyncio
import importlib.metadata
import logging
from contextlib import asynccontextmanager
from typing import Any, Optional

import meshtastic.serial_interface
import re2 as re
import uvicorn
from fastapi import FastAPI, Request, status
from pydantic import BaseModel, Field, model_validator

from . import data_types, http_exceptions, meshtastic

MESHTASTIC_SERIAL_DEV: str = '/dev/ttyUSB0'
MESSAGE_QUEUE_SIZE_BEFORE_HTTP_429: int = 10

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(module)s:%(lineno)d]: %(message)s'
)


class DetailResponse(BaseModel):
    """FastAPI error response schema."""

    detail: str


class RadioErrorResponse(BaseModel):
    detail: str = Field(default='Meshtastic radio problem')


class QueueErrorResponse(BaseModel):
    detail: str = Field(default=http_exceptions.QUEUE_FULL_429.detail)


SEND_MESSAGE_EXTRA_ERROR_RESPONSES: dict = {
    503: {
        'model':
        RadioErrorResponse,
        'description':
        'Meshtastic radio problem. Different errors can be returned.',
    },
    http_exceptions.QUEUE_FULL_429.status_code: {
        'model':
        QueueErrorResponse,
        'description':
        'Unable to handle more requests because the FIFO queue is full',
    }
}


# https://fastapi.tiangolo.com/advanced/events/#lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # The modem Meshtastic instance.
    app.state.radio = None

    # The modem device path.
    app.state.radio_serial_dev = MESHTASTIC_SERIAL_DEV
    app.state.running: bool = True

    # Main event loop.
    app.state.fastapi_loop = asyncio.get_running_loop()

    reconnect_task = asyncio.create_task(
        meshtastic.meshtastic_reconnector(app))
    app.state.packet_queue = asyncio.Queue(
        maxsize=MESSAGE_QUEUE_SIZE_BEFORE_HTTP_429)
    worker_task = asyncio.create_task(meshtastic.meshtastic_packet_worker(app))

    yield

    app.state.running = False

    worker_task.cancel()
    try:
        await worker_task
    except asyncio.CancelledError:
        logging.info('Meshtastic worker task closed')

    reconnect_task.cancel()
    try:
        await reconnect_task
    except asyncio.CancelledError:
        logging.info('Meshtastic reconnect task closed')

    if app.state.radio:
        app.state.radio.close()
        logging.info('Radio connection closed')


app = FastAPI(title='restmesh',
              description='Stateless thread-safe REST API for Meshtastic.',
              version=importlib.metadata.version('restmesh'),
              lifespan=lifespan)


def apply_regex_truncate_mtu(cls: Any, data: Any) -> Any:
    r"""Type validation is applied after this method."""
    if isinstance(data, dict):
        text: str = data.get('text')
        regex: dict = data.get('regex_subst', {'pattern': None, 'subst': None})
        pattern: str = regex.get('pattern', None)
        subst: str = regex.get('subst', None)

        if isinstance(text, str):
            if (isinstance(regex, dict) and pattern is not None
                    and subst is not None and isinstance(pattern, str)
                    and isinstance(subst, str)):
                try:
                    text = re.sub(pattern, subst, text)
                except re.error:
                    # Delegate error to the RegexSubst field validator.
                    pass

            data['text'] = data_types.truncate_to_meshtastic_mtu(text)

    return data


class CommonTextPayload(BaseModel):
    regex_subst: Optional[data_types.RegexSubst] = None

    @model_validator(mode='before')
    @classmethod
    def apply_regex_then_truncate_to_mtu(cls, data: Any) -> Any:
        return apply_regex_truncate_mtu(cls, data)


class SimpleCommonTextPayload(CommonTextPayload):
    text: data_types.TextMessagePayload
    want_ack: data_types.WantAck = True
    port_num: data_types.PortNum = 1


class ChannelBroadcastPayload(SimpleCommonTextPayload):
    pass


class NodeDirectPayload(SimpleCommonTextPayload):
    want_response: data_types.WantResponse = False


class AppriseCommonTextPayload(CommonTextPayload):
    version: data_types.AppriseJsonSchemaVersion
    title: data_types.AppriseNotificationTitle = ''
    message: data_types.TextMessagePayload
    type: data_types.AppriseNotificationType = 'info'
    attachment: list = Field(default=[], description='Unused parameter')
    want_ack: data_types.WantAck = True
    port_num: data_types.PortNum = 1


class AppriseJsonChannelBroadcastPayload(AppriseCommonTextPayload):
    pass


class AppriseJsonNodeDirectPayload(AppriseCommonTextPayload):
    want_response: data_types.WantResponse = False


# Response schemas.
class MeshPacketDetails(BaseModel):
    id: int
    from_node: int | str = Field(alias='from')
    to_node: int | str = Field(alias='to')
    channel: data_types.ChannelIndex
    port_num: data_types.PortNum
    text: str = Field(description='The message sent to the mesh')
    want_ack: data_types.WantAck
    want_response: data_types.WantResponse


class MeshActionResponse(BaseModel):
    status: data_types.MeshActionResponseStatus
    routing_mode: data_types.MeshActionResponseRoutingMode
    packet: MeshPacketDetails = Field(description='Packet data from radios')
    on_response_callback_payload: dict[str, Any] | None = None
    truncated: data_types.MeshActionResponseTruncated = False


@app.post('/api/v1/channels/{channel_index}/messages',
          status_code=status.HTTP_202_ACCEPTED,
          summary='Send a message to a channel',
          response_model=MeshActionResponse,
          responses=SEND_MESSAGE_EXTRA_ERROR_RESPONSES,
          tags=['Core Send'])
async def send_text_to_channel(
        payload: ChannelBroadcastPayload, request: Request,
        channel_index: data_types.ChannelIndex) -> MeshActionResponse:
    """Broadcast a text message to a specific mesh channel."""
    is_truncated: bool = data_types.truncated_message.get()
    data_types.truncated_message.set(False)

    packet, _ = await meshtastic.meshtastic_send_text(
        app=app,
        text=payload.text,
        destination_id=0xffffffff,
        channel_index=channel_index,
        want_ack=payload.want_ack,
        want_response=False,
        port_num=payload.port_num)
    return MeshActionResponse(status='success',
                              routing_mode='broadcast',
                              packet=MeshPacketDetails(**packet),
                              truncated=is_truncated)


@app.post('/api/v1/nodes/{node_target}/messages',
          status_code=status.HTTP_202_ACCEPTED,
          response_model=MeshActionResponse,
          responses=SEND_MESSAGE_EXTRA_ERROR_RESPONSES,
          tags=['Core Send'])
async def send_text_to_node(
        payload: NodeDirectPayload, request: Request,
        node_target: data_types.NodeTarget) -> MeshActionResponse:
    """Send a DM text to a node via nodeId string or nodeNum integer."""
    is_truncated: bool = data_types.truncated_message.get()
    data_types.truncated_message.set(False)

    packet, _ = await meshtastic.meshtastic_send_text(
        app=app,
        text=payload.text,
        destination_id=node_target,
        channel_index=0,
        want_ack=payload.want_ack,
        want_response=payload.want_response,
        port_num=payload.port_num)
    return MeshActionResponse(status='success',
                              routing_mode='direct',
                              packet=MeshPacketDetails(**packet),
                              truncated=is_truncated)


@app.post('/api/v1/integrations/apprise/channels/{channel_index}/messages',
          status_code=status.HTTP_202_ACCEPTED,
          response_model=MeshActionResponse,
          responses=SEND_MESSAGE_EXTRA_ERROR_RESPONSES,
          tags=['Integrations'])
async def apprise_gateway_adapter_send_text_channel(
        payload: AppriseJsonChannelBroadcastPayload,
        channel_index: data_types.ChannelIndex) -> MeshActionResponse:
    """Adapter gateway."""
    is_truncated: bool = data_types.truncated_message.get()
    data_types.truncated_message.set(False)

    packet, _ = await meshtastic.meshtastic_send_text(
        app=app,
        text=payload.message,
        destination_id=0xffffffff,
        channel_index=channel_index,
        want_ack=payload.want_ack,
        want_response=False,
        port_num=payload.port_num)
    return MeshActionResponse(status='success',
                              routing_mode='broadcast',
                              packet=MeshPacketDetails(**packet),
                              truncated=is_truncated)


@app.post('/api/v1/integrations/apprise/nodes/{node_target}/messages',
          status_code=status.HTTP_202_ACCEPTED,
          response_model=MeshActionResponse,
          responses=SEND_MESSAGE_EXTRA_ERROR_RESPONSES,
          tags=['Integrations'])
async def apprise_gateway_adapter_send_text_node(
        payload: AppriseJsonNodeDirectPayload, request: Request,
        node_target: data_types.NodeTarget) -> MeshActionResponse:
    """Adapter gateway."""
    is_truncated: bool = data_types.truncated_message.get()
    data_types.truncated_message.set(False)

    packet, _ = await meshtastic.meshtastic_send_text(
        app=app,
        text=payload.message,
        destination_id=node_target,
        channel_index=0,
        want_ack=payload.want_ack,
        want_response=payload.want_response,
        port_num=payload.port_num)
    return MeshActionResponse(status='success',
                              routing_mode='direct',
                              packet=MeshPacketDetails(**packet),
                              truncated=is_truncated)


def cli():
    global MESHTASTIC_SERIAL_DEV

    parser = argparse.ArgumentParser(
        description='restmesh: stateless thread-safe REST API for Meshtastic')
    parser.add_argument(
        '--version',
        action='version',
        version=importlib.metadata.version('restmesh'),
    )
    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='server host listening address (default: 127.0.0.1)')
    parser.add_argument('--port',
                        type=int,
                        default=8000,
                        help='server listening port (default: 8000)')
    parser.add_argument(
        '--radio-serial-path',
        type=str,
        default=MESHTASTIC_SERIAL_DEV,
        help=
        f'path of the USB serial device radio (default: {MESHTASTIC_SERIAL_DEV})'
    )

    args = parser.parse_args()

    MESHTASTIC_SERIAL_DEV = args.radio_serial_path

    logging.info(f'restmesh version {importlib.metadata.version("restmesh")}')
    uvicorn.run('restmesh.main:app',
                host=args.host,
                port=args.port,
                reload=False)


if __name__ == '__main__':
    cli()
