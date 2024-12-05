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

import os.path

from nbconvert.preprocessors import ExecutePreprocessor
import nbformat

from conftest import test_path

NOTEBOOKS = [
    "core_modify_camera.ipynb",
    "core_object_link.ipynb",
    "core_scene_job.ipynb",
    "script_intensity.ipynb",
    "script_lpf_preview.ipynb",
    "script_opt_prop.ipynb",
    "script_part.ipynb",
    "script_prism_example.ipynb",
    "script_project.ipynb",
    "script_sensor.ipynb",
    "script_simulation.ipynb",
    "script_source.ipynb",
    "script_spectrum.ipynb",
    "workflow_combine_speos_cars.ipynb",
    "workflow_open_result.ipynb",
]


def run_jupyter(notebook):
    with open(notebook) as f:
        nb = nbformat.read(f, as_version=4)
        ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
        try:
            assert ep.preprocess(nb) is not None, f"Got empty notebook for {notebook}"
        except Exception:
            assert False, f"Failed executing {notebook}"


def test_notebooks():
    note_book_path = os.path.join(os.path.split(os.path.split(test_path)[0])[0], "jupyter_notebooks")
    for note_book in NOTEBOOKS:
        print("Running: " + note_book)
        run_jupyter(os.path.join(note_book_path, note_book))
