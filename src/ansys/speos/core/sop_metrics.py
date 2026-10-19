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

"""Reusable setup and evaluation helpers for SOP metrics."""

from ansys.api.speos.experimental.sop.v1 import sop_pb2 as exp_messages

from ansys.speos.core.kernel.sop_template import ProtoSOPTemplate
from ansys.speos.core.kernel.vop_template import ProtoVOPTemplate
from ansys.speos.core.speos import Speos

_SWEEP_DEFINITIONS = (
    ("theta_in", 0.0, 90.0),
    ("theta_out", 0.0, 90.0),
    ("phi_in", 0.0, 360.0),
    ("phi_out", 0.0, 90.0),
    ("wavelength", 350.0, 700.0),
)


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
    theta_in: float, theta_out: float, phi_in: float, phi_out: float, wavelength: float
) -> exp_messages.ImpactDefinition:
    """Build an impact definition for directional or slice evaluation."""
    return exp_messages.ImpactDefinition(
        theta_in=theta_in,
        theta_out=theta_out,
        phi_in=phi_in,
        phi_out=phi_out,
        wavelength=wavelength,
    )


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


def _make_bsdf_slice_configs(
    fixed_values: exp_messages.ImpactDefinition,
) -> list[exp_messages.BSDFSlicesConfig.SliceConfig]:
    """Build the standard five BSDF slices for one fixed impact definition."""
    return [
        make_bsdf_slice_config(fixed_values, variable, start, end, 10)
        for variable, start, end in _SWEEP_DEFINITIONS
    ]


def evaluate_metric(bsdf_sop_link, vop_before_link, vop_after_link, configs=None):
    """Evaluate configured SOP metrics or the server default metrics.

    Parameters
    ----------
    bsdf_sop_link : object
        Link to the BSDF SOP template.
    vop_before_link : object
        Link to the VOP template before the SOP.
    vop_after_link : object
        Link to the VOP template after the SOP.
    configs : list, optional
        Metric-specific protobuf configurations created by the ``make_*_config``
        helpers. The corresponding ``MetricsConfig`` field is selected from
        each configuration's protobuf descriptor.

    Returns
    -------
    object
        The complete metrics evaluation response.
    """
    request = {
        "vop_before_guid": vop_before_link.key,
        "vop_after_guid": vop_after_link.key,
    }
    if configs:
        metrics_config = exp_messages.MetricsConfig()
        config_fields = metrics_config.DESCRIPTOR.fields_by_name.values()
        for metric_config in configs:
            config_field = next(
                (
                    field
                    for field in config_fields
                    if field.message_type
                    and field.message_type.full_name == metric_config.DESCRIPTOR.full_name
                ),
                None,
            )
            if config_field is None:
                raise TypeError(
                    f"Unsupported SOP metric configuration: {metric_config.DESCRIPTOR.full_name}"
                )
            getattr(metrics_config, config_field.name).CopyFrom(metric_config)
        request["config"] = metrics_config
    return bsdf_sop_link.evaluate_metrics(**request)


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
                f"  Slice {index}: {slice_result.swept_variable}, "
                f"samples={len(slice_result.samples)}"
            )
    print("\n" + "=" * 70)


def cleanup(speos: Speos, links, databases) -> None:
    """Delete temporary links, report remaining objects, and close Speos."""
    for link in links:
        link.delete()
    for name, database in databases.items():
        print(f"Remaining {name}: {len(database.list())}")
    speos.close()
