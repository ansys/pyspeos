from ansys.pyoptics.speos import LOG as logger
from ansys.pyoptics.speos.client import SpeosClient
from ansys.pyoptics.speos.speos import Speos
import os

MAX_MESSAGE_LENGTH = int(os.environ.get("SPEOS_MAX_MESSAGE_LENGTH", 256 * 1024**2))

try:
    import ansys.platform.instancemanagement as pypim

    _HAS_PIM = True
except ModuleNotFoundError:  # pragma: no cover
    _HAS_PIM = False

def launch_speos():
    if pypim.is_configured():
        logger.info(
            "Starting Geometry service remotely. The startup configuration will be ignored."
        )
        return launch_remote_speos()

def launch_remote_speos(
    version=None,
) -> Speos :
    """Start the Geometry Service remotely using the product instance management API.
    When calling this method, you need to ensure that you are in an
    environment where PyPIM is configured. This can be verified with
    :func:`pypim.is_configured <ansys.platform.instancemanagement.is_configured>`.
    Parameters
    ----------
    version : str, optional
        The Geometry Service version to run, in the 3 digits format, such as "212".
        If unspecified, the version will be chosen by the server.
    Returns
    -------
    ansys.geometry.core.modeler.Modeler
        An instance of the Geometry Service.
    """
    if not _HAS_PIM:  # pragma: no cover
        raise ModuleNotFoundError(
            "The package 'ansys-platform-instancemanagement' is required to use this function."
        )

    pim = pypim.connect()
    instance = pim.create_instance(product_name="speos", product_version=version)
    instance.wait_for_ready()
    channel = instance.build_grpc_channel()
    return SpeosClient(channel=channel, remote_instance=instance)