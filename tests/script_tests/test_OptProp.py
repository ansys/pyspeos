"""
Test basic using optical properties from script layer.
"""
import pytest

import ansys.speos.script as script


def test_create_OptProp():
    """Test creation of optical property."""
    pytest.skip("skipping this test")
    p = script.Project("test_create_OptProp")
    assert p is not None
    print(p.list())
    op = (
        p.create_optical_property(name="myprop", description="mydesc")
        .set_geometries(geometries=[script.GeoRef.from_native_link(geopath="mybody")])
        .set_surface_mirror(reflectance=100)
        .set_volume_library("mymaterial.material")
        .commit()
    )

    print(p.list())
    pass

    # obj = p.opt_props().new("mirror50").set_volume_opaque().set_surface_mirror(50).commit()
    # obj = p.create_source_surface("mysrc")
    # p.add(OptProp("mybsdf").set_volume_opaque().set_surface_library("mybsdf.bsdf"))
    # print(p.list())
