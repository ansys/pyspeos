# Copyright (C) 2021 - 2026 Synopsys, Inc. and ANSYS, Inc. All rights reserved.
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

"""Plotting helpers for SOP metrics."""

import matplotlib.pyplot as plt
import numpy as np

from ansys.speos.core.generic.general_methods import graphics_required


@graphics_required
def configure_plotting_theme() -> None:
    """Apply the plotting theme used by the visualization example."""
    plt.style.use("seaborn-v0_8-whitegrid")
    plt.rcParams.update(
        {
            "figure.facecolor": "#f6f3ee",
            "axes.facecolor": "#ffffff",
            "axes.edgecolor": "#d4cec5",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "grid.alpha": 0.75,
            "legend.frameon": False,
            "savefig.bbox": "tight",
        }
    )


def _metric_values(result):
    """Return the three RTA value arrays from a result."""
    return {
        "Reflectance": [sample.reflectance for sample in result.samples],
        "Transmittance": [sample.transmittance for sample in result.samples],
        "Absorbance": [sample.absorbance for sample in result.samples],
    }


@graphics_required
def plot_global_rta_results(result_global_rta, title="Global RTA Results", figsize=(12, 6)):
    """Plot Global RTA components as stacked bars and individual curves."""
    if not result_global_rta.samples:
        return None
    wavelengths = [sample.wavelength for sample in result_global_rta.samples]
    values = _metric_values(result_global_rta)
    fig, (bar_axis, line_axis) = plt.subplots(1, 2, figsize=figsize)
    x = np.arange(len(wavelengths))
    bottom = np.zeros(len(wavelengths))
    for (label, data), color in zip(values.items(), ("#1f77b4", "#ff7f0e", "#d62728")):
        bar_axis.bar(x, data, 0.6, bottom=bottom, label=label, color=color)
        line_axis.plot(wavelengths, data, "o-", label=label, linewidth=2, markersize=7)
        bottom += np.array(data)
    bar_axis.set_xticks(x, [f"{int(wavelength)} nm" for wavelength in wavelengths])
    bar_axis.set_title("RTA Components (Stacked)")
    line_axis.set_title("RTA Components (Individual)")
    for axis in (bar_axis, line_axis):
        axis.set_xlabel("Wavelength (nm)")
        axis.set_ylabel("Value")
        axis.set_ylim(0, 1)
        axis.grid(True, alpha=0.3)
        axis.legend()
    fig.suptitle(title)
    fig.tight_layout()
    return fig


@graphics_required
def plot_directional_rta_results(
    result_directional_rta, title="Directional RTA Results", figsize=None
):
    """Plot Directional RTA values grouped by incident azimuth."""
    if not result_directional_rta.samples:
        return None
    groups = {}
    for sample in result_directional_rta.samples:
        phi = sample.inputs.phi_in
        groups.setdefault(
            phi, {"theta": [], "reflectance": [], "transmittance": [], "absorbance": []}
        )
        groups[phi]["theta"].append(sample.inputs.theta_in)
        for metric in ("reflectance", "transmittance", "absorbance"):
            groups[phi][metric].append(getattr(sample, metric))
    fig, axes = plt.subplots(
        len(groups), 3, figsize=figsize or (15, 4 * len(groups)), squeeze=False
    )
    for row, (phi, data) in enumerate(sorted(groups.items())):
        order = np.argsort(data["theta"])
        for column, (metric, color) in enumerate(
            zip(("reflectance", "transmittance", "absorbance"), ("#1f77b4", "#ff7f0e", "#d62728"))
        ):
            axis = axes[row, column]
            theta = np.array(data["theta"])[order]
            values = np.array(data[metric])[order]
            axis.plot(theta, values, "o-", color=color, label=metric.title())
            axis.fill_between(theta, values, alpha=0.2, color=color)
            axis.set_title(f"{metric.title()} (phi_in = {phi:.1f} deg)")
            axis.set_xlabel("Incident angle theta_in (degrees)")
            axis.set_ylabel("Value")
            axis.set_ylim(0, 1)
            axis.grid(True, alpha=0.3)
            axis.legend()
    fig.suptitle(title)
    fig.tight_layout()
    return fig


@graphics_required
def plot_bsdf_slices(result_bsdf_slices, title="BSDF Slices Results", figsize=None):
    """Plot BSDF slices grouped by their swept variable."""
    if not result_bsdf_slices.slices:
        return None
    sweep_variables = ("theta_in", "theta_out", "phi_in", "phi_out", "wavelength")
    grouped_slices = {variable: [] for variable in sweep_variables}
    for slice_result in result_bsdf_slices.slices:
        if slice_result.swept_variable in grouped_slices:
            grouped_slices[slice_result.swept_variable].append(slice_result)

    fig, axes = plt.subplots(1, 5, figsize=figsize or (20, 5), squeeze=False)
    for axis, variable in zip(axes[0], sweep_variables):
        variable_slices = grouped_slices[variable]
        if not variable_slices:
            axis.text(0.5, 0.5, "No data", ha="center", va="center")
            axis.set_axis_off()
            axis.set_title(variable)
            continue

        colors = plt.cm.viridis(np.linspace(0, 1, len(variable_slices)))
        for color, slice_result in zip(colors, variable_slices):
            x_values = [sample.swept_variable_value for sample in slice_result.samples]
            y_values = [sample.bsdf_value for sample in slice_result.samples]
            inputs = slice_result.inputs
            fixed_values = ", ".join(
                f"{name}={getattr(inputs, name):g}"
                for name in ("theta_in", "theta_out", "phi_in", "phi_out", "wavelength")
                if name != variable
            )
            axis.plot(x_values, y_values, "o-", color=color, label=fixed_values)
        axis.set_title(variable)
        axis.set_xlabel("Swept value")
        axis.set_ylabel("BSDF value")
        axis.grid(True, alpha=0.3)
        axis.legend(
            fontsize="small",
            loc="upper center",
            bbox_to_anchor=(0.5, -0.3),
            borderaxespad=0,
        )

    fig.suptitle(title)
    fig.tight_layout(rect=(0, 0.2, 1, 0.95))
    return fig


@graphics_required
def plot_metrics_summary(
    result_global_rta=None,
    result_directional_rta=None,
    result_bsdf_slices=None,
    title="SOP Metrics Evaluation Summary",
    figsize=(16, 10),
):
    """Plot all available SOP metric results in one dashboard figure."""
    figure = plt.figure(figsize=figsize)
    grid = figure.add_gridspec(2, 5, height_ratios=(1, 1.2))
    global_axis = figure.add_subplot(grid[0, :2])
    directional_axis = figure.add_subplot(grid[0, 2:])
    slices_axis = figure.add_subplot(grid[1, 0])

    if result_global_rta and result_global_rta.samples:
        wavelengths = [sample.wavelength for sample in result_global_rta.samples]
        values = _metric_values(result_global_rta)
        positions = np.arange(len(wavelengths))
        bottom = np.zeros(len(wavelengths))
        colors = ("#1f77b4", "#ff7f0e", "#d62728")
        for (label, data), color in zip(values.items(), colors):
            global_axis.bar(positions, data, 0.65, bottom=bottom, label=label, color=color)
            bottom += np.array(data)
        global_axis.set_xticks(positions, [f"{int(wavelength)}" for wavelength in wavelengths])
        global_axis.set_xlabel("Wavelength (nm)")
        global_axis.set_ylabel("Value")
        global_axis.set_ylim(0, 1)
        global_axis.legend()
    else:
        global_axis.text(0.5, 0.5, "No Global RTA data", ha="center", va="center")
        global_axis.set_axis_off()
    global_axis.set_title("Global RTA")

    if result_directional_rta and result_directional_rta.samples:
        directional_colors = {
            "reflectance": "#1f77b4",
            "transmittance": "#ff7f0e",
            "absorbance": "#d62728",
        }
        groups = {}
        for sample in result_directional_rta.samples:
            phi = sample.inputs.phi_in
            groups.setdefault(phi, []).append(sample)
        for phi, samples in sorted(groups.items()):
            samples.sort(key=lambda sample: sample.inputs.theta_in)
            theta = [sample.inputs.theta_in for sample in samples]
            for metric, color in directional_colors.items():
                directional_axis.plot(
                    theta,
                    [getattr(sample, metric) for sample in samples],
                    "o-",
                    color=color,
                    alpha=0.8,
                    label=f"{metric.title()} (phi={phi:g} deg)",
                )
        directional_axis.set_xlabel("Incident angle theta_in (degrees)")
        directional_axis.set_ylabel("Value")
        directional_axis.set_ylim(0, 1)
        directional_axis.legend(fontsize="small", ncol=2)
    else:
        directional_axis.text(0.5, 0.5, "No Directional RTA data", ha="center", va="center")
        directional_axis.set_axis_off()
    directional_axis.set_title("Directional RTA")

    if result_bsdf_slices and result_bsdf_slices.slices:
        sweep_variables = ("theta_in", "theta_out", "phi_in", "phi_out", "wavelength")
        grouped_slices = {variable: [] for variable in sweep_variables}
        for slice_result in result_bsdf_slices.slices:
            if slice_result.swept_variable in grouped_slices:
                grouped_slices[slice_result.swept_variable].append(slice_result)

        plot_axes = [slices_axis]
        for index in range(1, len(sweep_variables)):
            plot_axes.append(figure.add_subplot(grid[1, index]))

        for axis, variable in zip(plot_axes, sweep_variables):
            variable_slices = grouped_slices[variable]
            if not variable_slices:
                axis.text(0.5, 0.5, "No data", ha="center", va="center")
                axis.set_axis_off()
                axis.set_title(variable)
                continue
            colors = plt.cm.viridis(np.linspace(0, 1, len(variable_slices)))
            for color, slice_result in zip(colors, variable_slices):
                x_values = [sample.swept_variable_value for sample in slice_result.samples]
                y_values = [sample.bsdf_value for sample in slice_result.samples]
                inputs = slice_result.inputs
                fixed_values = ", ".join(
                    f"{name}={getattr(inputs, name):g}"
                    for name in ("theta_in", "theta_out", "phi_in", "phi_out", "wavelength")
                    if name != variable
                )
                axis.plot(x_values, y_values, "o-", color=color, label=fixed_values)
            axis.set_title(variable)
            axis.set_xlabel("Swept value")
            axis.set_ylabel("BSDF value")
            axis.legend(
                fontsize="small",
                loc="upper center",
                bbox_to_anchor=(0.5, -0.3),
                borderaxespad=0,
            )
    else:
        slices_axis.text(0.5, 0.5, "No BSDF slice data", ha="center", va="center")
        slices_axis.set_axis_off()
    if not result_bsdf_slices or not result_bsdf_slices.slices:
        slices_axis.set_title("BSDF Slices")

    figure.suptitle(title, fontsize=16)
    figure.tight_layout(rect=(0, 0.2, 1, 0.95))
    return figure


@graphics_required
def plot_results(result_all) -> None:
    """Render individual metric charts and the combined summary chart."""
    for figure in (
        plot_global_rta_results(result_all.global_rta),
        plot_directional_rta_results(result_all.directional_rta),
        plot_bsdf_slices(result_all.bsdf_slices),
        plot_metrics_summary(
            result_all.global_rta, result_all.directional_rta, result_all.bsdf_slices
        ),
    ):
        plt.show()
