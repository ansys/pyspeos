# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited. ANSYS Confidential Information

import PySimpleGUI as sg
from google.protobuf.json_format import MessageToJson, Parse

import ansys.speos.core.client as pys
from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.spectrum import Spectrum, SpectrumLink

# main speos client
speos_client = pys.SpeosClient(timeout=5)

# list all available services
services_list = ("spectrum", "...")
selected_service = None

# list all items
items_list = ()
selected_item = None


def get_service_selected(service) -> CrudStub:
    """Get service CRUD database"""
    if service == "spectrum":
        return speos_client.spectrums()
    # ...
    return None


def list_items(service) -> list:
    """List all items in database"""
    if service == "spectrum":
        return speos_client.spectrums().List()
    # ...
    return None


def create_new_item(service) -> CrudItem:
    """Get service CRUD database"""
    if service == "spectrum":
        sp = Spectrum()
        sp.name = "new"
        sp.description = "new"
        sp.monochromatic.wavelength = 486
        return speos_client.spectrums().Create(sp)
    # ...
    return None


def list_items_name(service) -> list:
    return list(map(lambda x: x.key, list_items(service)))


# get content of selected item
def item_content(service):
    """Get content of selected item"""
    if not selected_item:
        return ""
    return MessageToJson(selected_item.get(), indent=4)


layout = [
    [
        [
            sg.Text("Server address:"),
            sg.Input("localhost:50051", font=("Consolas", 10), key="-SERVER-"),
            sg.Text("Database:"),
            sg.Combo(values=services_list, size=(None, 20), default_value="spectrum", key="-SERVICES-"),
            sg.Button("Refresh"),
            sg.Push(),
        ]
    ],
    [
        [
            sg.Listbox(values=(), size=(30, 30), key="-ITEMS-", enable_events=True, auto_size_text=True),
            sg.Multiline("item content", size=(60, 32), key="-CONTENT-"),
        ]
    ],
    [[sg.Button("New"), sg.Push(), sg.Button("Reload"), sg.Button("Save"), sg.Button("Delete")]],
]

window = sg.Window("PySpeos Database viewer", layout, finalize=True, resizable=True)
window.set_min_size((500, 250))
items_list = window["-ITEMS-"]
item_inputtext = window["-CONTENT-"]

while True:  # the event loop
    event, values = window.read()
    if values and "-SERVICES-" in values.keys():
        service_name = values["-SERVICES-"]
    if event == sg.WIN_CLOSED:
        break
    elif event == "Refresh":
        # restart client
        serverstr = values["-SERVER-"].split(":")
        speos_client = pys.SpeosClient(host=serverstr[0], port=serverstr[1], timeout=5)
        # Refresh item list
        items_list.update(values=list_items_name(service_name))
    elif event == "-ITEMS-":
        # store selected item
        selected_key = values["-ITEMS-"]
        if selected_key:
            selected_key = selected_key[0]
        # refresh item content
        selected_service = get_service_selected(service_name)
        selected_item = SpectrumLink(selected_service, selected_key)
        item_inputtext.update(item_content(service_name))
    elif event == "New":
        # create new item
        selected_item = create_new_item(service_name)
        # Refresh item list
        items = list_items_name(service_name)
        items_list.update(values=items)
        items_list.update(set_to_index=len(items), scroll_to_index=len(items))
        # refresh item content
        item_inputtext.update(item_content(service_name))
    elif event == "Reload":
        # refresh item content
        item_inputtext.update(item_content(service_name))
    elif event == "Save":
        # update item
        try:
            content = Parse(values["-CONTENT-"], Spectrum())
            selected_item.set(content)
            # refresh item content
            item_inputtext.update(item_content(service_name))
        except Exception as e:
            sg.popup_error(e)

    elif event == "Delete":
        # remove item
        selected_item.delete()
        # Refresh item list
        items_list.update(values=list_items_name(service_name))
        item_inputtext.update("")

window.close()
