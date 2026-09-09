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

"""Reusable setup, evaluation, reporting, and plotting helpers for SOP metrics."""

from types import SimpleNamespace

from ansys.api.speos.experimental.sop.v1 import sop_pb2 as exp_messages
import matplotlib.pyplot as plt
import numpy as np

from ansys.speos.core.kernel.sop_template import ProtoSOPTemplate
from ansys.speos.core.kernel.vop_template import ProtoVOPTemplate
from ansys.speos.core.speos import Speos


def create_templates(speos: Speos, bsdf_file_path: str):
    """Create the BSDF SOP and the two VOP templates used by metric evaluation."""
    sop_db = speos.client.sop_templates()
    vop_db = speos.client.vop_templates()
    sop_message = ProtoSOPTemplate(name="BSDF_Surface")
    sop_message.library.sop_file_uri = bsdf_file_path
    bsdf_sop_link = sop_db.create(message=sop_message)
    vop_before_message = ProtoVOPTemplate(name="Optic_Before")
    vop_before_message.optic.index = 1.0
    vop_before_link = vop_db.create(message=vop_before_message)
    vop_after_message = ProtoVOPTemplate(name="Optic_After")
    vop_after_message.optic.index = 1.5
    vop_after_link = vop_db.create(message=vop_after_message)
    return sop_db, vop_db, bsdf_sop_link, vop_before_link, vop_after_link


def make_impact_definition(
    theta_in: float, phi_in: float, wavelength: float
) -> exp_messages.ImpactDefinition:
    """Build an impact definition for directional or slice evaluation."""
    return exp_messages.ImpactDefinition(theta_in=theta_in, phi_in=phi_in, wavelength=wavelength)


def make_impact_def(
    theta_in: float, phi_in: float, wavelength: float
) -> exp_messages.ImpactDefinition:
    """Build an impact definition using the legacy example helper name."""
    return make_impact_definition(theta_in, phi_in, wavelength)


def make_metrics_config(metric_name: str, metric_config) -> exp_messages.MetricsConfig:
    """Wrap a metric-specific protobuf configuration in ``MetricsConfig``."""
    config = exp_messages.MetricsConfig()
    getattr(config, metric_name).CopyFrom(metric_config)
    return config


def make_global_rta_config(wavelengths: list[float]) -> exp_messages.GlobalRTAConfig:
    """Build a Global RTA configuration for the supplied wavelengths."""
    config = exp_messages.GlobalRTAConfig()
    config.wavelengths.extend(wavelengths)
    return config


def make_directional_rta_config(
    impacts: list[exp_messages.ImpactDefinition],
) -> exp_messages.DirectionalRTAConfig:
    """Build a Directional RTA configuration from impact definitions."""
    config = exp_messages.DirectionalRTAConfig()
    config.impacts.extend(impacts)
    return config


def make_bsdf_slice_config(
    fixed_values: exp_messages.ImpactDefinition,
    sweep_variable: str,
    sweep_start: float,
    sweep_end: float,
    num_samples: int,
) -> exp_messages.BSDFSlicesConfig.SliceConfig:
    """Build one BSDF slice configuration."""
    config = exp_messages.BSDFSlicesConfig.SliceConfig()
    config.fixed_values.CopyFrom(fixed_values)
    config.sweep_variable = sweep_variable
    config.sweep_start = sweep_start
    config.sweep_end = sweep_end
    config.num_samples = num_samples
    return config


def make_bsdf_slices_config(
    slices: list[exp_messages.BSDFSlicesConfig.SliceConfig],
) -> exp_messages.BSDFSlicesConfig:
    """Build a BSDF slices configuration from slice definitions."""
    config = exp_messages.BSDFSlicesConfig()
    config.slices.extend(slices)
    return config


def _evaluate_metric(bsdf_sop_link, vop_before_link, vop_after_link, name, config=None):
    request = {
        "vop_before_guid": vop_before_link.key,
        "vop_after_guid": vop_after_link.key,
    }
    if config is not None:
        request["config"] = make_metrics_config(name, config)
    return bsdf_sop_link.evaluate_metrics(**request)


def evaluate_global_rta(bsdf_sop_link, vop_before_link, vop_after_link, config):
    """Evaluate Global RTA and return its protobuf response."""
    return _evaluate_metric(
        bsdf_sop_link, vop_before_link, vop_after_link, "global_rta", config
    ).global_rta


def evaluate_directional_rta(bsdf_sop_link, vop_before_link, vop_after_link, config):
    """Evaluate Directional RTA and return its protobuf response."""
    return _evaluate_metric(
        bsdf_sop_link, vop_before_link, vop_after_link, "directional_rta", config
    ).directional_rta


def evaluate_bsdf_slices(bsdf_sop_link, vop_before_link, vop_after_link, config):
    """Evaluate BSDF slices and return their protobuf response."""
    return _evaluate_metric(
        bsdf_sop_link, vop_before_link, vop_after_link, "bsdf_slices", config
    ).bsdf_slices


def evaluate_all_metrics(bsdf_sop_link, vop_before_link, vop_after_link):
    """Evaluate representative Global RTA, Directional RTA, and BSDF slices."""
    impact = make_impact_definition(0.0, 0.0, 550.0)
    directional = make_directional_rta_config(
        [make_impact_definition(theta, 0.0, 550.0) for theta in range(0, 91, 15)]
    )
    slices = make_bsdf_slices_config(
        [
            make_bsdf_slice_config(impact, variable, start, end, 10)
            for variable, start, end in (
                ("theta_in", 0.0, 90.0),
                ("theta_out", 0.0, 90.0),
                ("phi_out", 0.0, 90.0),
                ("wavelength", 350.0, 700.0),
            )
        ]
    )
    return SimpleNamespace(
        global_rta=evaluate_global_rta(
            bsdf_sop_link,
            vop_before_link,
            vop_after_link,
            make_global_rta_config([380, 550, 700]),
        ),
        directional_rta=evaluate_directional_rta(
            bsdf_sop_link, vop_before_link, vop_after_link, directional
        ),
        bsdf_slices=evaluate_bsdf_slices(bsdf_sop_link, vop_before_link, vop_after_link, slices),
    )


def evaluate_default_metrics(bsdf_sop_link, vop_before_link, vop_after_link):
    """Evaluate metrics with server defaults and return the complete response."""
    return _evaluate_metric(bsdf_sop_link, vop_before_link, vop_after_link, "default")


def display_metrics_statistics(
    result_global_rta=None, result_directional_rta=None, result_bsdf_slices=None
) -> None:
    """Print compact statistics for the available metric results."""
    print("\n" + "=" * 70)
    print("METRICS EVALUATION STATISTICS".center(70))
    print("=" * 70)
    if result_global_rta and result_global_rta.samples:
        print(f"\n[GLOBAL RTA] Samples: {len(result_global_rta.samples)}")
        for sample in result_global_rta.samples:
            print(
                f"  {sample.wavelength:>7.1f} nm | R={sample.reflectance:.4f} | "
                f"T={sample.transmittance:.4f} | A={sample.absorbance:.4f}"
            )
    if result_directional_rta and result_directional_rta.samples:
        print(f"\n[DIRECTIONAL RTA] Samples: {len(result_directional_rta.samples)}")
        for sample in result_directional_rta.samples:
            print(
                f"  theta={sample.inputs.theta_in:>6.1f} deg | "
                f"phi={sample.inputs.phi_in:>6.1f} deg | R={sample.reflectance:.4f} | "
                f"T={sample.transmittance:.4f} | A={sample.absorbance:.4f}"
            )
    if result_bsdf_slices and result_bsdf_slices.slices:
        print(f"\n[BSDF SLICES] Total slices: {len(result_bsdf_slices.slices)}")
        for index, slice_result in enumerate(result_bsdf_slices.slices, start=1):
            print(
                f"Slice {index}: {slice_result.swept_variable}, samples={len(slice_result.samples)}"
            )
    print("\n" + "=" * 70)


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


def plot_bsdf_slices(result_bsdf_slices, title="BSDF Slices Results", figsize=None):
    """Plot one curve for each BSDF slice."""
    if not result_bsdf_slices.slices:
        return None
    count = len(result_bsdf_slices.slices)
    columns = min(2, count)
    rows = (count + columns - 1) // columns
    fig, axes = plt.subplots(
        rows, columns, figsize=figsize or (8 * columns, 5 * rows), squeeze=False
    )
    axes = axes.flatten()
    colors = plt.cm.viridis(np.linspace(0, 1, count))
    for index, slice_result in enumerate(result_bsdf_slices.slices):
        axis = axes[index]
        x = [sample.swept_variable_value for sample in slice_result.samples]
        y = [sample.bsdf_value for sample in slice_result.samples]
        axis.plot(x, y, "o-", color=colors[index], label=f"Slice {index + 1}")
        axis.fill_between(x, y, alpha=0.2, color=colors[index])
        axis.set_title(f"Slice {index + 1}: {slice_result.swept_variable}")
        axis.set_xlabel("Swept value")
        axis.set_ylabel("BSDF value")
        axis.grid(True, alpha=0.3)
        axis.legend()
    for axis in axes[count:]:
        axis.set_visible(False)
    fig.suptitle(title)
    fig.tight_layout()
    return fig


def plot_metrics_summary(
    result_global_rta=None,
    result_directional_rta=None,
    result_bsdf_slices=None,
    title="SOP Metrics Evaluation Summary",
    figsize=(16, 10),
):
    """Plot a compact overview of the available SOP metric results."""
    fig, axis = plt.subplots(figsize=figsize)
    axis.set_axis_off()
    lines = [title]
    if result_global_rta:
        lines.append(f"Global RTA samples: {len(result_global_rta.samples)}")
    if result_directional_rta:
        lines.append(f"Directional RTA samples: {len(result_directional_rta.samples)}")
    if result_bsdf_slices:
        lines.append(f"BSDF slices: {len(result_bsdf_slices.slices)}")
    axis.text(0.05, 0.9, "\n".join(lines), va="top", fontsize=14)
    fig.tight_layout()
    return fig


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
        if figure is not None:
            figure.show()


def cleanup(speos: Speos, links, databases) -> None:
    """Delete temporary links, report remaining objects, and close Speos."""
    for link in links:
        link.delete()
    for name, database in databases.items():
        print(f"Remaining {name}: {len(database.list())}")
    speos.close()
