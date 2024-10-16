# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

import json
from typing import Iterator, List

from google.protobuf.message import Message

from ansys.speos.core import SpeosClient, protobuf_message_to_dict


def replace_guids(speos_client: SpeosClient, message: Message, ignore_simple_key: str = "") -> dict:
    json_dict = protobuf_message_to_dict(message=message)
    _replace_guid_elt(speos_client=speos_client, json_dict=json_dict, ignore_simple_key=ignore_simple_key)
    return json_dict


def dict_to_str(dict: dict) -> str:
    return json.dumps(dict, indent=4)


def _replace_guid_elt(speos_client: SpeosClient, json_dict: dict, ignore_simple_key: str = "") -> None:
    new_items = []
    for k, v in json_dict.items():
        if k.endswith("_guid") and v != "" and k != ignore_simple_key:
            new_v = protobuf_message_to_dict(message=speos_client.get_item(key=v).get())
            _replace_guid_elt(speos_client=speos_client, json_dict=new_v)
            new_items.append((k[: k.find("_guid")], new_v))
        elif k.endswith("_guids") and len(v) != 0:
            new_key_list = k[: k.find("_guid")] + "s"
            new_value_list = []
            for iv in v:
                new_v = protobuf_message_to_dict(message=speos_client.get_item(key=iv).get())
                _replace_guid_elt(speos_client=speos_client, json_dict=new_v)
                new_value_list.append(new_v)
            new_items.append((new_key_list, new_value_list))

        if type(v) == dict:
            _replace_guid_elt(speos_client=speos_client, json_dict=v)
        elif type(v) == list:
            for iv in v:
                if type(iv) == dict:
                    _replace_guid_elt(speos_client=speos_client, json_dict=iv)
    for new_k, new_v in new_items:
        json_dict[new_k] = new_v


class _ReplacePropsElt:
    def __init__(self) -> None:
        self.new_items = {}
        self.dict_to_complete = {}
        self.key_to_remove = ""
        self.dict_to_remove = {}


def _finder_by_key(dict_var: dict, key: str, x_path: str = "") -> List[tuple[str, dict]]:
    out_list = []
    for k, v in dict_var.items():
        if k == key:
            out_list.append((x_path + "." + k, v))
        elif isinstance(v, dict):
            x_path_bckp = x_path
            for x_path, vv in _finder_by_key(dict_var=v, key=key, x_path=x_path + "." + k):
                out_list.append((x_path, vv))
            x_path = x_path_bckp

        elif isinstance(v, list):
            x_path_bckp = x_path
            x_path += "." + k + "["
            i = 0
            for item in v:
                if isinstance(item, dict):
                    x_path_bckp2 = x_path
                    if "name" in item.keys():
                        x_path = x_path + ".name='" + item["name"] + "']"
                    else:
                        x_path = x_path + str(i) + "]"
                    for x_path, vv in _finder_by_key(dict_var=item, key=key, x_path=x_path):
                        out_list.append((x_path, vv))
                    x_path = x_path_bckp2
                i = i + 1
            x_path = x_path_bckp
    return out_list


def _value_finder_key_startswith(dict_var: dict, key: str) -> Iterator[tuple[str, dict]]:
    for k, v in dict_var.items():
        if k.startswith(key):
            yield (k, v)
        elif isinstance(v, dict):
            for kk, vv in _value_finder_key_startswith(dict_var=v, key=key):
                yield (kk, vv)


def _value_finder_key_endswith(dict_var: dict, key: str) -> Iterator[tuple[str, dict, dict]]:
    for k, v in dict_var.items():
        if k.endswith(key):
            yield (k, v, dict_var)

        if isinstance(v, dict):
            for kk, vv, parent in _value_finder_key_endswith(dict_var=v, key=key):
                yield (kk, vv, parent)


def replace_properties(json_dict: dict) -> None:
    replace_props_elts = []
    for k, v, parent in _value_finder_key_endswith(dict_var=json_dict, key="_properties"):
        replace_props_elt = _ReplacePropsElt()
        replace_props_elt.key_to_remove = k
        replace_props_elt.dict_to_remove = parent
        for kk, vv in _value_finder_key_startswith(dict_var=json_dict, key=k[: k.find("_properties")]):
            replace_props_elt.dict_to_complete = vv
            for kkk, vvv in v.items():
                if not kkk.endswith("_properties"):
                    replace_props_elt.new_items[kkk] = vvv
        replace_props_elts.append(replace_props_elt)

    for rpe in replace_props_elts:
        for k, v in rpe.new_items.items():
            rpe.dict_to_complete[k] = v
        if rpe.key_to_remove in rpe.dict_to_remove.keys():
            rpe.dict_to_remove.pop(rpe.key_to_remove)
