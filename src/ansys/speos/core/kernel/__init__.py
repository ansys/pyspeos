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

"""PySpeos Kernel module gathers low-level interactions and internal operations of the project."""

from ansys.speos.core.kernel.body import BodyLink, ProtoBody
from ansys.speos.core.kernel.client import SpeosClient
from ansys.speos.core.kernel.face import FaceLink, ProtoFace
from ansys.speos.core.kernel.intensity_template import (
    IntensityTemplateLink,
    ProtoIntensityTemplate,
)
from ansys.speos.core.kernel.job import JobLink, ProtoJob
from ansys.speos.core.kernel.part import PartLink, ProtoPart
from ansys.speos.core.kernel.proto_message_utils import (
    protobuf_message_to_dict,
    protobuf_message_to_str,
)
from ansys.speos.core.kernel.scene import ProtoScene, SceneLink
from ansys.speos.core.kernel.sensor_template import (
    ProtoSensorTemplate,
    SensorTemplateLink,
)
from ansys.speos.core.kernel.simulation_template import (
    ProtoSimulationTemplate,
    SimulationTemplateLink,
)
from ansys.speos.core.kernel.sop_template import (
    ProtoSOPTemplate,
    SOPTemplateLink,
)
from ansys.speos.core.kernel.source_template import (
    ProtoSourceTemplate,
    SourceTemplateLink,
)
from ansys.speos.core.kernel.spectrum import ProtoSpectrum, SpectrumLink
from ansys.speos.core.kernel.vop_template import (
    ProtoVOPTemplate,
    VOPTemplateLink,
)
