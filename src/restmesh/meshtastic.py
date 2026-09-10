# SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)
#
# SPDX-License-Identifier: GPL-3.0-or-later

import asyncio
import importlib
import logging
from typing import Any

import meshtastic.serial_interface
from fastapi import FastAPI
from google.protobuf.json_format import MessageToDict
from meshtastic.mesh_interface import MeshInterface
from pubsub import pub

from . import http_exceptions

MESHTASTIC_SERIAL_DEV_RECONNECTION_TIMEOUT_SEC: int = 5
MESSAGE_QUEUE_TIMEOUT_BETWEEN_SENT_PACKETS_SEC: int = 3


class MessageQueueTask:
    """A FIFO queue that handles all the outbound Meshtastic messages."""

    def __init__(self, params: dict[str, Any]):
        self.params = params
        self.future: asyncio.Future = asyncio.get_running_loop().create_future(
        )


def reply_to_mesh_command(text_reply: str, app, destination_node: int):
    r"""Send a reply to a mesh-received command."""
    asyncio.run_coroutine_threadsafe(
        meshtastic_send_text(app=app,
                             text=text_reply,
                             destination_id=destination_node,
                             channel_index=0,
                             want_ack=True,
                             want_response=False,
                             port_num=1), app.state.fastapi_loop)


def onReceive(app, packet, interface):
    r"""pub-sub on receive callback."""
    logging.debug('packet received')
    payload_object: dict = packet.get('decoded', {})
    this_nodeinfo: dict = interface.getMyNodeInfo()

    # Filter by texts.
    if payload_object.get('portnum', '') == 'TEXT_MESSAGE_APP':
        # Filter by node connected to this computer.
        if packet.get('to', -1) == this_nodeinfo.get('num', -1):
            logging.info(f'text packet sent to this node: {packet}')
            text_message: str = payload_object.get('text', '').strip()

            destination_node: int = packet.get('from', -1)
            match text_message:
                case '!help' | '/help':
                    commands: str = '\n'.join(
                        ['!api', '!help', '!motd', '!ping'])
                    reply_to_mesh_command(commands, app, destination_node)
                case '!api' | '/api':
                    software_name: str = 'restmesh'
                    software_meta: dict = importlib.metadata.metadata(
                        software_name)
                    software_home: str = software_meta['Project-URL'].replace(
                        ',', ':')
                    software_version: str = software_meta['Version']
                    software_summary: str = software_meta['Summary']
                    final_string: str = '\n'.join([
                        f'API: {software_name} {software_version}',
                        software_summary, f'{software_home}'
                    ])
                    reply_to_mesh_command(final_string, app, destination_node)
                case '!motd' | '/motd':
                    reply_to_mesh_command('MOTD: not implemented', app,
                                          destination_node)
                case '!ping' | '/ping':
                    reply_to_mesh_command('pong', app, destination_node)
                case _:
                    commands: str = '\n'.join(
                        ['commands:', '!api', '!help', '!motd', '!ping'])
                    reply_to_mesh_command(commands, app, destination_node)
                    logging.info(f'unknown command: {text_message}')


async def meshtastic_packet_worker(app: FastAPI):
    r"""Manage outbound messages thread."""
    logging.info('Meshtastic message packet background worker started')

    # Enable receive commands.
    def callback_wrapper(packet, interface):
        onReceive(app, packet, interface)

    pub.subscribe(callback_wrapper, 'meshtastic.receive')

    while True:
        task: MessageQueueTask = await app.state.packet_queue.get()
        p: dict = task.params

        def handle_on_response(packet):
            r"""Radio returned NAK or wantResponse was set to true, need to retry with new attempt."""
            logging.info(f'NAK or wants response for packet {packet}')
            routing_error: str = packet.get('decoded',
                                            {}).get('routing', {}).get(
                                                'errorReason', 'unknown')

            if p['want_response'] and not p['want_ack']:
                logging.info(
                    'WantAck was set to false: unable to determine if packet was routed or not'
                )
            elif p['want_response'] and p[
                    'want_ack'] and routing_error == 'NO_RESPONSE':
                logging.info(
                    'unable to determine if packet was routed or not (normal behavior)'
                )
                logging.debug(
                    "Radio reports: 'NO_RESPONSE' but it's meaningless in this context"
                )
                logging.debug(
                    'onResponse callback was called immediately because WantResponse=True so radio did not have time to correctly check for routing'
                )
            elif routing_error not in ['unknown', 'NONE']:
                logging.warning(
                    f"radio reports a routing error '{routing_error}' for packet id {packet.get('requestId', 0)}"
                )
                logging.debug('retry strategy not implemented')
                # TODO
                # Some kind of retry strategy could be implemented here by
                # re-enqueueing the same packet and increasing the attempts
                # counter.

        try:
            radio_interface = app.state.radio
            if radio_interface is None:
                raise RuntimeError('Radio is still not ready. Retry later.')

            # See:
            # https://meshtastic.org/docs/overview/mesh-algo/#layer-2-reliable-zero-hop-messaging
            # for wantAck.
            # If WantAck is set, the following documentation from mesh.proto applies:
            # This packet is being sent as a reliable message, we would prefer
            # it to arrive at the destination. We would like to receive an ACK packet in response.
            raw_packet: meshtastic.protobuf.mesh_pb2.MeshPacket = radio_interface.sendText(
                text=p['text'],
                destinationId=p['destination_id'],
                wantAck=p['want_ack'],
                wantResponse=p['want_response'],
                channelIndex=p['channel_index'],
                portNum=p['port_num'],
                onResponse=handle_on_response)
            # onResponse -- A closure of the form funct(packet), that will be
            # called when a response packet arrives (or the transaction
            # is NAKed due to non receipt)

            # Decode protobuf to Python dict.
            decoded_packet: dict[str, Any] = MessageToDict(
                raw_packet, preserving_proto_field_name=True)

            logging.info('Full raw packet:')
            logging.info('')
            logging.info(f'{decoded_packet}')
            logging.info('')

            packet_id: int = decoded_packet.get('id', 0)
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
                'want_response': p['want_response'],
                'attempts': p['attempts']
            }

            logging.info('radio returned:')
            logging.info(f'  Packet transmitted with ID: {packet_id}')
            logging.info(f'  text                      : \'{p["text"]}\'')
            logging.info(
                f'  destinationId             : {p["destination_id"]}')
            logging.info(f'  channelIndex              : {p["channel_index"]}')
            logging.info(f'  portNum                   : {p["port_num"]}')
            logging.info('')

            if not task.future.done():
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
        'port_num': port_num,
        'attempts': 0,
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
