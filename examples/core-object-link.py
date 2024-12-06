# Copyright (C) 2023 - 2024 ANSYS, Inc. and/or its affiliates.
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

# # Object Link usage in PySpeos core layer

# This tutorial demonstrates how to use speos objects in layer core.

# ## What is an ObjectLink?

# The ObjectLink is an object that is created from a protobuf message and then stored in the server database.

# ## Which speos objects are used via ObjectLink?

# Almost all speos objects are used via ObjectLink: like sources, sensors, simulations and more.

# +
import ansys.speos.core as core

# -

# ## Create connection with speos rpc server

# +
speos = core.Speos(host="localhost", port=50098)
# -

# ## Create an ObjectLink

# +
sop_t_db = speos.client.sop_templates()
# -

# +
sop_t = core.SOPTemplate()
sop_t.name = "Mirror_90"
sop_t.mirror.reflectance = 90.0

mirror_90_link = sop_t_db.create(message=sop_t)
print(mirror_90_link)
# -

# +
sop_t = core.SOPTemplate()
sop_t.name = "Mirror_100"
sop_t.mirror.reflectance = 100.0

mirror_100_link = sop_t_db.create(message=sop_t)
# -

# ## Modify an ObjectLink

# Modify data locally

# +
mirror_data = mirror_90_link.get()
mirror_data.name = "Mirror_50"
mirror_data.mirror.reflectance = 50
# -

# Update on db

# +
mirror_90_link.set(data=mirror_data)
print(mirror_90_link)
# -

# ## Delete an ObjectLink

# This means deleting data in db

# +
mirror_100_link.delete()
mirror_90_link.delete()
sop_t_db.list()
# -
