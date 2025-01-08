# # How to create a spectrum

# This tutorial demonstrates how to create a spectrum in script layer.

## What is spectrum?

# Spectrum defines the wavelength information to be used for a source.

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

# ## Create simulation
# New project
# +
p = script.Project(speos=speos)
print(p)
# -

# ## Create
# Create locally in two steps
# The mention "local: " is added when printing the spectrum
# +
sp1 = script.Spectrum(speos_client=speos.client, name="Spectrum.1").set_blackbody(temperature=2930)
print(sp1)
# -

# Push it to the server
# Now that it is committed to the server, the mention "local: " is no more present when printing the spectrum
# +
sp1.commit()
print(sp1)
# -

# Create locally with one step
# +
sp2 = script.Spectrum(speos_client=speos.client, name="Spectrum.2").set_warmwhitefluorescent().commit()
print(sp2)
# -

# ## Read
# Datamodel
# A mention "local: " is added if it is not yet committed to the server
# +
print(sp1)
# -

# ## Update
# Tipp: if you are manipulating a spectrum already committed, don't forget to commit your changes.
# If you don't, you will still only watch what is committed on the server.
# +
sp1.set_monochromatic(wavelength=333).commit()
print(sp1)
# -

# ## Reset
# Possibility to reset local values from the one available in the server.
# +
sp1.set_incandescent()  # set incandescent but no commit
sp1.reset()  # reset -> this will apply the server value to the local value
sp1.delete()  # delete (to display the local value with the below print)
print(sp1)
# -

# ## Delete
# Once the data is deleted from the server, you can still work with local data and maybe commit later.
# +
sp2.delete()
print(sp1)
# -

# +
sp1.delete()
# -
