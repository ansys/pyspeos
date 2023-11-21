# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited. ANSYS Confidential Information

import PySimpleGUI as sg
from google.protobuf.json_format import MessageToJson, Parse

import ansys.speos.core.client as pys
from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.sensor_template import SensorTemplate, SensorTemplateLink, SensorTemplateStub
from ansys.speos.core.spectrum import Spectrum, SpectrumLink, SpectrumStub

# main speos client
speos_client = pys.SpeosClient(port="50051", timeout=5)

# list all available services
services_list = ("spectrum", "sensor_template", "...")
selected_service = None

# list all items
items_list = ()
selected_item = None


def get_service_selected(service) -> CrudStub:
    """Get service CRUD database"""
    if service == "spectrum":
        return speos_client.spectrums()
    elif service == "sensor_template":
        return speos_client.sensor_templates()
    # ...
    return None


def get_item_selected(db, key) -> CrudItem:
    if isinstance(db, SpectrumStub):
        return SpectrumLink(db, key)
    elif isinstance(db, SensorTemplateStub):
        return SensorTemplateLink(db, key)
    # ...
    return None


def list_items(service) -> list:
    """List all items in database"""
    if service == "spectrum":
        return speos_client.spectrums().List()
    elif service == "sensor_template":
        return speos_client.sensor_templates().List()
    # ...
    return None


def update_item(json_content):
    try:
        if not selected_item:
            return ""

        content = None
        if isinstance(selected_item, SpectrumLink):
            content = Parse(json_content, Spectrum())
        elif isinstance(selected_item, SensorTemplateLink):
            content = Parse(json_content, SensorTemplate())

        if content:
            selected_item.set(content)
    except Exception as e:
        sg.popup_error(e)


def create_new_item(service) -> CrudItem:
    """Get service CRUD database"""
    if service == "spectrum":
        sp = Spectrum()
        sp.name = "new"
        sp.description = "new"
        sp.monochromatic.wavelength = 486
        return speos_client.spectrums().Create(sp)
    elif service == "sensor_template":
        ssr = SensorTemplate()
        ssr.name = "new"
        ssr.description = "new"
        ssr.irradiance_sensor_template.sensor_type_photometric.SetInParent()
        ssr.irradiance_sensor_template.illuminance_type_planar.SetInParent()
        ssr.irradiance_sensor_template.dimensions.x_start = -50.0
        ssr.irradiance_sensor_template.dimensions.x_end = 50.0
        ssr.irradiance_sensor_template.dimensions.x_sampling = 100
        ssr.irradiance_sensor_template.dimensions.y_start = -50.0
        ssr.irradiance_sensor_template.dimensions.y_end = 50.0
        ssr.irradiance_sensor_template.dimensions.y_sampling = 100
        return speos_client.sensor_templates().Create(ssr)
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
        item_inputtext.update("item content")
    elif event == "-ITEMS-":
        # store selected item
        selected_key = values["-ITEMS-"]
        if selected_key:
            selected_key = selected_key[0]
        # refresh item content
        selected_service = get_service_selected(service_name)
        selected_item = get_item_selected(selected_service, selected_key)
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
        update_item(values["-CONTENT-"])
        # refresh item content
        item_inputtext.update(item_content(service_name))

    elif event == "Delete":
        # remove item
        selected_item.delete()
        # Refresh item list
        items_list.update(values=list_items_name(service_name))
        item_inputtext.update("")

window.close()
