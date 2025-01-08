# # How to create an intensity

# This tutorial demonstrates how to create an intensity property in script layer.

## What is intensity?

# Intensity is used to define the source direction in the space.

# +
import os

import ansys.speos.core as core
import ansys.speos.script as script

tests_data_path = os.path.join("/app", "assets")
# -

# Create connection with speos rpc server
# +
speos = core.Speos(host="localhost", port=50098)
# -

# ## Create
# Create locally
# The mention "local: " is added when printing the intensity
# +
intensity1 = script.Intensity(speos_client=speos.client, name="Intensity.1").set_cos(N=1, total_angle=160)
print(intensity1)
# -

# push to server
# Now that it is committed to the server, the mention "local: " is no more present when printing the intensity.
# Except for the properties that stays local until a whole project is committed.
# +
intensity1.commit()
print(intensity1)
# -

# via 1 step
# fluent api is implemented in pySpeos
# +
intensity2 = script.Intensity(speos_client=speos.client, name="Intensity.2").set_cos(N=2, total_angle=140).commit()
print(intensity2)
# -

# Specificity with properties needed
# +
intensity3 = script.Intensity(speos_client=speos.client, name="Intensity.3")
intensity3.set_gaussian().set_FWHM_angle_x(value=40).set_FWHM_angle_y(value=30).set_total_angle(value=170).set_axis_system(
    axis_system=[0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.1, 0.0, 0.0, 0.0, 1.0]
)
intensity3.commit()
print(intensity3)
# -

# ## Default Value
# Some default values are available when applicable in every methods and class.
# +
intensity4 = script.Intensity(speos_client=speos.client, name="Intensity.4")
print(intensity4)
# -

# ## Update
# Tipp: if you are manipulating an intensity already committed, don't forget to commit your changes.
# If you don't, you will still only watch what is committed on the server.
# +
intensity1.set_cos(N=1, total_angle=50).commit()
print(intensity1)
# -

# ## Reset
# Possibility to reset local values from the one available in the server.
# +
intensity3.set_cos()  # set cos but no commit
intensity3.reset()  # reset -> this will apply the server value to the local value
intensity3.delete()  # delete (to display the local value with the below print)
print(intensity3)
# -


# ## Delete
# Once the data is deleted from the server, you can still work with local data and maybe commit later.
# +
intensity1.delete()
print(intensity1)
# -

# +
intensity2.delete()
intensity3.delete()
# -
