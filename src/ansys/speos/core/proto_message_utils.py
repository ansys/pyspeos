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

"""Module with method to process Protobuf messages."""

import json
from typing import Iterator, List

from google.protobuf.message import Message

from ansys.speos.core.kernel import SpeosClient, protobuf_message_to_dict


def dict_to_str(dict: dict) -> str:
    """Transform a dictionary into a string.

    Parameters
    ----------
    dict
        Dictionary to transform.

    Returns
    -------
    str
        String representation of the dictionary.
    """
    return json.dumps(dict, indent=4, ensure_ascii=False)


def _replace_guids(
    speos_client: SpeosClient, message: Message, ignore_simple_key: str = ""
) -> dict:
    # Transform protobuf message into dictionary
    json_dict = protobuf_message_to_dict(message=message)
    # Add for each element xxx_guid a key xxx with value the corresponding data from database
    _replace_guid_elt(
        speos_client=speos_client,
        json_dict=json_dict,
        ignore_simple_key=ignore_simple_key,
    )
    return json_dict


def _replace_guid_elt(
    speos_client: SpeosClient, json_dict: dict, ignore_simple_key: str = ""
) -> None:
    new_items = []
    for k, v in json_dict.items():
        # If we are in the case of key "xxx_guid", with a guid non empty
        # and that the key is not to ignore
        if k.endswith("_guid") and v != "" and k != ignore_simple_key:
            # Retrieve the item from db and transform it to dictionary
            new_v = protobuf_message_to_dict(message=speos_client[v].get())

            # This item can potentially have some "xxx_guid" fields to replace
            _replace_guid_elt(
                speos_client=speos_client,
                json_dict=new_v,
                ignore_simple_key=ignore_simple_key,
            )
            # Add the new value under "xxx" key
            new_items.append((k[: k.find("_guid")], new_v))
        # Possibility to have a list of guids : "xxx_guids"
        elif k.endswith("_guids") and len(v) != 0:
            # then a new list of values will be added under "xxxs" key
            new_key_list = k[: k.find("_guid")] + "s"
            new_value_list = []
            for iv in v:
                # Retrieve the item from db and transform it to dictionary
                new_v = protobuf_message_to_dict(message=speos_client[iv].get())

                # This item can potentially have some "xxx_guid" fields to replace
                _replace_guid_elt(
                    speos_client=speos_client,
                    json_dict=new_v,
                    ignore_simple_key=ignore_simple_key,
                )
                # Add the new value to the "xxxs" list
                new_value_list.append(new_v)
            new_items.append((new_key_list, new_value_list))

        # Call recursevely if the value is a dict or a list with dict as items values
        if isinstance(v, dict):
            _replace_guid_elt(
                speos_client=speos_client,
                json_dict=v,
                ignore_simple_key=ignore_simple_key,
            )
        elif isinstance(v, list):
            for iv in v:
                if isinstance(iv, dict):
                    _replace_guid_elt(
                        speos_client=speos_client,
                        json_dict=iv,
                        ignore_simple_key=ignore_simple_key,
                    )

    # To avoid modifying a dict when reading it, all changes were stored in new_items list
    # They are applied now
    for new_k, new_v in new_items:
        json_dict[new_k] = new_v


class _ReplacePropsElt:
    """Class to help replacing properties element."""

    def __init__(self) -> None:
        self.new_items = {}
        self.dict_to_complete = {}
        self.key_to_remove = ""
        self.dict_to_remove = {}


def _value_finder_key_startswith(dict_var: dict, key: str) -> Iterator[tuple[str, dict]]:
    """Find all (key,value) corresponding to a key that starts with input key."""
    for k, v in dict_var.items():
        if k.startswith(key):  # if the key fits the condition
            yield (k, v)

        if isinstance(v, dict):  # Look recursively if the value is a dict
            for kk, vv in _value_finder_key_startswith(dict_var=v, key=key):
                yield (kk, vv)


def _value_finder_key_endswith(dict_var: dict, key: str) -> Iterator[tuple[str, dict, dict]]:
    """Find all (key,value,parent dict) corresponding to a key that ends with input key."""
    for k, v in dict_var.items():
        if k.endswith(key):  # if the key fits the condition
            yield (k, v, dict_var)

        if isinstance(v, dict):  # Look recursively if the value is a dict
            for kk, vv, parent in _value_finder_key_endswith(dict_var=v, key=key):
                yield (kk, vv, parent)


def _replace_properties(json_dict: dict) -> None:
    """Replace every "xxx_properties" values to the place where the "xxx" value is defined."""
    replace_props_elts = []
    # Look for the "xxx_properties" elements
    for k, v, parent in _value_finder_key_endswith(dict_var=json_dict, key="_properties"):
        replace_props_elt = _ReplacePropsElt()
        replace_props_elt.key_to_remove = (
            k  # We will later remove this key, as its value were moved to correct place
        )
        replace_props_elt.dict_to_remove = (
            parent  # Remember the parent to be able to remove the key
        )

        # Look for the corresponding xxx item that we will complete with properties values
        for kk, vv in _value_finder_key_startswith(
            dict_var=json_dict, key=k[: k.find("_properties")]
        ):
            if kk != k and type(vv) is dict:
                replace_props_elt.dict_to_complete = (
                    vv  # Remember the dictionary to complete with properties
                )
                for kkk, vvv in v.items():
                    if not kkk.endswith("_properties"):
                        replace_props_elt.new_items[kkk] = vvv  # Store every property key, value

        # Replace only if dict_to_complete and new_items are not empty
        if len(replace_props_elt.dict_to_complete) != 0 or len(replace_props_elt.new_items) != 0:
            replace_props_elts.append(replace_props_elt)

    # To avoid modifying dictionary while parsing it, modifications are done now
    for rpe in replace_props_elts:
        # Complete by adding key values
        for k, v in rpe.new_items.items():
            rpe.dict_to_complete[k] = v
        # Remove the key "xxx_properties" that is useless now
        if rpe.key_to_remove in rpe.dict_to_remove.keys():
            rpe.dict_to_remove.pop(rpe.key_to_remove)


def _finder_by_key(dict_var: dict, key: str, x_path: str = "") -> List[tuple[str, dict]]:
    """Find a key in a dictionary (recursively).

    It will return a list of (x_path, dictionary) of items corresponding to the key.
    """
    out_list = []

    # Loop on all dictionary items
    for k, v in dict_var.items():
        if k == key:  # If directly found, append to the out_list
            out_list.append(
                (x_path + "." + k, v)
            )  # x_path contains ".key" to be able to identify where to find the value returned
        elif isinstance(v, dict):
            # In case of a dictionary value, then call recursively _finder_by_key to check its keys
            x_path_bckp = x_path
            for x_path, vv in _finder_by_key(dict_var=v, key=key, x_path=x_path + "." + k):
                out_list.append((x_path, vv))
            x_path = x_path_bckp  # retrieve previous x_path

        elif isinstance(v, list):
            # In case of list, will loop on each list item to look for whished key
            x_path_bckp = x_path
            x_path += (
                "." + k + "["
            )  # x_path contains .key[idx] to be able to identify where to find the value returned
            i = 0
            for item in v:
                if isinstance(item, dict):
                    x_path_bckp2 = x_path
                    # In case the dict has field name, use it in x_path like .key[.name='TheName']
                    # it is more meaningful that just [idx]
                    if "name" in item.keys():
                        x_path = x_path + ".name='" + item["name"] + "']"
                    else:  # if no field name, then just use .key[idx]
                        x_path = x_path + str(i) + "]"

                    # Call recursively _finder_by_key to check items keys
                    for x_path, vv in _finder_by_key(dict_var=item, key=key, x_path=x_path):
                        out_list.append((x_path, vv))
                    x_path = x_path_bckp2  # retrieve previous x_path
                i = i + 1
            x_path = x_path_bckp  # retrieve previous x_path
    return out_list


def _flatten_dict(dict_var: dict):
    """Flatten a dictionary (recursively).

    It will return a dictionary of (key, value) of items corresponding to the key.
    If a same key appears multiple time, the last value will be used as the value.

    Parameters
    ----------
    dict_var: dict

    Returns
    -------
    dict

    """
    flat_dict = {}
    for k, v in dict_var.items():
        if isinstance(v, dict):
            flat_dict.update(_flatten_dict(v))
        flat_dict[k] = v
    return flat_dict
