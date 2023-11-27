# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited. ANSYS Confidential Information

import PySimpleGUI as sg
from google.protobuf.json_format import MessageToJson, Parse

import ansys.speos.core.client as pys
from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.intensity_template import (
    IntensityTemplate,
    IntensityTemplateHelper,
    IntensityTemplateLink,
    IntensityTemplateStub,
)
from ansys.speos.core.sensor_template import (
    SensorTemplate,
    SensorTemplateHelper,
    SensorTemplateLink,
    SensorTemplateStub,
)
from ansys.speos.core.source_template import (
    SourceTemplate,
    SourceTemplateHelper,
    SourceTemplateLink,
    SourceTemplateStub,
)
from ansys.speos.core.spectrum import Spectrum, SpectrumHelper, SpectrumLink, SpectrumStub

# main speos client
speos_client = pys.SpeosClient(port="50051", timeout=5)

# list all available services
services_list = ("spectrum", "intensity_template", "source_template", "sensor_template", "...")
selected_service = None

# list all items
items_list = ()
selected_item = None


def get_service_selected(service) -> CrudStub:
    """Get service CRUD database"""
    if service == "spectrum":
        return speos_client.spectrums()
    elif service == "intensity_template":
        return speos_client.intensity_templates()
    elif service == "source_template":
        return speos_client.source_templates()
    elif service == "sensor_template":
        return speos_client.sensor_templates()
    # ...
    return None


def get_item_selected(db, key) -> CrudItem:
    if isinstance(db, SpectrumStub):
        return SpectrumLink(db, key)
    elif isinstance(db, IntensityTemplateStub):
        return IntensityTemplateLink(db, key)
    elif isinstance(db, SourceTemplateStub):
        return SourceTemplateLink(db, key)
    elif isinstance(db, SensorTemplateStub):
        return SensorTemplateLink(db, key)
    # ...
    return None


def list_items(service) -> list:
    """List all items in database"""
    if service == "spectrum":
        return speos_client.spectrums().list()
    elif service == "intensity_template":
        return speos_client.intensity_templates().list()
    elif service == "source_template":
        return speos_client.source_templates().list()
    elif service == "sensor_template":
        return speos_client.sensor_templates().list()
    # ...
    return None


def update_item(json_content):
    try:
        if not selected_item:
            return ""

        content = None
        if isinstance(selected_item, SpectrumLink):
            content = Parse(json_content, Spectrum())
        elif isinstance(selected_item, IntensityTemplateLink):
            content = Parse(json_content, IntensityTemplate())
        elif isinstance(selected_item, SourceTemplateLink):
            content = Parse(json_content, SourceTemplate())
        elif isinstance(selected_item, SensorTemplateLink):
            content = Parse(json_content, SensorTemplate())

        if content:
            selected_item.set(content)
    except Exception as e:
        sg.popup_error(e)


def create_new_item(service) -> CrudItem:
    """Get service CRUD database"""
    if service == "spectrum":
        return SpectrumHelper.create_monochromatic(
            spectrum_stub=speos_client.spectrums(), name="new", description="new", wavelength=486
        )
    elif service == "intensity_template":
        return IntensityTemplateHelper.create_lambertian(
            intensity_template_stub=speos_client.intensity_templates(), name="new", description="new", total_angle=180.0
        )
    elif service == "source_template":
        return SourceTemplateHelper.create_surface(
            source_template_stub=speos_client.source_templates(),
            name="new",
            description="new",
            intensity_template=IntensityTemplateHelper.create_symmetric_gaussian(
                intensity_template_stub=speos_client.intensity_templates(),
                name="symmetric_gaussian",
                description="symmetruc gaussian intensity template for surfacic source template",
                FWHM_angle=30.0,
                total_angle=180.0,
            ),
            flux=SourceTemplateHelper.Flux(unit=SourceTemplateHelper.Flux.Unit.Lumen, value=683.0),
            spectrum=SpectrumHelper.create_blackbody(
                spectrum_stub=speos_client.spectrums(),
                name="blackbody",
                description="blackbody spectrum for surfacic source template",
                temperature=2856.0,
            ),
        )
    elif service == "sensor_template":
        return SensorTemplateHelper.create_irradiance(
            sensor_template_stub=speos_client.sensor_templates(),
            name="new",
            description="new",
            type=SensorTemplateHelper.Type.Photometric,
            illuminance_type=SensorTemplateHelper.IlluminanceType.Planar,
            dimensions=SensorTemplateHelper.Dimensions(
                x_start=-50.0, x_end=50.0, x_sampling=100, y_start=-50.0, y_end=50.0, y_sampling=100
            ),
        )
    # ...
    return None


def list_items_name(service) -> list:
    return list(map(lambda x: x.key, list_items(service)))


# get content of selected item
def item_content(service):
    """Get content of selected item"""
    if not selected_item:
        return ""
    return MessageToJson(
        selected_item.get(), indent=4, including_default_value_fields=True, preserving_proto_field_name=True
    )


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
