import pytest
from ansys.pyoptics.speos.lpf import lpfreader

def test_lpfreader():
    r = lpfreader()
    r.InitLpfFileName("toto.lpf")