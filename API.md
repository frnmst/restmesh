<!--
SPDX-FileCopyrightText: 2026-2026 Franco Masotti (See /README.md)

SPDX-License-Identifier: GPL-3.0-or-later
-->

<!--TOC-->

- [REST API reference](#rest-api-reference)

<!--TOC-->

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
| regex_subst | [RegexSubst](#regexsubst-schema) or null |  | No |
| version | string | Apprise JSON schema version | Yes |
| title | string or null | Unused parameter | No |
| message | string | UTF-8 text to the mesh. This API limits it to 200 bytes for safety, although [the default Meshtastic MTU is 237 bytes](https://buf.build/meshtastic/protobufs/docs/86640f20db7b9b5be42949d18e8d96ad10d47a68%3Ameshtastic#meshtastic.Constants) | Yes |
| type | string, <br>**Available values:** "info", "warning", "success", "failure", "" or null | Unused parameter | No |
| attachment | [  ], <br>**Default:**  | Unused parameter | No |
| want_ack | boolean, <br>**Default:** true | `true` if you want the message sent in a reliable manner (with retries and ack/nak provided for delivery). Meshtastic's firmware will handle the retries. will [See this also](https://python.meshtastic.org/mesh_interface.html#meshtastic.mesh_interface.MeshInterface.sendText) | No |
| port_num | integer, <br>**Default:** 1 | Protobuf application port number | No |

#### AppriseJsonNodeDirectPayload Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| regex_subst | [RegexSubst](#regexsubst-schema) or null |  | No |
| version | string | Apprise JSON schema version | Yes |
| title | string or null | Unused parameter | No |
| message | string | UTF-8 text to the mesh. This API limits it to 200 bytes for safety, although [the default Meshtastic MTU is 237 bytes](https://buf.build/meshtastic/protobufs/docs/86640f20db7b9b5be42949d18e8d96ad10d47a68%3Ameshtastic#meshtastic.Constants) | Yes |
| type | string, <br>**Available values:** "info", "warning", "success", "failure", "" or null | Unused parameter | No |
| attachment | [  ], <br>**Default:**  | Unused parameter | No |
| want_ack | boolean, <br>**Default:** true | `true` if you want the message sent in a reliable manner (with retries and ack/nak provided for delivery). Meshtastic's firmware will handle the retries. will [See this also](https://python.meshtastic.org/mesh_interface.html#meshtastic.mesh_interface.MeshInterface.sendText) | No |
| port_num | integer, <br>**Default:** 1 | Protobuf application port number | No |
| want_response | boolean | `true` if you want the service on the other side to send an application layer response. [See this also](https://python.meshtastic.org/mesh_interface.html#meshtastic.mesh_interface.MeshInterface.sendText) | No |

#### ChannelBroadcastPayload Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| regex_subst | [RegexSubst](#regexsubst-schema) or null |  | No |
| text | string | UTF-8 text to the mesh. This API limits it to 200 bytes for safety, although [the default Meshtastic MTU is 237 bytes](https://buf.build/meshtastic/protobufs/docs/86640f20db7b9b5be42949d18e8d96ad10d47a68%3Ameshtastic#meshtastic.Constants) | Yes |
| want_ack | boolean, <br>**Default:** true | `true` if you want the message sent in a reliable manner (with retries and ack/nak provided for delivery). Meshtastic's firmware will handle the retries. will [See this also](https://python.meshtastic.org/mesh_interface.html#meshtastic.mesh_interface.MeshInterface.sendText) | No |
| port_num | integer, <br>**Default:** 1 | Protobuf application port number | No |

#### HTTPValidationError Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| detail | [ [ValidationError](#validationerror-schema) ] |  | No |

#### MeshActionResponse Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| status | string | Always return "success" | Yes |
| routing_mode | string, <br>**Available values:** "broadcast", "direct" | Message routing type<br>*Enum:* `"broadcast"`, `"direct"` | Yes |
| packet | [MeshPacketDetails](#meshpacketdetails-schema) | Packet data from radios | Yes |
| on_response_callback_payload | object or null |  | No |
| truncated | boolean | Message was truncated to Meshtastic MTU before being sent | No |

#### MeshPacketDetails Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| id | integer |  | Yes |
| from | integer or string |  | Yes |
| to | integer or string |  | Yes |
| channel | integer | The channel index (0 to 7) | Yes |
| port_num | integer | Protobuf application port number | Yes |
| text | string | The message sent to the mesh | Yes |
| want_ack | boolean | `true` if you want the message sent in a reliable manner (with retries and ack/nak provided for delivery). Meshtastic's firmware will handle the retries. will [See this also](https://python.meshtastic.org/mesh_interface.html#meshtastic.mesh_interface.MeshInterface.sendText) | No |
| want_response | boolean, <br>**Default:** true | `true` if you want the service on the other side to send an application layer response. [See this also](https://python.meshtastic.org/mesh_interface.html#meshtastic.mesh_interface.MeshInterface.sendText) | No |

#### NodeDirectPayload Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| regex_subst | [RegexSubst](#regexsubst-schema) or null |  | No |
| text | string | UTF-8 text to the mesh. This API limits it to 200 bytes for safety, although [the default Meshtastic MTU is 237 bytes](https://buf.build/meshtastic/protobufs/docs/86640f20db7b9b5be42949d18e8d96ad10d47a68%3Ameshtastic#meshtastic.Constants) | Yes |
| want_ack | boolean, <br>**Default:** true | `true` if you want the message sent in a reliable manner (with retries and ack/nak provided for delivery). Meshtastic's firmware will handle the retries. will [See this also](https://python.meshtastic.org/mesh_interface.html#meshtastic.mesh_interface.MeshInterface.sendText) | No |
| port_num | integer, <br>**Default:** 1 | Protobuf application port number | No |
| want_response | boolean | `true` if you want the service on the other side to send an application layer response. [See this also](https://python.meshtastic.org/mesh_interface.html#meshtastic.mesh_interface.MeshInterface.sendText) | No |

#### QueueErrorResponse Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| detail | string, <br>**Default:** Unable to handle more requests, queue full. |  | No |

#### RadioErrorResponse Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| detail | string, <br>**Default:** Meshtastic radio problem |  | No |

#### RegexSubst Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| pattern | string | A regex pattern to be matched against | No |
| subst | string | What to replace the regex pattern with | No |

#### ValidationError Schema

| Name | Type | Description | Required |
| ---- | ---- | ----------- | -------- |
| loc | [ string or integer ] |  | Yes |
| msg | string |  | Yes |
| type | string |  | Yes |
| input |  |  | No |
| ctx | object |  | No |

<!-- END_API_DOCS -->
