from google.protobuf.json_format import MessageToJson
from google.protobuf.message import Message


def protobuf_message_to_str(message: Message) -> None:
    return (
        message.DESCRIPTOR.full_name
        + "\n"
        + MessageToJson(
            message=message, including_default_value_fields=True, preserving_proto_field_name=True, indent=4
        )
    )
