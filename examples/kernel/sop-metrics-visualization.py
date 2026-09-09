"""Evaluate and visualize SOP metrics with a notebook-style script."""

# ## Prerequisites

# +
from pathlib import Path

from ansys.speos.core import launcher
from ansys.speos.core.kernel.client import default_docker_channel
from ansys.speos.core.sop_metrics import (
    cleanup,
    configure_plotting_theme,
    create_templates,
    display_metrics_statistics,
    evaluate_all_metrics,
    plot_results,
)
from ansys.speos.core.speos import Speos

# -

# ## Start/Connect to Speos RPC Server

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

bsdf_file_path = str(assets_data_path / "Test_not_interpolated.brdf")
sop_db = vop_db = bsdf_sop_link = vop_before_link = vop_after_link = None
# -

# ## Create SOP and VOP templates

# +
try:
    sop_db, vop_db, bsdf_sop_link, vop_before_link, vop_after_link = create_templates(
        speos, bsdf_file_path
    )
    # -

    # ## Evaluate Metrics

    # +
    result_all = evaluate_all_metrics(bsdf_sop_link, vop_before_link, vop_after_link)
    # -

    # ## Display Metrics Statistics

    # +
    display_metrics_statistics(
        result_all.global_rta, result_all.directional_rta, result_all.bsdf_slices
    )
    # -

    # ## Create Visualizations

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
