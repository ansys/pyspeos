# (c) 2023 ANSYS, Inc. Unauthorized use, distribution, or duplication is prohibited. ANSYS Confidential Information

import PySimpleGUI as sg
from google.protobuf.json_format import Parse

from ansys.speos.core.body import Body, BodyFactory, BodyLink, BodyStub
import ansys.speos.core.client as pys
from ansys.speos.core.crud import CrudItem, CrudStub
from ansys.speos.core.face import Face, FaceFactory, FaceLink, FaceStub
from ansys.speos.core.intensity_template import (
    IntensityTemplate,
    IntensityTemplateFactory,
    IntensityTemplateLink,
    IntensityTemplateStub,
)
from ansys.speos.core.job import Job, JobFactory, JobLink, JobStub
from ansys.speos.core.part import Part, PartFactory, PartLink, PartStub
from ansys.speos.core.proto_message_utils import protobuf_message_to_str
from ansys.speos.core.scene import Scene, SceneFactory, SceneLink, SceneStub
from ansys.speos.core.sensor_template import (
    SensorTemplate,
    SensorTemplateFactory,
    SensorTemplateLink,
    SensorTemplateStub,
)
from ansys.speos.core.simulation_template import (
    SimulationTemplate,
    SimulationTemplateFactory,
    SimulationTemplateLink,
    SimulationTemplateStub,
)
from ansys.speos.core.sop_template import (
    SOPTemplate,
    SOPTemplateFactory,
    SOPTemplateLink,
    SOPTemplateStub,
)
from ansys.speos.core.source_template import (
    SourceTemplate,
    SourceTemplateFactory,
    SourceTemplateLink,
    SourceTemplateStub,
)
from ansys.speos.core.spectrum import Spectrum, SpectrumFactory, SpectrumLink, SpectrumStub
from ansys.speos.core.vop_template import (
    VOPTemplate,
    VOPTemplateFactory,
    VOPTemplateLink,
    VOPTemplateStub,
)

# main speos client
speos_client = pys.SpeosClient(port="50051", timeout=5)

# list all available services
services_list = (
    "face",
    "body",
    "part",
    "sop_template",
    "vop_template",
    "spectrum",
    "intensity_template",
    "source_template",
    "sensor_template",
    "simulation_template",
    "scene",
    "job",
)
selected_service = None

# list all items
items_list = ()
selected_item = None


def get_service_selected(service) -> CrudStub:
    """Get service CRUD database"""
    if service == "face":
        return speos_client.faces()
    elif service == "body":
        return speos_client.bodies()
    elif service == "part":
        return speos_client.parts()
    elif service == "sop_template":
        return speos_client.sop_templates()
    elif service == "vop_template":
        return speos_client.vop_templates()
    elif service == "spectrum":
        return speos_client.spectrums()
    elif service == "intensity_template":
        return speos_client.intensity_templates()
    elif service == "source_template":
        return speos_client.source_templates()
    elif service == "sensor_template":
        return speos_client.sensor_templates()
    elif service == "simulation_template":
        return speos_client.simulation_templates()
    elif service == "scene":
        return speos_client.scenes()
    elif service == "job":
        return speos_client.jobs()
    return None


def get_item_selected(db, key) -> CrudItem:
    if isinstance(db, FaceStub):
        return FaceLink(db, key)
    elif isinstance(db, BodyStub):
        return BodyLink(db, key)
    elif isinstance(db, PartStub):
        return PartLink(db, key)
    elif isinstance(db, SOPTemplateStub):
        return SOPTemplateLink(db, key)
    elif isinstance(db, VOPTemplateStub):
        return VOPTemplateLink(db, key)
    elif isinstance(db, SpectrumStub):
        return SpectrumLink(db, key)
    elif isinstance(db, IntensityTemplateStub):
        return IntensityTemplateLink(db, key)
    elif isinstance(db, SourceTemplateStub):
        return SourceTemplateLink(db, key)
    elif isinstance(db, SensorTemplateStub):
        return SensorTemplateLink(db, key)
    elif isinstance(db, SimulationTemplateStub):
        return SimulationTemplateLink(db, key)
    elif isinstance(db, SceneStub):
        return SceneLink(db, key)
    elif isinstance(db, JobStub):
        return JobLink(db, key)
    return None


def list_items(service) -> list:
    """List all items in database"""
    if service == "face":
        return speos_client.faces().list()
    elif service == "body":
        return speos_client.bodies().list()
    elif service == "part":
        return speos_client.parts().list()
    elif service == "sop_template":
        return speos_client.sop_templates().list()
    elif service == "vop_template":
        return speos_client.vop_templates().list()
    elif service == "spectrum":
        return speos_client.spectrums().list()
    elif service == "intensity_template":
        return speos_client.intensity_templates().list()
    elif service == "source_template":
        return speos_client.source_templates().list()
    elif service == "sensor_template":
        return speos_client.sensor_templates().list()
    elif service == "simulation_template":
        return speos_client.simulation_templates().list()
    elif service == "scene":
        return speos_client.scenes().list()
    elif service == "job":
        return speos_client.jobs().list()
    return None


def update_item(json_content):
    try:
        if not selected_item:
            return ""

        content = None
        if isinstance(selected_item, FaceLink):
            content = Parse(json_content, Face())
        elif isinstance(selected_item, BodyLink):
            content = Parse(json_content, Body())
        elif isinstance(selected_item, PartLink):
            content = Parse(json_content, Part())
        elif isinstance(selected_item, SOPTemplateLink):
            content = Parse(json_content, SOPTemplate())
        elif isinstance(selected_item, VOPTemplateLink):
            content = Parse(json_content, VOPTemplate())
        elif isinstance(selected_item, SpectrumLink):
            content = Parse(json_content, Spectrum())
        elif isinstance(selected_item, IntensityTemplateLink):
            content = Parse(json_content, IntensityTemplate())
        elif isinstance(selected_item, SourceTemplateLink):
            content = Parse(json_content, SourceTemplate())
        elif isinstance(selected_item, SensorTemplateLink):
            content = Parse(json_content, SensorTemplate())
        elif isinstance(selected_item, SimulationTemplateLink):
            content = Parse(json_content, SimulationTemplate())
        elif isinstance(selected_item, SceneLink):
            content = Parse(json_content, Scene())
        elif isinstance(selected_item, JobLink):
            content = Parse(json_content, Job())

        if content:
            selected_item.set(content)
    except Exception as e:
        sg.popup_error(e)


def create_new_item(service) -> CrudItem:
    """Get service CRUD database"""
    if service == "face":
        return speos_client.faces().create(message=FaceFactory.rectangle("new", description="new"))
    elif service == "body":
        return speos_client.bodies().create(message=BodyFactory.box(name="new", description="new", face_stub=speos_client.faces()))
    elif service == "part":
        return speos_client.parts().create(
            message=PartFactory.new(
                name="new",
                description="new",
                bodies=[speos_client.bodies().create(message=BodyFactory.box(name="body_for_part", face_stub=speos_client.faces()))],
            )
        )
    elif service == "sop_template":
        return speos_client.sop_templates().create(message=SOPTemplateFactory.mirror(name="new", description="new", reflectance=100.0))
    elif service == "vop_template":
        return speos_client.vop_templates().create(
            message=VOPTemplateFactory.optic(name="new", description="new", index=1.5, absorption=0.0)
        )
    elif service == "spectrum":
        return speos_client.spectrums().create(message=SpectrumFactory.monochromatic(name="new", description="new", wavelength=486))
    elif service == "intensity_template":
        return speos_client.intensity_templates().create(
            message=IntensityTemplateFactory.lambertian(name="new", description="new", total_angle=180.0)
        )
    elif service == "source_template":
        return speos_client.source_templates().create(
            message=SourceTemplateFactory.surface(
                name="new",
                description="new",
                intensity_template=speos_client.intensity_templates().create(
                    message=IntensityTemplateFactory.symmetric_gaussian(
                        name="symmetric_gaussian",
                        description="symmetric gaussian intensity template for surfacic source template",
                        FWHM_angle=30.0,
                        total_angle=180.0,
                    )
                ),
                flux=SourceTemplateFactory.Flux(unit=SourceTemplateFactory.Flux.Unit.Lumen, value=683.0),
                spectrum=speos_client.spectrums().create(
                    message=SpectrumFactory.blackbody(
                        name="blackbody",
                        description="blackbody spectrum for surfacic source template",
                        temperature=2856.0,
                    )
                ),
            )
        )
    elif service == "sensor_template":
        return speos_client.sensor_templates().create(
            message=SensorTemplateFactory.irradiance(
                name="new",
                description="new",
                type=SensorTemplateFactory.Type.Photometric,
                illuminance_type=SensorTemplateFactory.IlluminanceType.Planar,
                dimensions=SensorTemplateFactory.Dimensions(
                    x_start=-50.0, x_end=50.0, x_sampling=100, y_start=-50.0, y_end=50.0, y_sampling=100
                ),
            )
        )
    elif service == "simulation_template":
        return speos_client.simulation_templates().create(message=SimulationTemplateFactory.direct_mc(name="new", description="new"))
    elif service == "scene":
        return speos_client.scenes().create(
            message=SceneFactory.new(
                name="new",
                description="new",
                part=create_new_item("part"),
                vop_instances=[SceneFactory.vop_instance(name="Optic.1", vop_template=create_new_item("vop_template"))],
                sop_instances=[SceneFactory.sop_instance(name="Mirror.1", sop_template=create_new_item("sop_template"))],
                source_instances=[
                    SceneFactory.source_instance(
                        name="Surface.1",
                        source_template=create_new_item("source_template"),
                        properties=SceneFactory.surface_source_props(exitance_constant_geo_paths={"body_for_part/Face:2": False}),
                    )
                ],
                sensor_instances=[
                    SceneFactory.sensor_instance(
                        name="Irradiance.1",
                        sensor_template=create_new_item("sensor_template"),
                        properties=SceneFactory.irradiance_sensor_props(),
                    )
                ],
                simulation_instances=[
                    SceneFactory.simulation_instance(name="Direct.1", simulation_template=create_new_item("simulation_template"))
                ],
            )
        )
    elif service == "job":
        return speos_client.jobs().create(
            message=JobFactory.new(
                name="new",
                description="new",
                scene=create_new_item("scene"),
                simulation_path="Direct.1",
                properties=JobFactory.direct_mc_props(),
            )
        )
    return None


def list_items_name(service) -> list:
    return list(map(lambda x: x.key, list_items(service)))


# get content of selected item
def item_content():
    """Get content of selected item"""
    if not selected_item:
        return ""
    return protobuf_message_to_str(selected_item.get(), with_full_name=False)


layout = [
    [
        [
            sg.Text("Server address:"),
            sg.Input("localhost:50051", font=("Consolas", 10), key="-SERVER-"),
            sg.Text("Database:"),
            sg.Combo(values=services_list, size=(None, 20), default_value="face", key="-SERVICES-"),
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
        item_inputtext.update(item_content())
    elif event == "New":
        # create new item
        selected_item = create_new_item(service_name)
        # Refresh item list
        items = list_items_name(service_name)
        items_list.update(values=items)
        items_list.update(set_to_index=len(items), scroll_to_index=len(items))
        # refresh item content
        item_inputtext.update(item_content())
    elif event == "Reload":
        # refresh item content
        item_inputtext.update(item_content())
    elif event == "Save":
        # update item
        update_item(values["-CONTENT-"])
        # refresh item content
        item_inputtext.update(item_content())

    elif event == "Delete":
        # remove item
        selected_item.delete()
        # Refresh item list
        items_list.update(values=list_items_name(service_name))
        item_inputtext.update("")

window.close()
