# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited. ANSYS Confidential Information

import PySimpleGUI as sg
from google.protobuf.json_format import MessageToJson, Parse

import ansys.speos.core.client as pys

# main speos client
speoscli = pys.SpeosClient()

# list all available services
services_list = ("spectrum", "...")
selected_service = None

# list all items
available_items = ()
selected_item = None


# get service CRUD database
def get_service_database(service):
    if service == "spectrum":
        return speoscli.get_spectrum_db()
    # ...
    return None


# get content of selected item
def get_item_content():
    return MessageToJson(get_service_database(selected_service).Read(selected_item), indent=4)


layout = [
    [
        [
            sg.Text("Server address:"),
            sg.Input("localhost:50051", font=("Consolas", 10), key="-SERVER-"),
            sg.Text("Database:"),
            sg.Combo(values=services_list, size=(None, 20), default_value="spectrum", key="-SERVICES-"),
            sg.Button("Refresh"),
        ]
    ],
    [
        [
            sg.Listbox(values=(), size=(30, 30), key="-ITEMS-", enable_events=True, auto_size_text=True),
            sg.Multiline("item content", size=(60, 32), key="-CONTENT-"),
        ]
    ],
    [sg.Button("New"), sg.Push(), sg.Button("Reload"), sg.Button("Save"), sg.Button("Delete")],
]

window = sg.Window("Pick a color", layout, finalize=True)
window.set_min_size((500, 250))
items_list = window["-ITEMS-"]
item_inputtext = window["-CONTENT-"]

while True:  # the event loop
    event, values = window.read()
    if event == sg.WIN_CLOSED:
        break
    elif event == "Refresh":
        # restart client
        serverstr = values["-SERVER-"].split(":")
        speoscli = pys.SpeosClient(host=serverstr[0], port=serverstr[1])
        # store item list
        selected_service = values["-SERVICES-"]
        available_items = get_service_database(selected_service).List()
        # Refresh item list
        items_list.update(values=available_items)
    elif event == "-ITEMS-":
        # store selected item
        selected_item = values["-ITEMS-"][0]
        # refresh item content
        item_inputtext.update(get_item_content())
    elif event == "New":
        # create new item
        selected_item = get_service_database(selected_service).NewBlackbody(5555).key()
        # update item list
        available_items = get_service_database(selected_service).List()
        # Refresh item list
        items_list.update(values=available_items)
        # refresh item content
        item_inputtext.update(get_item_content())
    elif event == "Reload":
        # refresh item content
        item_inputtext.update(get_item_content())
    elif event == "Save":
        # update item
        content = Parse(values["-CONTENT-"], get_service_database(selected_service).Content())
        get_service_database(selected_service).Update(selected_item, content)
        # refresh item content
        item_inputtext.update(get_item_content())
    elif event == "Delete":
        # remove item
        get_service_database(selected_service).Delete(selected_item)
        # refresh item list and context
        selected_item = ""
        available_items = get_service_database(selected_service).List()
        items_list.update(values=available_items)
        item_inputtext.update("")

window.close()
