# Copyright (C) 2021 - 2025 ANSYS, Inc. and/or its affiliates.
# SPDX-License-Identifier: MIT
#
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Module with utility elements for protobuf messages from Speos RPC server."""

import json

from google.protobuf import __version__ as protobuf_version
from google.protobuf.json_format import MessageToJson
from google.protobuf.message import Message


def protobuf_message_to_str(message: Message, with_full_name: bool = True) -> str:
    """
    Convert a protobuf message to formatted json string.

    Parameters
    ----------
    message : google.protobuf.message.Message
        Protobuf message.
    with_full_name : bool
        Prepend the returned string with protobuf message full name.
        By default, ``True``.

    Returns
    -------
    str
        protobuf message formatted to be logged/printed.
    """
    ret = ""
    if with_full_name:
        ret += message.DESCRIPTOR.full_name + "\n"

    protobuf_major_version = int(protobuf_version.split(sep=".", maxsplit=1)[0])
    if protobuf_major_version < 5:
        ret += MessageToJson(
            message=message,
            including_default_value_fields=True,
            preserving_proto_field_name=True,
            indent=4,
            ensure_ascii=False,
        )
    else:
        ret += MessageToJson(
            message=message,
            always_print_fields_with_no_presence=True,
            preserving_proto_field_name=True,
            indent=4,
            ensure_ascii=False,
        )
    return ret


def protobuf_message_to_dict(message) -> dict:
    """Convert protobuf message to a formatted json dict.

    Parameters
    ----------
    message : google.protobuf.message.Message
        Protobuf message.

    Returns
    -------
    dict
        protobuf message formatted as dict.
    """
    return json.loads(protobuf_message_to_str(message=message, with_full_name=False))
