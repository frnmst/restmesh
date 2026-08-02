<!--
SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)

SPDX-License-Identifier: GPL-3.0-or-later
-->

# restmesh

[![Buy me a coffee](assets/buy_me_a_coffee.svg)](https://buymeacoff.ee/frnmst)

A stateless thread-safe REST API for Meshtastic.

<!--TOC-->

- [restmesh](#restmesh)
  - [Description and features](#description-and-features)
  - [Quickstart](#quickstart)
    - [Installation](#installation)
    - [CLI help](#cli-help)
    - [Running](#running)
      - [Defaults](#defaults)
      - [Globally](#globally)
    - [Use the Core API](#use-the-core-api)
  - [REST API reference](#rest-api-reference)
    - [\[POST\] /api/v1/channels/{channel_index}/messages](#post-apiv1channelschannel_indexmessages)
      - [Parameters](#parameters)
      - [Request Body](#request-body)
      - [Responses](#responses)
    - [\[POST\] /api/v1/nodes/{node_target}/messages](#post-apiv1nodesnode_targetmessages)
      - [Parameters](#parameters-1)
      - [Request Body](#request-body-1)
      - [Responses](#responses-1)
    - [\[POST\] /api/v1/integrations/apprise/channels/{channel_index}/messages](#post-apiv1integrationsapprisechannelschannel_indexmessages)
      - [Parameters](#parameters-2)
      - [Request Body](#request-body-2)
      - [Responses](#responses-2)
    - [\[POST\] /api/v1/integrations/apprise/nodes/{node_target}/messages](#post-apiv1integrationsapprisenodesnode_targetmessages)
      - [Parameters](#parameters-3)
      - [Request Body](#request-body-3)
      - [Responses](#responses-3)
    - [Schemas](#schemas)
      - [AppriseJsonChannelBroadcastPayload Schema](#apprisejsonchannelbroadcastpayload-schema)
      - [AppriseJsonNodeDirectPayload Schema](#apprisejsonnodedirectpayload-schema)
      - [ChannelBroadcastPayload Schema](#channelbroadcastpayload-schema)
      - [HTTPValidationError Schema](#httpvalidationerror-schema)
      - [MeshActionResponse Schema](#meshactionresponse-schema)
      - [MeshPacketDetails Schema](#meshpacketdetails-schema)
      - [NodeDirectPayload Schema](#nodedirectpayload-schema)
      - [QueueErrorResponse Schema](#queueerrorresponse-schema)
      - [RadioErrorResponse Schema](#radioerrorresponse-schema)
      - [ValidationError Schema](#validationerror-schema)
  - [Integrations](#integrations)
    - [Apprise](#apprise)
      - [Channel](#channel)
      - [Node](#node)
  - [Contributing](#contributing)
  - [Responsible usage policy](#responsible-usage-policy)
    - [Meshtastic](#meshtastic)
  - [Consulting and custom integrations](#consulting-and-custom-integrations)
  - [License](#license)
  - [Changelog and trusted source](#changelog-and-trusted-source)
  - [Git forge mirrors](#git-forge-mirrors)
  - [Support this project](#support-this-project)

<!--TOC-->

## Description and features

Send messages on Meshtastic using a standard REST API:

- thread safe via asyncio
- safe because a FIFO queue avoid overwhelming the mesh
- very simple to integrate in other projects:
  [Apprise](https://appriseit.com/) is [already available](#apprise)
- aims to have 100% unit test coverage
- doesn't use a database, it merely acts as a gateway
- no MQTT, WiFI, bluetooth: just plug in the radio via USB, set it as
  `CLIENT_MUTE` and enjoy

A typical use case for restmesh is for system error reporting, for
example when local Internet is down. You could set up a script to interface
with restmesh like this:

```shell
#!/usr/bin/env bash

# See:
# https://www.iana.org/domains/root/servers
#
# It is very improbable that 3 root DNS server go simultaneously offline.
#
ANYCAST_1='198.41.0.4'
ANYCAST_2='192.36.148.17'
ANYCAST_3='202.12.27.33'

(nc -zu -w 2 "${ANYCAST_1}" 53 \
 || nc -zu -w 2 "${ANYCAST_2}" 53 \
 || nc -zu -w 2 "${ANYCAST_3}" 53) 2>/dev/null \
&& anycast_ok='true' || anycast_ok='false'

if [ "${anycast_ok}" = 'false' ]; then
    echo 'Internet unreachable, alerting mesh channel'

    # Use Meshtastic channel 1 (a non-primary channel).
    # Channel IDs are the same reported in the mobile app.
    #
    # You need to install apprise first via pip or your distro's package
    # manager.
    apprise -b 'ERROR: Internet unreachable' "json://127.0.0.1:8000/api/v1/integrations/apprise/channels/1/messages"
fi
```

## Quickstart

### Installation

```shell
pip install restmesh
```

### CLI help

```
usage: restmesh [-h] [--host HOST] [--port PORT] [--radio-serial-path RADIO_SERIAL_PATH]

restmesh: stateless thread-safe REST API for Meshtastic

options:
  -h, --help            show this help message and exit
  --host HOST           Server host listening address (default: 127.0.0.1)
  --port PORT           Server listening port (default: 8000)
  --radio-serial-path RADIO_SERIAL_PATH
                        Path of the USB serial device radio (default: /dev/ttyUSB0)
```

### Running

#### Defaults

```shell
restmesh --host 127.0.0.1 --port 8000 --radio-serial-path /dev/ttyUSB0
```

Connect to [http://127.0.0.1/docs](http://127.0.0.1/docs) for the Swagger page
to test the endpoints, or use [Apprise](#apprise) directly.

#### Globally

```shell
restmesh --host 0.0.0.0 --port 8000 --radio-serial-path /dev/ttyUSB0
```

> [!WARNING]
> At the moment no kind of authentication is implemented!

### Use the Core API

Send to channel 0 (the primary channel):

```shell
curl -X 'POST' \
'http://127.0.0.1:8000/api/v1/channels/0/messages' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "This is a message for the mesh on channel 0!",
  "wantAck": false,
  "portNum": 1
}'
```

Send to node `!0a1b2c3d`:

```shell
curl -X 'POST' \
  'http://127.0.0.1:8000/api/v1/nodes/%210a1b2c3d/messages' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "text": "This is a message for node !0a1b2c3d",
  "wantAck": false,
  "wantResponse": true,
  "portNum": 1
}'
```

## REST API reference

This endpoint documentation is automatically generated from FastAPI OpenAPI's
generator and
[swagger-markdown](https://www.npmjs.com/package/swagger-markdown).

<!-- START_API_DOCS -->
---

### [POST] /api/v1/channels/{channel_index}/messages
**Send a message to a channel**

Broadcast a text message to a specific mesh channel.

#### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ------ |
| channel_index | path | The channel index (0 to 7) | Yes | integer |

#### Request Body

| Required | Schema |
| -------- | ------ |
|  Yes | **application/json**: [ChannelBroadcastPayload](#channelbroadcastpayload-schema)<br> |

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 202 | Successful Response | **application/json**: [MeshActionResponse](#meshactionresponse-schema)<br> |
| 422 | Validation Error | **application/json**: [HTTPValidationError](#httpvalidationerror-schema)<br> |
| 429 | Unable to handle more requests because the FIFO queue is full | **application/json**: [QueueErrorResponse](#queueerrorresponse-schema)<br> |
| 503 | Meshtastic radio problem. Different errors can be returned. | **application/json**: [RadioErrorResponse](#radioerrorresponse-schema)<br> |

### [POST] /api/v1/nodes/{node_target}/messages
**Send Text To Node**

Send a DM text to a node via nodeId string or nodeNum integer.

#### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ------ |
| node_target | path | Target destination: can be a lowercase hex string NodeId (e.g. !2c3b4f5a) or a numeric NodeNum < 2^32 (e.g. 60). | Yes | string or integer |

#### Request Body

| Required | Schema |
| -------- | ------ |
|  Yes | **application/json**: [NodeDirectPayload](#nodedirectpayload-schema)<br> |

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 202 | Successful Response | **application/json**: [MeshActionResponse](#meshactionresponse-schema)<br> |
| 422 | Validation Error | **application/json**: [HTTPValidationError](#httpvalidationerror-schema)<br> |
| 429 | Unable to handle more requests because the FIFO queue is full | **application/json**: [QueueErrorResponse](#queueerrorresponse-schema)<br> |
| 503 | Meshtastic radio problem. Different errors can be returned. | **application/json**: [RadioErrorResponse](#radioerrorresponse-schema)<br> |

---

### [POST] /api/v1/integrations/apprise/channels/{channel_index}/messages
**Apprise Gateway Adapter Send Text Channel**

Adapter gateway.

#### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ------ |
| channel_index | path | The channel index (0 to 7) | Yes | integer |

#### Request Body

| Required | Schema |
| -------- | ------ |
|  Yes | **application/json**: [AppriseJsonChannelBroadcastPayload](#apprisejsonchannelbroadcastpayload-schema)<br> |

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 202 | Successful Response | **application/json**: [MeshActionResponse](#meshactionresponse-schema)<br> |
| 422 | Validation Error | **application/json**: [HTTPValidationError](#httpvalidationerror-schema)<br> |
| 429 | Unable to handle more requests because the FIFO queue is full | **application/json**: [QueueErrorResponse](#queueerrorresponse-schema)<br> |
| 503 | Meshtastic radio problem. Different errors can be returned. | **application/json**: [RadioErrorResponse](#radioerrorresponse-schema)<br> |

### [POST] /api/v1/integrations/apprise/nodes/{node_target}/messages
**Apprise Gateway Adapter Send Text Node**

Adapter gateway.

#### Parameters

| Name | Located in | Description | Required | Schema |
| ---- | ---------- | ----------- | -------- | ------ |
| node_target | path | Target destination: can be a lowercase hex string NodeId (e.g. !2c3b4f5a) or a numeric NodeNum < 2^32 (e.g. 60). | Yes | string or integer |

#### Request Body

| Required | Schema |
| -------- | ------ |
|  Yes | **application/json**: [AppriseJsonNodeDirectPayload](#apprisejsonnodedirectpayload-schema)<br> |

#### Responses

| Code | Description | Schema |
| ---- | ----------- | ------ |
| 202 | Successful Response | **application/json**: [MeshActionResponse](#meshactionresponse-schema)<br> |
| 422 | Validation Error | **application/json**: [HTTPValidationError](#httpvalidationerror-schema)<br> |
| 429 | Unable to handle more requests because the FIFO queue is full | **application/json**: [QueueErrorResponse](#queueerrorresponse-schema)<br> |
| 503 | Meshtastic radio problem. Different errors can be returned. | **application/json**: [RadioErrorResponse](#radioerrorresponse-schema)<br> |

---
### Schemas

#### AppriseJsonChannelBroadcastPayload Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| version | string | Apprise JSON schema version | Yes |
| title | string or null | Unused parameter | No |
| message | string | UTF-8 text limited to the 237 byte Meshtastic MTU (200 here for safety) | Yes |
| type | string, <br>**Available values:** "info", "warning", "success", "failure" or null | Unused parameter | No |
| attachment | [  ], <br>**Default:**  | Unused parameter | No |
| wantAck | boolean | `true` if you want the message sent in a reliable manner (with retries and ack/nak provided for delivery) | No |
| portNum | integer, <br>**Default:** 1 | Protobuf application port number | No |

#### AppriseJsonNodeDirectPayload Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| version | string | Apprise JSON schema version | Yes |
| title | string or null | Unused parameter | No |
| message | string | UTF-8 text limited to the 237 byte Meshtastic MTU (200 here for safety) | Yes |
| type | string, <br>**Available values:** "info", "warning", "success", "failure" or null | Unused parameter | No |
| attachment | [  ], <br>**Default:**  | Unused parameter | No |
| wantAck | boolean | `true` if you want the message sent in a reliable manner (with retries and ack/nak provided for delivery) | No |
| wantResponse | boolean, <br>**Default:** true | `true` if you want the service on the other side to send an application layer response | No |
| portNum | integer, <br>**Default:** 1 | Protobuf application port number | No |

#### ChannelBroadcastPayload Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| text | string | UTF-8 text limited to the 237 byte Meshtastic MTU (200 here for safety) | Yes |
| wantAck | boolean | `true` if you want the message sent in a reliable manner (with retries and ack/nak provided for delivery) | No |
| portNum | integer, <br>**Default:** 1 | Protobuf application port number | No |

#### HTTPValidationError Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| detail | [ [ValidationError](#validationerror-schema) ] |  | No |

#### MeshActionResponse Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| status | string | Always return "success" | Yes |
| routing_mode | string, <br>**Available values:** "broadcast", "direct" | Message routing type<br>*Enum:* `"broadcast"`, `"direct"` | Yes |
| packet | [MeshPacketDetails](#meshpacketdetails-schema) | Packet data from radio | Yes |
| onResponse_callback_payload | object or null |  | No |
| truncated | boolean | Message was truncated to Meshtastic MTU before being sent | No |

#### MeshPacketDetails Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| id | integer |  | Yes |
| from | integer or string |  | Yes |
| to | integer or string |  | Yes |
| channel | integer | The channel index (0 to 7) | Yes |
| portnum | integer | Protobuf application port number | Yes |
| text | string | The message sent to the mesh | Yes |
| wantAck | boolean | `true` if you want the message sent in a reliable manner (with retries and ack/nak provided for delivery) | No |
| wantResponse | boolean, <br>**Default:** true | `true` if you want the service on the other side to send an application layer response | No |

#### NodeDirectPayload Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| text | string | UTF-8 text limited to the 237 byte Meshtastic MTU (200 here for safety) | Yes |
| wantAck | boolean | `true` if you want the message sent in a reliable manner (with retries and ack/nak provided for delivery) | No |
| wantResponse | boolean, <br>**Default:** true | `true` if you want the service on the other side to send an application layer response | No |
| portNum | integer, <br>**Default:** 1 | Protobuf application port number | No |

#### QueueErrorResponse Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| detail | string, <br>**Default:** Unable to handle more requests, queue full. |  | No |

#### RadioErrorResponse Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| detail | string, <br>**Default:** Meshtastic radio problem |  | No |

#### ValidationError Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| loc | [ string or integer ] |  | Yes |
| msg | string |  | Yes |
| type | string |  | Yes |
| input |  |  | No |
| ctx | object |  | No |

<!-- END_API_DOCS -->

## Integrations

### Apprise

restmesh accepts [Apprise](https://appriseit.com/) via the JSON schema. To be
able to use it you need to
[install it first](https://appriseit.com/getting-started/installation/).
See also the [Repology](https://repology.org/projects/?search=apprise) page
to see the available packages for Apprise.

> [!NOTE]
> The title parameter is ignored! Write your full text in the body.

#### Channel

Simple example using channel 0:

```shell
apprise -b 'My message here' "json://localhost:8000/api/v1/integrations/apprise/channels/0/messages"
```

With parameters:

```shell
apprise -b 'Hello world!' "json://localhost:8000/api/v1/integrations/apprise/channels/0/messages?:wantAck=false&:portNum=1"
```

#### Node

Send a message to the node with hex id `!0a1b2c3d`. Alternatively you can use
the decimal integer representation of the node id, without prepending the
`!` character:

```shell
apprise -b 'My message here' "json://localhost:8000/api/v1/integrations/apprise/nodes/!0a1b2c3d/messages"

apprise -b 'My message here' "json://localhost:8000/api/v1/integrations/apprise/nodes/169552957/messages"
```

With parameters:

```shell
apprise -b 'Hello world!' "json://localhost:8000/api/v1/integrations/apprise/nodes/!0a1b2c3d/messages?:wantResponse=true&wantAck=false&:portNum=1"

apprise -b 'Hello world!' "json://localhost:8000/api/v1/integrations/apprise/nodes/169552957/messages?:wantResponse=true&wantAck=false&:portNum=1"
```

## Contributing

See [Contributing](./CONTRIBUTING.md).

## Responsible usage policy

### Meshtastic

In some places, such as Europe, the non-ham LoRa band has limited air time use.
Please don't use restmesh for mass spamming, and never broadcast automated
messages on public channels such as `MediumFast` or `LongFast`. Setup private
channels instead.

restmesh has a basic message FIFO queue also to mitigate the air time problem.

## Consulting and custom integrations

If you need help or custom endpoints and integrations, I'm available for
contract-based freelance consulting and custom Python development:

- Email: <solvecomputersciencecollabs+restmesh@gmail.com>
- Freelancing: <https://blog.franco.net.eu.org/jobs/>

## License

Copyright (C) 2026 [Franco Masotti](https://blog.franco.net.eu.org/about/#contacts)

restmesh is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free
Software Foundation, either version 3 of the License, or (at your
option) any later version.

restmesh is distributed in the hope that it will be useful, but WITHOUT
ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
more details.

You should have received a copy of the GNU General Public License along
with restmesh. If not, see <http://www.gnu.org/licenses/>.

## Changelog and trusted source

You can check the authenticity of new releases using my public key.

Changelogs, instructions, sources and keys can be found at
[blog.franco.net.eu.org/software/#restmesh](https://blog.franco.net.eu.org/software/#restmesh).

## Git forge mirrors

| URL | Type | Notes |
|-----|------|-------|
| https://github.com/frnmst/restmesh | RW | Official home |
| https://codeberg.org/frnmst/restmesh | RW | Mirror |
| https://framagit.org/frnmst/restmesh | RW | Mirror |
| https://repos.franco.net.eu.org/frnmst/restmesh | RW | Mirror |

## Support this project

- [Buy Me a Coffee](https://www.buymeacoffee.com/frnmst)
- [Liberapay](https://liberapay.com/frnmst)
- [GitHub Sponsors](https://github.com/sponsors/frnmst)
