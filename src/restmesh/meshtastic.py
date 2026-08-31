# SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)
#
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import logging
from typing import Any

import meshtastic.serial_interface
from fastapi import FastAPI
from google.protobuf.json_format import MessageToDict
from meshtastic.mesh_interface import MeshInterface

from . import http_exceptions

MESHTASTIC_SERIAL_DEV_RECONNECTION_TIMEOUT_SEC: int = 5
MESSAGE_QUEUE_TIMEOUT_BETWEEN_SENT_PACKETS_SEC: int = 3


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
                'port_num': p['port_num'],
                'text': p['text'],
                'want_ack': p['want_ack'],
                'want_response': p['want_response']
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
                        devPath=app.state.radio_serial_dev))
                app.state.radio = interface

                logging.info(
                    f'Connected to radio via serial on {app.state.radio_serial_dev}'
                )
            except FileNotFoundError as e:
                app.state.radio = None
                logging.error(e)
                logging.warning(
                    f'Radio serial device {app.state.radio_serial_dev} not found'
                )
            except Exception as e:
                app.state.radio = None
                logging.error(e)
                logging.warning(
                    f'Radio serial device {app.state.radio_serial_dev} unavailable'
                )
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


async def meshtastic_send_text(
        app: FastAPI, text: str, destination_id: int | str, channel_index: int,
        want_ack: bool, want_response: bool,
        port_num: int) -> tuple[dict[str, Any], dict[str, Any] | None]:
    """Interface with Python Meshtastic interface.sendText() method."""
    if (not hasattr(app.state, 'radio')
            or not getattr(app.state, 'radio', None)):
        raise http_exceptions.RADIO_UNAVAILABLE_503
    if app.state.packet_queue.qsize() >= app.state.packet_queue.maxsize:
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


if __name__ == '__main__':
    pass
