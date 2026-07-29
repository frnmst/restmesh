# SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)
#
# SPDX-License-Identifier: GPL-3.0-or-later

import argparse
import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Any, Literal

import meshtastic.serial_interface
import uvicorn
from fastapi import FastAPI, Request, status
from google.protobuf.json_format import MessageToDict
from meshtastic.mesh_interface import MeshInterface
from pydantic import BaseModel, Field

from . import data_types, http_exceptions

MESHTASTIC_SERIAL_DEV: str = '/dev/ttyUSB0'
MESHTASTIC_SERIAL_DEV_RECONNECTION_TIMEOUT_SEC: int = 5
MESSAGE_QUEUE_TIMEOUT_BETWEEN_SENT_PACKETS_SEC: int = 3
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


class MessageQueueTask:
    """A FIFO queue that handles all the outbound Meshtastic messages."""

    def __init__(self, params: dict[str, Any]):
        self.params = params
        self.future: asyncio.Future = asyncio.get_running_loop().create_future(
        )


async def meshtastic_packet_worker(app: FastAPI):
    r"""Manage outbound messages thread."""
    logging.info(
        'Meshtastic message sender (packet) background worker started')

    while True:
        task: MessageQueueTask = await app.state.packet_queue.get()

        try:
            radio_interface = app.state.radio
            if radio_interface is None:
                raise RuntimeError('Radio is still not ready. Retry later.')

            p: dict = task.params

            # See:
            # https://meshtastic.org/docs/overview/mesh-algo/#layer-2-reliable-zero-hop-messaging
            # for wantAck.
            raw_packet: meshtastic.protobuf.mesh_pb2.MeshPacket = radio_interface.sendText(
                text=p['text'],
                destinationId=p['destination_id'],
                wantAck=p['want_ack'],
                wantResponse=p['want_response'],
                channelIndex=p['channel_index'],
                portNum=p['port_num'],
                onResponse=None)

            # Decode protobuf to Python dict.
            decoded_packet: dict[str, Any] = MessageToDict(
                raw_packet, preserving_proto_field_name=True)

            logging.info('Full raw packet:')
            logging.info('')
            logging.info(f'{decoded_packet}')
            logging.info('')

            packet_id: int = getattr(decoded_packet, 'id', 0)
            from_node_raw: int = getattr(decoded_packet, 'from_', 0)
            to_node_raw: int = getattr(decoded_packet, 'to', 0)
            channel_raw: int = getattr(decoded_packet, 'channel', 0)

            sent_packet: dict[str, Any] = {
                'id': packet_id,
                'from': from_node_raw,
                'to': to_node_raw,
                'channel': channel_raw,
                'portnum': p['port_num'],
                'text': p['text'],
                'wantAck': p['want_ack'],
                'wantResponse': p['want_response']
            }

            logging.info('radio returned:')
            logging.info(f'  Packet transmitted with ID -> {packet_id}')
            logging.info(f'  text                       -> \'{p["text"]}\'')
            logging.info(
                f'  destinationId              -> {p["destination_id"]}')
            logging.info(
                f'  channelIndex               -> {p["channel_index"]}')
            logging.info(f'  portNum                    -> {p["port_num"]}')
            logging.info('')

            # No callback data for the moment.
            task.future.set_result((sent_packet, None))

            # Do not overwhelm the mesh.
            # FIXME: there are probably better ways to do this.
            await asyncio.sleep(MESSAGE_QUEUE_TIMEOUT_BETWEEN_SENT_PACKETS_SEC)

        except MeshInterface.MeshInterfaceError as e:
            logging.error(f'Meshtastic protocol error: {e}')
            task.future.set_exception(e)
        except Exception as e:
            logging.error(f'Local USB/Serial communication failure: {e}')
            task.future.set_exception(e)
        finally:
            app.state.packet_queue.task_done()


async def meshtastic_reconnector(app: FastAPI):
    while app.state.running:
        if app.state.radio is None:
            logging.info('Connecting to radio')

            try:
                loop = asyncio.get_running_loop()

                # Connect to the radio in a background thread so FastAPI can
                # continue working.
                interface = await loop.run_in_executor(
                    None, lambda: meshtastic.serial_interface.SerialInterface(
                        devPath=MESHTASTIC_SERIAL_DEV))
                app.state.radio = interface
                logging.info(
                    f'Connected to radio via serial on {MESHTASTIC_SERIAL_DEV}'
                )
            except FileNotFoundError as e:
                app.state.radio = None
                logging.error(e)
                logging.warning(
                    f'Radio serial device {MESHTASTIC_SERIAL_DEV} not found')
            except Exception as e:
                app.state.radio = None
                logging.error(e)
                logging.warning(
                    f'Radio serial device {MESHTASTIC_SERIAL_DEV} unavailable')
        else:
            try:
                if hasattr(app.state.radio,
                           'stream') and app.state.radio.stream is None:
                    raise Exception('Serial stream interrupted')
            except Exception as e:
                logging.error(e)
                logging.warning(
                    'Detected radio disconnection in background, forcing quit')
                try:
                    app.state.radio.close()
                except Exception as e:
                    logging.info('Unhandled exception, continuing')
                    logging.warning(e)
                app.state.radio = None

        await asyncio.sleep(MESHTASTIC_SERIAL_DEV_RECONNECTION_TIMEOUT_SEC)


# https://fastapi.tiangolo.com/advanced/events/#lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.radio = None
    app.state.running: bool = True
    reconnect_task = asyncio.create_task(meshtastic_reconnector(app))
    app.state.packet_queue = asyncio.Queue(
        maxsize=MESSAGE_QUEUE_SIZE_BEFORE_HTTP_429)
    worker_task = asyncio.create_task(meshtastic_packet_worker(app))

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
              version='0.1.0',
              lifespan=lifespan)


class ChannelBroadcastPayload(BaseModel):
    text: data_types.TextMessagePayload
    wantAck: data_types.WantAck = False
    portNum: data_types.PortNum = 1


class NodeDirectPayload(BaseModel):
    text: data_types.TextMessagePayload
    wantAck: data_types.WantAck = False
    wantResponse: data_types.WantResponse = True
    portNum: data_types.PortNum = 1


class AppriseJsonChannelBroadcastPayload(BaseModel):
    version: str
    title: data_types.AppriseNotificationTitle = ''
    message: data_types.TextMessagePayload
    type: data_types.AppriseNotificationType = 'info'
    attachment: list = Field(default=[], description='Unused parameter')
    wantAck: data_types.WantAck = False
    portNum: data_types.PortNum = 1


class AppriseJsonNodeDirectPayload(BaseModel):
    version: str
    title: data_types.AppriseNotificationTitle = ''
    message: data_types.TextMessagePayload
    type: data_types.AppriseNotificationType = 'info'
    attachment: list = Field(default=[], description='Unused parameter')
    wantAck: data_types.WantAck = False
    wantResponse: data_types.WantResponse = True
    portNum: data_types.PortNum = 1


# Response schemas.
class MeshPacketDetails(BaseModel):
    id: int
    from_node: int | str = Field(alias='from')
    to_node: int | str = Field(alias='to')
    channel: data_types.ChannelIndex
    portnum: data_types.PortNum
    text: str = Field(description='The message sent to the mesh')
    wantAck: data_types.WantAck
    wantResponse: data_types.WantResponse


class MeshActionResponse(BaseModel):
    status: Literal['success']
    routing_mode: Literal['broadcast', 'direct']
    packet: MeshPacketDetails
    onResponse_callback_payload: dict[str, Any] | None = None
    truncated: bool = False


async def meshtastic_send_text(
        # radio_interface: meshtastic.serial_interface.SerialInterface,
        app: FastAPI,
        text: str,
        destination_id: int | str,
        channel_index: int,
        want_ack: bool,
        want_response: bool,
        port_num: int) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Interface with Python Meshtastic interface.sendText() method."""
    if (not hasattr(app.state, 'radio')
            or not getattr(app.state, 'radio', None)):
        raise http_exceptions.RADIO_UNAVAILABLE_503
    if app.state.packet_queue.qsize() >= MESSAGE_QUEUE_SIZE_BEFORE_HTTP_429:
        raise http_exceptions.QUEUE_FULL_429

    params: dict = {
        'text': text,
        'destination_id': destination_id,
        'channel_index': channel_index,
        'want_ack': want_ack,
        'want_response': want_response,
        'port_num': port_num
    }
    task = MessageQueueTask(params)
    await app.state.packet_queue.put(task)

    try:
        sent_packet, callback_data = await task.future
        return sent_packet, callback_data
    except MeshInterface.MeshInterfaceError as e:
        logging.error(f'Meshtastic protocol error: {e}')
        raise http_exceptions.RADIO_PROTOCOL_ERROR_503
    except Exception as e:
        logging.error(f'Local USB/Serial communication or other failure: {e}')
        raise http_exceptions.RADIO_USB_OR_SERIAL_FAILURE_503


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

    packet, _ = await meshtastic_send_text(app=app,
                                           text=payload.text,
                                           destination_id=0xffffffff,
                                           channel_index=channel_index,
                                           want_ack=payload.wantAck,
                                           want_response=False,
                                           port_num=payload.portNum)
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

    packet, _ = await meshtastic_send_text(app=app,
                                           text=payload.text,
                                           destination_id=node_target,
                                           channel_index=0,
                                           want_ack=payload.wantAck,
                                           want_response=payload.wantResponse,
                                           port_num=payload.portNum)
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

    packet, _ = await meshtastic_send_text(app=app,
                                           text=payload.message,
                                           destination_id=0xffffffff,
                                           channel_index=channel_index,
                                           want_ack=payload.wantAck,
                                           want_response=False,
                                           port_num=payload.portNum)
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

    packet, _ = await meshtastic_send_text(app=app,
                                           text=payload.text,
                                           destination_id=node_target,
                                           channel_index=0,
                                           want_ack=payload.wantAck,
                                           want_response=payload.wantResponse,
                                           port_num=payload.portNum)
    return MeshActionResponse(status='success',
                              routing_mode='direct',
                              packet=MeshPacketDetails(**packet),
                              truncated=is_truncated)


def cli():
    global MESHTASTIC_SERIAL_DEV

    parser = argparse.ArgumentParser(
        description='restmesh: stateless thread-safe REST API for Meshtastic')

    parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Server host listening address (default: 127.0.0.1)')
    parser.add_argument('--port',
                        type=int,
                        default=8000,
                        help='Server listening port (default: 8000)')
    parser.add_argument(
        '--radio-serial-path',
        type=str,
        default=MESHTASTIC_SERIAL_DEV,
        help=
        f'Path of the USB serial device radio (default: {MESHTASTIC_SERIAL_DEV})'
    )

    args = parser.parse_args()

    MESHTASTIC_SERIAL_DEV = args.radio_serial_path
    uvicorn.run('restmesh.main:app',
                host=args.host,
                port=args.port,
                reload=False)


if __name__ == '__main__':
    cli()
