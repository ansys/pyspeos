# # How to create a Display source

# This tutorial demonstrates how to create a Display source in PySpeos.
#
# ## What is a Display source?
#
# A Display source simulates light emitted from display panels such as screens,
# monitors, or LED panels. It allows you to specify image content, dimensions,
# luminance, color space, and intensity distribution.
#
# ## Prerequisites
#
# ### Perform imports

# +
from pathlib import Path

from ansys.speos.core import Project, Speos, launcher
from ansys.speos.core.kernel.client import (
    default_docker_channel,
)
from ansys.speos.core.source import SourceDisplay

# -

# ### Define constants
# Constants help ensure consistency and avoid repetition throughout the example.

HOSTNAME = "localhost"
GRPC_PORT = 50098  # Be sure the Speos GRPC Server has been started on this port.
USE_DOCKER = True  # Set to False if you're running this example locally as a Notebook.

# ## Model Setup
#
# ### Load assets (optional)
# If you want to use a specific image file for your display source,
# make sure you have the image available.

if USE_DOCKER:  # Running on the remote server.
    assets_data_path = Path("/app") / "assets"
else:
    assets_data_path = Path("/path/to/your/download/assets/directory")

# ### Connect to the RPC Server
# This Python client connects to a server where the Speos engine
# is running as a service. In this example, the server and
# client are the same machine. The launch_local_speos_rpc_method can
# be used to start a local instance of the service.

if USE_DOCKER:
    speos = Speos(channel=default_docker_channel())
else:
    speos = launcher.launch_local_speos_rpc_server(port=GRPC_PORT)

# ### Create a new project
#
# The only way to create a Display source using the core layer is to create it from a project.
# The ``Project`` class is instantiated by passing a ``Speos`` instance

p = Project(speos=speos)
print(p)


# ## Display Source Creation
#
# ### Create with default values
#
# By default, a Display source is created with:
# - Luminous flux: 100 cd/m²
# - Dimensions: 100mm x 100mm (0 to 100 in X and Y)
# - Color space: sRGB
# - Lambertian intensity distribution
# - Position: Origin with identity orientation

display1 = SourceDisplay(project=p, name="Display.1")
print("Display source with defaults:")
print(display1)

# ### Commit to server
#
# After creating locally, commit the source to push it to the RPC server.

display1.commit()
print("\nAfter commit:")
print(display1)

# ## Configure Display Source Properties
#
# ### Set image file
#
# Specify an image file that will be displayed on the source.
# Supported formats: PNG, JPEG, BMP, TIFF, RGB

# Uncomment if you have an image file:
# image_path = str(assets_data_path / "display_image.png")
# display1.set_image_file_uri(uri=image_path)

# ### Set source dimensions
#
# Define the physical size of the display in millimeters.

display1.set_source_dimensions(
    x_start=0.0,  # Start position in X (mm)
    x_end=200.0,  # End position in X (mm)
    y_start=0.0,  # Start position in Y (mm)
    y_end=150.0,  # End position in Y (mm)
)

# ### Set luminous flux (luminance)
#
# Specify the luminance in cd/m².

display1.set_luminous_flux(value=250.0)

# ### Set contrast ratio (optional)
#
# Define the contrast ratio of the display. If not set, it's considered infinite.

display1.set_contrast_ratio(value=1000)

# To set it back to infinite:
# display1.clear_contrast_ratio()

# ### Set position and orientation
#
# Position the display in 3D space using an axis system.
# Format: [Origin_x, Origin_y, Origin_z, X_dir_x, X_dir_y, X_dir_z,
#          Y_dir_x, Y_dir_y, Y_dir_z, Z_dir_x, Z_dir_y, Z_dir_z]

display1.set_axis_system(axis_system=[100, 50, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1])

# Commit all changes
display1.commit()
print("\nDisplay source after configuration:")
print(display1)

# ## Color Space Configuration
#
# ### Predefined color spaces
#
# Create a second display with Adobe RGB color space

display2 = SourceDisplay(project=p, name="Display.AdobeRGB")
display2.set_color_space_adobe_rgb()
display2.commit()
print("\nDisplay with Adobe RGB:")
print(display2)

# ### Custom color space
#
# Create a display with custom RGB color space by specifying chromaticity coordinates

display3 = SourceDisplay(project=p, name="Display.Custom")
display3.set_custom_color_space(
    red_x=0.64,  # Red chromaticity x
    red_y=0.33,  # Red chromaticity y
    green_x=0.30,  # Green chromaticity x
    green_y=0.60,  # Green chromaticity y
    blue_x=0.15,  # Blue chromaticity x
    blue_y=0.06,  # Blue chromaticity y
    white_x=0.3127,  # White point x (D65)
    white_y=0.3290,  # White point y (D65)
)
display3.commit()
print("\nDisplay with custom color space:")
print(display3)

# ## Intensity Distribution
#
# Configure the angular distribution of light emitted from the display.
#
# ### Lambertian (cosine) distribution

display4 = SourceDisplay(project=p, name="Display.Lambertian")
display4.set_intensity().set_lambertian(exponent=1.0)  # Standard Lambertian
display4.commit()

# ### Custom intensity with higher exponent

display5 = SourceDisplay(project=p, name="Display.Directional")
display5.set_intensity().set_lambertian(exponent=3.0)  # More directional
display5.commit()

# ## Advanced Example: Complete Display Configuration

display_advanced = SourceDisplay(project=p, name="Display.Advanced", default_values=False)

# Configure all properties
display_advanced.set_source_dimensions(x_start=-100.0, x_end=100.0, y_start=-75.0, y_end=75.0)
display_advanced.set_luminous_flux(value=300.0)
display_advanced.set_contrast_ratio(value=2000)
display_advanced.set_color_space_srgb()
display_advanced.set_axis_system(axis_system=[0, 0, 100, 1, 0, 0, 0, 0, -1, 0, 1, 0])
display_advanced.set_intensity().set_lambertian(exponent=2.0)

display_advanced.commit()
print("\nAdvanced display configuration:")
print(display_advanced)

# ## Project Summary
#
# View all sources in the project

print("\nProject summary:")
print(p)

# ## Modifying Existing Display Source
#
# ### Reset to server state
#
# If you made local changes and want to revert to the last committed state:

display1.set_luminous_flux(value=500.0)  # Make a local change
print(f"\nLocal luminous flux: {display1._source_template.display.luminous_flux}")

display1.reset()  # Reset to server state
print(f"After reset: {display1._source_template.display.luminous_flux}")

# ### Update and commit changes

display1.set_luminous_flux(value=350.0)
display1.set_axis_system(axis_system=[200, 100, 50, 1, 0, 0, 0, 1, 0, 0, 0, 1])
display1.commit()
print("\nDisplay after update:")
print(display1)

# ## Cleanup
#
# ### Delete a source
#
# Remove a source from the server (local data remains available)

# display3.delete()
# print("\nAfter deleting Display.Custom:")
# print(p)

# ## Tips and Best Practices
#
# 1. **Image resolution**: Use appropriate resolution images for your display size
# 2. **Color space**: Choose sRGB for standard displays, Adobe RGB for wide-gamut displays
# 3. **Luminance values**: Typical display luminance ranges from 100-500 cd/m²
# 4. **Contrast ratio**: Modern displays typically have contrast ratios of 1000:1 to 5000:1
# 5. **Intensity distribution**: Lambertian (exponent=1) is typical for most displays
# 6. **Position**: Use set_axis_system to position the display correctly in your scene

print("\n✓ Display source tutorial completed successfully!")
