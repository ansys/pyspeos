"""Evaluate SOP metrics with a notebook-style, executable script."""

# ## Prerequisites
#
# This example evaluates three SOP metric families:
#
# - Global RTA at selected wavelengths.
# - Directional RTA for a list of incident angles.
# - BSDF slices for each supported sweep variable.
#
# The metric helpers create protobuf configuration messages. The messages are
# passed together to ``evaluate_metric`` in one RPC call.

# +
from pathlib import Path

from ansys.speos.core import launcher
from ansys.speos.core.kernel.client import default_docker_channel
from ansys.speos.core.sop_metrics import (
    cleanup,
    create_templates,
    display_metrics_statistics,
    evaluate_metric,
    make_bsdf_slice_config,
    make_bsdf_slices_config,
    make_directional_rta_config,
    make_global_rta_config,
    make_impact_definition,
)
from ansys.speos.core.speos import Speos

# -

# ## Start/Connect to Speos RPC Server
#
# Select either a Docker-hosted Speos server or a local server. The returned
# ``Speos`` client is used to create templates and evaluate the metrics.

# +
HOSTNAME = "localhost"
GRPC_PORT = 50098
USE_DOCKER = True

if USE_DOCKER:
    assets_data_path = Path("/app") / "assets"
else:
    assets_data_path = Path("/path/to/your/download/assets/directory")

if USE_DOCKER:
    speos = Speos(channel=default_docker_channel())
else:
    speos = launcher.launch_local_speos_rpc_server(port=GRPC_PORT)

bsdf_file_path = str(assets_data_path / "Test_not_interpolated.brdf")
sop_db = vop_db = bsdf_sop_link = vop_before_link = vop_after_link = None
# -

# ## Create SOP and VOP templates
#
# The BSDF SOP is evaluated between two VOP templates. Here the templates
# represent the optical media before and after the BSDF surface.

# +
try:
    sop_db, vop_db, bsdf_sop_link, vop_before_link, vop_after_link = create_templates(
        speos, bsdf_file_path
    )
    # -

    # ## Build Metric Configurations
    #
    # An impact definition contains the five inputs used by directional and
    # slice evaluations: incident/outgoing angles and wavelength.

    # +
    normal_impact = make_impact_definition(0.0, 0.0, 0.0, 0.0, 550.0)

    # Global RTA needs only the wavelengths at which R, T, and A are sampled.
    global_config = make_global_rta_config([380, 550, 700])

    # Directional RTA evaluates the same optical impact at several incident
    # angles. The remaining inputs stay fixed for every directional sample.
    directional_config = make_directional_rta_config(
        [make_impact_definition(theta, 0.0, 0.0, 0.0, 550.0) for theta in range(0, 91, 15)]
    )
    # A BSDF slice sweeps one input while keeping the other four fixed. Build
    # five slices for the normal impact and repeat them for a second impact at
    # 45 degrees. Each slice contains ten samples over its selected range.
    slice_definitions = (
        ("theta_in", 0.0, 90.0),
        ("theta_out", 0.0, 90.0),
        ("phi_in", 0.0, 360.0),
        ("phi_out", 0.0, 90.0),
        ("wavelength", 350.0, 700.0),
    )
    slice_configs = [
        make_bsdf_slice_config(normal_impact, variable, start, end, 10)
        for variable, start, end in slice_definitions
    ]
    angled_impact = make_impact_definition(45.0, 45.0, 0.0, 0.0, 550.0)
    slice_configs.extend(
        make_bsdf_slice_config(angled_impact, variable, start, end, 10)
        for variable, start, end in slice_definitions
    )

    slices_config = make_bsdf_slices_config(slice_configs)
    # -

    # ## Evaluate Configured Metrics
    #
    # ``evaluate_metric`` identifies each configuration from its protobuf
    # descriptor and fills the matching field in ``MetricsConfig``.

    # +
    result_all = evaluate_metric(
        bsdf_sop_link,
        vop_before_link,
        vop_after_link,
        [global_config, directional_config, slices_config],
    )
    # -

    # ## Inspect Results
    #
    # The response contains ``global_rta``, ``directional_rta``, and
    # ``bsdf_slices`` fields corresponding to the requested configurations.

    # +
    display_metrics_statistics(
        result_all.global_rta, result_all.directional_rta, result_all.bsdf_slices
    )
    # -

    # ## Evaluate Server Defaults
    #
    # Omitting the configuration list sends no ``config`` field. The RPC
    # service then evaluates its default set of SOP metrics.

    # +
    default_results = evaluate_metric(bsdf_sop_link, vop_before_link, vop_after_link)
    print(f"Default Global RTA samples: {len(default_results.global_rta.samples)}")
    # -
# -

# ## Cleanup
#
# Delete the temporary SOP and VOP links and close the Speos connection even if
# evaluation or reporting raises an exception.

# +
finally:
    if all(item is not None for item in (bsdf_sop_link, vop_before_link, vop_after_link)):
        cleanup(
            speos,
            (bsdf_sop_link, vop_before_link, vop_after_link),
            {"SOPs": sop_db, "VOPs": vop_db},
        )
    else:
        speos.close()
# -
