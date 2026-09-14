"""Evaluate and visualize SOP metrics with a notebook-style script."""

# ## Prerequisites
#
# This tutorial evaluates Global RTA, Directional RTA, and BSDF slice metrics,
# then plots all returned data with the dedicated SOP metrics plotting helpers.
# The metric configuration messages are combined into one evaluation request.

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
from ansys.speos.core.sop_metrics_plotting import configure_plotting_theme, plot_results
from ansys.speos.core.speos import Speos

# -

# ## Start/Connect to Speos RPC Server
#
# Configure Matplotlib before creating figures, then select either a Docker-
# hosted Speos server or a locally launched server.

# +
HOSTNAME = "localhost"
GRPC_PORT = 50098
USE_DOCKER = True

if USE_DOCKER:
    assets_data_path = Path("/app") / "assets"
else:
    assets_data_path = Path("/path/to/your/download/assets/directory")

configure_plotting_theme()
if USE_DOCKER:
    speos = Speos(channel=default_docker_channel())
else:
    speos = launcher.launch_local_speos_rpc_server(port=GRPC_PORT)

bsdf_file_path = str(
    Path("D:/AnsysDev/pyspeos/pyspeos/tests/assets/Gaussian Fresnel 10 deg.anisotropicbsdf")
)
sop_db = vop_db = bsdf_sop_link = vop_before_link = vop_after_link = None
# -

# ## Create SOP and VOP templates
#
# The BSDF SOP is evaluated between VOP templates describing the media on each
# side of the optical surface.

# +
try:
    sop_db, vop_db, bsdf_sop_link, vop_before_link, vop_after_link = create_templates(
        speos, bsdf_file_path
    )
    # -

    # ## Build Metric Configurations
    #
    # Impact definitions provide the fixed inputs used by Directional RTA and
    # BSDF slice evaluations.

    # +
    normal_impact = make_impact_definition(0.0, 0.0, 0.0, 0.0, 550.0)

    # Global RTA returns reflectance, transmittance, and absorbance for each
    # requested wavelength.
    global_config = make_global_rta_config([380, 550, 700])

    # Directional RTA samples a range of incident angles while the other
    # impact inputs remain fixed.
    directional_config = make_directional_rta_config(
        [make_impact_definition(theta, 0.0, 0.0, 0.0, 550.0) for theta in range(0, 91, 15)]
    )
    # Each BSDF slice sweeps one variable and keeps the remaining four inputs
    # fixed. Create the five supported sweep types for two fixed impacts.
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

    # ## Evaluate Metrics
    #
    # The evaluator uses protobuf descriptors to place each config in the
    # appropriate field of ``MetricsConfig`` and returns one combined result.

    # +
    result_all = evaluate_metric(
        bsdf_sop_link,
        vop_before_link,
        vop_after_link,
        [global_config, directional_config, slices_config],
    )
    # -

    # ## Display Metric Statistics
    #
    # Print a compact textual summary before opening the figures.

    # +
    # -

    # ## Display Metrics Statistics

    # +
    display_metrics_statistics(
        result_all.global_rta, result_all.directional_rta, result_all.bsdf_slices
    )
    # -
    # -

    # ## Create Visualizations
    #
    # ``plot_results`` creates individual charts for each metric family and a
    # combined dashboard. Slice charts are grouped by sweep variable and label
    # each curve with its fixed input values.

    # +
    plot_results(result_all)

# -

# ## Cleanup

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
