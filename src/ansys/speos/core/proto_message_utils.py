from typing import Optional

from google.protobuf.json_format import MessageToJson
from google.protobuf.message import Message


def protobuf_message_to_str(message: Message, with_full_name: Optional[bool] = True) -> str:
    """
    Returns a protobuf message as formatted json string.

    Parameters
    ----------
    message : Message
        Protobuf message.
    with_full_name : bool, optional
        Prepend the returned string with protobuf message full name.

    Returns
    -------
    str
        protobuf message formatted to be logged/printed.
    """
    ret = ""
    if with_full_name:
        ret += message.DESCRIPTOR.full_name + "\n"
    ret += MessageToJson(message=message, including_default_value_fields=True, preserving_proto_field_name=True, indent=4)
    return ret
