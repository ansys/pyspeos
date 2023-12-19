"""
Test basic using optical properties from script layer.
"""

import os

import ansys.speos.script as script
from conftest import test_path


def test_create_OptProp():
    """Test creation of optical property."""
    p = script.Project()
    assert p is not None
    print(p)
    op = (
        p.create_optical_property(name="myprop", description="mydesc")
        .set_geometries(geometries=[script.GeoRef.from_native_link(geopath="mybody")])
        .set_surface_mirror(reflectance=100)
        .set_volume_library(os.path.join(test_path, "AIR.material"))
        .commit()
    )
    assert op is not None
    print(op)
    print(p)
