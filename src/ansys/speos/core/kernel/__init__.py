# Copyright (C) 2021 - 2025 ANSYS, Inc. and/or its affiliates.
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

"""This init file allows python to treat directories containing it as modules.

Import any methods you want exposed at your library level here.

For example, if you want to avoid this behavior:

.. code::

   >>> from ansys.product.library.module import add

Then add the import within this module to enable:

.. code::

   >>> from ansys.product import library
   >>> library.add(1, 2)

.. note::

   It's best to import the version here as well so it can be
   referenced at the library level.

"""

from ansys.speos.core.kernel.body import Body, BodyLink
from ansys.speos.core.kernel.face import Face, FaceLink
from ansys.speos.core.kernel.intensity_template import IntensityTemplate, IntensityTemplateLink
from ansys.speos.core.kernel.job import Job, JobLink
from ansys.speos.core.logger import LOG, Logger
from ansys.speos.core.kernel.part import Part, PartLink
from ansys.speos.core.kernel.proto_message_utils import protobuf_message_to_dict, protobuf_message_to_str
from ansys.speos.core.kernel.scene import Scene, SceneLink
from ansys.speos.core.kernel.sensor_template import SensorTemplate, SensorTemplateLink
from ansys.speos.core.kernel.simulation_template import SimulationTemplate, SimulationTemplateLink
from ansys.speos.core.kernel.sop_template import SOPTemplate, SOPTemplateLink
from ansys.speos.core.kernel.source_template import SourceTemplate, SourceTemplateLink
from ansys.speos.core.kernel.spectrum import Spectrum, SpectrumLink
from ansys.speos.core.speos import Speos, SpeosClient
from ansys.speos.core.kernel.vop_template import VOPTemplate, VOPTemplateLink
