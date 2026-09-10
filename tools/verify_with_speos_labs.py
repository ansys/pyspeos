# Copyright (C) 2021 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
# SPDX-License-Identifier: MIT

r"""Verify the PySpeos file formats against the Speos Labs editors themselves.

This is a manual verification harness, not part of the test suite: it needs a local
Windows install of Speos Labs and it drives its editors through COM. It is the strongest
check available on the formats implemented in PySpeos, because it uses Speos as the
oracle instead of our own reader:

* **write** - PySpeos writes a file, the Speos editor opens it and saves it back, and
  PySpeos reads the result. Speos silently rewrites anything it did not understand, so a
  difference means PySpeos wrote something Speos read differently.
* **read** - the Speos editor opens a reference file and saves it back, which shows the
  layout Speos itself produces for that content.

Every Speos Labs editor exposes the same automation interface: ``Show(bShow)``,
``OpenFile(path)``, ``SaveFile(path)`` and ``GetPID``. ``GetPID`` takes no argument so it
reads as a property. The editors return 1 on success, except ``RayEditor`` which
returns 0.

Only the editors that have been registered are usable. They have no ``/RegServer``
switch: they register themselves when they start, which needs administrator rights.
Right-click the executable and pick *Run as administrator*, wait for the window, then
close it. Out of the box only ``UserMaterialViewer`` and ``RayEditor`` tend to be
registered.

Usage:

* ``python tools/verify_with_speos_labs.py`` verifies every format.
* ``python tools/verify_with_speos_labs.py material ray`` verifies the given formats.
* ``--keep`` keeps the produced files for inspection.

There is no Speos Labs editor for ``*.OPT3DMapping``: ``TextureMappingViewer.exe`` ships
without a type library and is not an automation server, so 3D texture mappings cannot be
verified this way.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
from typing import Callable, List

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ansys.speos.core import (  # noqa: E402
    CoatedSurfaceFile,
    CoatedSurfaceSample,
    MaterialConstringence,
    MaterialFile,
    Ray,
    RayFile,
    ScatteringSurfaceFile,
    ScatteringSurfaceSample,
    SimpleScatteringSurfaceFile,
    SpectrumFile,
    SpeosFileFormat,
    VolumeScatteringHenyeyGreenstein,
)

REPOSITORY = Path(__file__).resolve().parents[1]
ASSETS = REPOSITORY / "tests" / "assets"
REFERENCES = ASSETS / "file_formats"


@dataclass
class Case:
    """One file format and the Speos Labs editor that owns it."""

    name: str
    prog_id: str
    extension: str
    file_type: type[SpeosFileFormat]
    build: Callable[[], SpeosFileFormat]
    references: List[Path]
    success: int = 1
    """Value the editor returns on success. ``RayEditor`` returns 0 where the others return 1."""


def scattering_surface() -> ScatteringSurfaceFile:
    """Build a scattering surface exercising every contribution."""
    blank = ScatteringSurfaceSample()
    at_400 = ScatteringSurfaceSample(
        specular_reflection=30.0,
        specular_transmission=20.0,
        lambertian_reflection=20.0,
        lambertian_transmission=10.0,
    )
    at_600 = ScatteringSurfaceSample(
        gaussian_reflection=20.0,
        gaussian_transmission=20.0,
        gaussian_fwhm_incidence_reflection=30.0,
        gaussian_fwhm_incidence_transmission=5.0,
        gaussian_fwhm_perpendicular_reflection=5.0,
        gaussian_fwhm_perpendicular_transmission=30.0,
    )
    return ScatteringSurfaceFile(
        wavelengths=[400.0, 600.0],
        incident_angles=[0.0, 45.0, 90.0],
        samples=[[at_400, blank], [blank, at_600], [blank, blank]],
    )


def coated_surface() -> CoatedSurfaceFile:
    """Build a coating with S and P responses differing at normal incidence."""
    rows = {
        0.0: [(31.9, 68.1, 35.0, 65.0), (1.5, 98.5, 1.5, 98.5)],
        50.0: [(11.3, 88.7, 11.3, 88.7), (11.4, 88.6, 11.4, 88.6)],
        90.0: [(100.0, 0.0, 100.0, 0.0), (100.0, 0.0, 100.0, 0.0)],
    }
    return CoatedSurfaceFile(
        wavelengths=[480.0, 780.0],
        incident_angles=list(rows),
        samples=[[CoatedSurfaceSample(*values) for values in row] for row in rows.values()],
    )


def scattering_material() -> MaterialFile:
    """Build a diffusing material with a Henyey-Greenstein phase function."""
    return MaterialFile(
        description="PySpeos verification material",
        dispersion=MaterialConstringence(constringence=57.2, index=1.49),
        absorption_wavelengths=[486.0, 532.0, 643.0],
        absorption_values=[0.0001, 0.00015, 0.0005],
        scattering_wavelengths=[480.0, 555.0, 650.0],
        scattering_values=[0.016, 0.0165, 0.025],
        scattering=VolumeScatteringHenyeyGreenstein(
            wavelengths=[480.0, 555.0, 650.0], anisotropies=[0.8, 0.9, 0.9]
        ),
    )


def rays() -> RayFile:
    """Build a small collimated ray file."""
    return RayFile(
        rays=[
            Ray(position=(0.0, 0.0, 0.0), direction=(0.0, 0.0, 1.0), wavelength=633.0),
            Ray(position=(0.1, 0.0, 0.0), direction=(0.0, 0.0, 1.0), wavelength=555.0),
            Ray(position=(0.0, 0.1, 0.0), direction=(0.0, 0.0, 1.0), wavelength=450.0),
        ],
        radiant_flux=1.0,
        luminous_flux=112.0,
    )


CASES = [
    Case(
        "spectrum",
        "SpectrumViewer.Application",
        ".spectrum",
        SpectrumFile,
        lambda: SpectrumFile(
            description="PySpeos verification spectrum",
            wavelengths=[400.0, 555.0, 700.0],
            values=[10.0, 100.0, 25.0],
        ),
        [REFERENCES / "KB.spectrum", ASSETS / "R04.spectrum"],
    ),
    Case(
        "material",
        "UserMaterialViewer.Application",
        ".material",
        MaterialFile,
        scattering_material,
        sorted(REFERENCES.glob("*.material")),
    ),
    Case(
        "scattering",
        "AdvancedScatteringViewer.Application",
        ".scattering",
        ScatteringSurfaceFile,
        scattering_surface,
        [],
    ),
    Case(
        "simplescattering",
        "SimpleScatteringViewer.Application",
        ".simplescattering",
        SimpleScatteringSurfaceFile,
        lambda: SimpleScatteringSurfaceFile(mode="Reflection", lambertian=100.0, gaussian_fwhm=5.0),
        [ASSETS / "L100 2.simplescattering"],
    ),
    Case(
        "coated",
        "CoatedSurfaceViewer.Application",
        ".coated",
        CoatedSurfaceFile,
        coated_surface,
        [REFERENCES / "Coating Example.coated"],
    ),
    Case(
        "ray",
        "RayEditor.Application",
        ".ray",
        RayFile,
        rays,
        [ASSETS / "Rays.ray"],
        success=0,
    ),
]


class Editor:
    """A Speos Labs editor driven through COM."""

    def __init__(self, prog_id, success=1):
        import comtypes.client

        self._app = comtypes.client.CreateObject(prog_id, dynamic=True)
        self._success = success
        self._pid = int(self._app.GetPID)
        self._app.Show(0)

    def rewrite(self, source: Path, destination: Path) -> None:
        """Open a file in the editor and save it back to another path."""
        if self._app.OpenFile(str(source)) != self._success:
            raise RuntimeError(f"the editor refused to open {source}")
        if self._app.SaveFile(str(destination)) != self._success:
            raise RuntimeError(f"the editor refused to save {destination}")
        if not destination.is_file():
            raise RuntimeError(f"the editor reported success but wrote nothing to {destination}")

    def close(self) -> None:
        """Stop the editor process, which also invalidates the COM proxy."""
        subprocess.run(["taskkill", "/PID", str(self._pid), "/F"], capture_output=True, check=False)


def compare(case: Case, original: Path, rewritten: Path) -> tuple:
    """Report how the file Speos wrote differs from the one it was given.

    Returns the semantic differences, which are always defects, and the layout
    differences, which only are when the input was written by PySpeos.
    """
    try:
        before = case.file_type.load(original)
    except Exception as exc:  # noqa: BLE001
        return [f"PySpeos cannot read the input it was given: {exc}"], []
    try:
        after = case.file_type.load(rewritten)
    except Exception as exc:  # noqa: BLE001
        return [f"PySpeos cannot read what Speos wrote: {exc}"], []

    semantic = []
    if before != after:
        semantic.append("the model changed after Speos rewrote the file")
        semantic.extend(f"  {line}" for line in describe_difference(before, after))

    layout = []
    if case.extension != ".ray":
        original_lines = [line.rstrip() for line in read_lines(original) if line.strip()]
        rewritten_lines = [line.rstrip() for line in read_lines(rewritten) if line.strip()]
        for number, (ours, theirs) in enumerate(zip(original_lines, rewritten_lines), start=1):
            if ours != theirs:
                layout.append(f"line {number}: given {ours!r}, speos wrote {theirs!r}")
        if len(original_lines) != len(rewritten_lines):
            layout.append(
                f"line count: given {len(original_lines)}, speos wrote {len(rewritten_lines)}"
            )
    return semantic, layout


def describe_difference(before, after) -> List[str]:
    """List the fields that differ between two models."""
    lines = []
    for name in vars(before):
        mine, theirs = getattr(before, name), getattr(after, name)
        if mine != theirs:
            lines.append(f"{name}: {mine!r} -> {theirs!r}")
    return lines


def read_lines(path: Path) -> List[str]:
    """Read a text file as a list of lines."""
    return path.read_text(encoding="utf-8", errors="replace").splitlines()


def run(case: Case, work_dir: Path) -> bool:
    """Push the built model and every reference file of a case through the editor."""
    print(f"\n=== {case.name}  ({case.prog_id}) ===")
    try:
        editor = Editor(case.prog_id, case.success)
    except Exception as exc:  # noqa: BLE001
        print(f"  SKIPPED, the editor is not available: {exc}")
        print(f"  start {case.prog_id.split('.')[0]}.exe once as an administrator to register it")
        return True

    ok = True
    try:
        built = case.build().save(work_dir / f"pyspeos{case.extension}")
        inputs = [built] + [reference for reference in case.references if reference.is_file()]
        for index, source in enumerate(inputs):
            destination = work_dir / f"{index}_speos_{source.name}"
            ours = source is built
            label = "written by pyspeos" if ours else f"reference {source.name}"
            try:
                editor.rewrite(source, destination)
            except Exception as exc:  # noqa: BLE001
                print(f"  FAIL  {label}: {exc}")
                ok = False
                continue

            semantic, layout = compare(case, source, destination)
            failures = semantic + layout if ours else []
            print(f"  {'FAIL' if failures else 'OK  '}  {label}")
            for line in failures:
                print(f"          {line}")
            if not ours:
                # Speos rewriting a file it did not write only shows how it normalizes it,
                # for instance rounding spectrum samples to 6 significant digits.
                for line in semantic + layout:
                    print(f"          note: {line}")
            ok = ok and not failures
    finally:
        editor.close()
    return ok


def main() -> int:
    """Run the verification and return a process exit code."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("formats", nargs="*", help="formats to verify, all of them by default")
    parser.add_argument("--keep", action="store_true", help="keep the produced files")
    arguments = parser.parse_args()

    selected = [case for case in CASES if not arguments.formats or case.name in arguments.formats]
    if not selected:
        parser.error(f"unknown format, pick from {[case.name for case in CASES]}")

    work_dir = Path(tempfile.mkdtemp(prefix="pyspeos_labs_"))
    print(f"working in {work_dir}")
    try:
        return 0 if all([run(case, work_dir) for case in selected]) else 1
    finally:
        if arguments.keep:
            print(f"\nfiles kept in {work_dir}")
        else:
            shutil.rmtree(work_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
