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
import logging

_
from ansys.speos.core.body import Body, BodyFactory, BodyLink
from ansys.speos.core.face import Face, FaceFactory, FaceLink
from ansys.speos.core.intensity_template import (
    IntensityTemplate,
    IntensityTemplateFactory,
    IntensityTemplateLink,
)
from ansys.speos.core.job import Job, JobFactory, JobLink
from ansys.speos.core.logger import LOG, Logger
from ansys.speos.core.part import Part, PartFactory, PartLink
from ansys.speos.core.scene import Scene, SceneFactory, SceneLink
from ansys.speos.core.sensor_template import (
    SensorTemplate,
    SensorTemplateFactory,
    SensorTemplateLink,
)
from ansys.speos.core.simulation_template import (
    SimulationTemplate,
    SimulationTemplateFactory,
    SimulationTemplateLink,
)
from ansys.speos.core.sop_template import SOPTemplate, SOPTemplateFactory, SOPTemplateLink
from ansys.speos.core.source_template import (
    SourceTemplate,
    SourceTemplateFactory,
    SourceTemplateLink,
)
from ansys.speos.core.spectrum import Spectrum, SpectrumFactory, SpectrumLink
from ansys.speos.core.speos import Speos
from ansys.speos.core.vop_template import VOPTemplate, VOPTemplateFactory, VOPTemplateLink
