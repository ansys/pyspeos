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

from ansys.pyoptics.speos._version import __version__
from ansys.pyoptics.speos.module import add
from ansys.pyoptics.speos.other_module import Complex, ExampleClass
from ansys.pyoptics.speos.lpf import lpfreader

