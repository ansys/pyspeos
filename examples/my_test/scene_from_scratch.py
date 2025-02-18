from geom_utils import create_box
import numpy

from ansys.speos.core import GeoRef, Project, Speos
from ansys.speos.core.sensor import Irradiance, Radiance
from ansys.speos.core.simulation import Direct, Inverse
from ansys.speos.core.source import Surface

# ## Create connection with speos rpc server
speos = Speos(host="localhost", port=50098)

# ## New Project

# The only way to create an optical property, is to create it from a project.
p = Project(speos=speos)

root_part = p.create_root_part().commit()

body1 = root_part.create_body(name="TheBodyB1").commit()
body2 = root_part.create_body(name="TheBodyB2").commit()
body3 = root_part.create_body(name="TheBodyB3").commit()
body4 = root_part.create_body(name="TheBodyB4").commit()
gp_box1 = create_box(
    body1, base_axis_sytem=[0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1], x_size=100, y_size=100, z_size=100
)
gp_box2 = create_box(
    body2,
    base_axis_sytem=[500, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
    x_size=100,
    y_size=100,
    z_size=100,
)
gp_box3 = create_box(
    body3,
    base_axis_sytem=[-500, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
    x_size=100,
    y_size=100,
    z_size=100,
)
gp_box4 = create_box(
    body4,
    base_axis_sytem=[0, 500, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
    x_size=100,
    y_size=100,
    z_size=100,
)
print(root_part)

# p.preview()

# Materials
mat1 = p.create_optical_property("Material.1")
mat1.set_surface_mirror(reflectance=100).set_volume_opaque().set_geometries(
    geometries=[gp_box1[0], gp_box2[0]]
).commit()
mat2 = p.create_optical_property("Material.2")
mat2.set_surface_mirror(reflectance=100).set_volume_opaque().set_geometries(
    geometries=[gp_box3[0], gp_box4[0]]
).commit()

# Sources
source1 = p.create_source(name="Surface.1", feature_type=Surface)
source1.set_flux_radiant(value=1000.0).set_intensity().set_cos(N=1)
source1.set_spectrum().set_monochromatic(wavelength=400)
source1.set_exitance_constant(geometries=[(gp_box1[0], False)]).commit()

source2 = p.create_source(name="Surface.2", feature_type=Surface)
source2.set_flux_radiant(value=1000.0).set_intensity().set_cos(N=1)
source2.set_spectrum().set_monochromatic(wavelength=500)
source2.set_exitance_constant(geometries=[(gp_box2[0], False)]).commit()

source3 = p.create_source(name="Surface.3", feature_type=Surface)
source3.set_flux_radiant(value=1000.0).set_intensity().set_cos(N=1)
source3.set_spectrum().set_monochromatic(wavelength=600)
source3.set_exitance_constant(geometries=[(gp_box3[0], False)]).commit()

source4 = p.create_source(name="Surface.4", feature_type=Surface)
source4.set_flux_radiant(value=1000.0).set_intensity().set_cos(N=1)
source4.set_spectrum().set_monochromatic(wavelength=680)
source4.set_exitance_constant(geometries=[(gp_box4[0], False)]).commit()
source4.set_flux_radiant(value=1000.0).set_intensity()

# Sensors
sensor_r = p.create_sensor(name="Radiance1", feature_type=Radiance)
sensor_r.set_dimensions().set_x_start(-500).set_x_end(500).set_y_start(-500).set_y_end(
    500
).set_x_sampling(300).set_y_sampling(300)
sensor_r.set_type_colorimetric()
sensor_r.set_layer_type_source()
# Sensor orientation
main_dir = numpy.array([0, 0, 1])
main_dir = main_dir / numpy.linalg.norm(main_dir)
sensor_x_axis = numpy.array([1, 0, 0])
sensor_y_axis = numpy.cross(main_dir, sensor_x_axis)
sensor_axis_system_position = [0, 0, 800]
sensor_r.set_axis_system(
    numpy.concatenate((sensor_axis_system_position, sensor_x_axis, sensor_y_axis, main_dir))
)
sensor_r.set_focal(500.0).commit()

sensor_r2 = p.create_sensor(name="Radiance2", feature_type=Radiance)
sensor_r2.set_dimensions().set_x_start(-500).set_x_end(500).set_y_start(-500).set_y_end(
    500
).set_x_sampling(300).set_y_sampling(300)
sensor_r2.set_type_colorimetric()
sensor_r2.set_layer_type_source()
# Sensor orientation
main_dir = numpy.array([0, -0.5, 0.8])
main_dir = main_dir / numpy.linalg.norm(main_dir)
sensor_x_axis = numpy.array([1, 0, 0])
sensor_y_axis = numpy.cross(main_dir, sensor_x_axis)
sensor_axis_system_position = [0, -500, 800]
sensor_r2.set_axis_system(
    numpy.concatenate((sensor_axis_system_position, sensor_x_axis, sensor_y_axis, main_dir))
)
sensor_r2.set_focal(700.0).commit()
# p.preview()

# Simulation
simu_dir = p.create_simulation(name="SimuDir1", feature_type=Direct)
simu_dir.set_sensor_paths(["Radiance1", "Radiance2"])
simu_dir.set_source_paths(["Surface.1", "Surface.2", "Surface.3", "Surface.4"])
simu_dir.set_stop_condition_duration(value=10).commit()
results = simu_dir.compute_CPU()
print(str(results))


source1.set_spectrum().set_blackbody(3500).commit()
source2.set_spectrum().set_blackbody(5000).commit()
source3.set_spectrum().set_blackbody(7000).commit()
source4.set_spectrum().set_blackbody(10000).commit()
simu_inv = p.create_simulation(name="SimuInv1", feature_type=Inverse)
simu_inv.set_sensor_paths(["Radiance1", "Radiance2"])
simu_inv.set_source_paths(["Surface.1", "Surface.2", "Surface.3", "Surface.4"])
simu_inv.set_stop_condition_duration(value=10).commit()
results = simu_inv.compute_CPU()
print(str(results))
