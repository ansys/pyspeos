from __future__ import annotations

from enum import Enum


class Project:
    """Stored in a file, a Project describe all Speos features (optical properties, sources, sensors, simulations)
    that user can fill in. Extension .scdocx refer to Speos for SpaceClaim.
    From Speos for NX, input file must have extension .prt or .asm.
    From pySpeos, input file is related to Scene filename.
    Project provide functions to get Speos Tree representation as a list of Features and to make actions on them."""

    def __init__(self, path: str):
        return

    def list():
        """Return all feature key as a tree, can be used to list all features"""
        return

    def add(feature):
        """Add a new feature, to associate to main ribbon commands"""
        return

    def get(featureId: str):
        """Get details about a feature"""

    def action(featureId: str):
        """Act on feature: update, hide/show, copy, ..."""

    def save():
        """Save class state in file given at construction"""


#
# Basic approach
# - Members for all entries
# - Enums for option menus
#


class OptPropB:
    """Represent a Speos optical properties"""

    name = ""
    description = ""
    metadata = {}

    class SurfaceType(Enum):
        MIRROR = 1
        OPTICALPOLISHED = 2
        LIBRARY = 3

    surface_type = SurfaceType(SurfaceType.OPTICALPOLISHED)
    surface_mirror_reflectance = 0
    surface_libary_file = ""

    class VolumeType(Enum):
        OPAQUE = 1
        OPTIC = 2
        NONHOMOGENEOUS = 3
        LIBRARY = 4

    volume_type = VolumeType(VolumeType.OPAQUE)
    volume_optic_index = 1
    volume_optic_absorption = 0
    volume_optic_constringence = 0
    volume_nonhmogeneous_file = ""
    volume_nonhmogeneous_coordsys = ()
    volume_libary_file = ""

    def Check(self):
        """Check consistency of state"""


#
# Fluent approach
# - functions for
#


class OptPropF:
    """Represent a Speos optical properties"""

    def __init__(self, name: str, description: str, metadata: map):
        return

    def set_surface_mirror(self, reflectance: float) -> OptPropF:
        return self

    def set_surface_opticalpolished(self) -> OptPropF:
        return self

    def set_surface_library(self, path: str) -> OptPropF:
        return self

    def set_volume_opaque(self) -> OptPropF:
        return self

    def set_volume_optique(self, index: float, absorption: float, constringence: float) -> OptPropF:
        return self

    def set_volume_nonhomogeneous(self, path: str, coordsys) -> OptPropF:
        return self

    def set_volume_library(self, path: str) -> OptPropF:
        return self


""" Usage """
p = Project("lenssystem.scdocx")
print(p.list())  # print tree
# Add mirror50
op = OptPropB()
op.name = "mirror50"
op.surface_type = OptPropB.SurfaceType.MIRROR
op.surface_mirror_reflectance = 50
op.volume_type = OptPropB.VolumeType.OPAQUE
p.add(op)
# Same with Fluent interface
p.add(OptPropF("mirror50").set_volume_opaque().set_mirror(50))
# Add bsdf
op = OptPropB()
op.surface_type = OptPropB.SurfaceType.LIBRARY
op.surface_libary_file = "mybsdf.bsdf"
op.volume_type = OptPropB.VolumeType.OPAQUE
p.add(op)
# Same with Fluent interface
p.add(OptPropF("mybsdf").set_volume_opaque().set_surface_library("mybsdf.bsdf"))
print(p.list())
