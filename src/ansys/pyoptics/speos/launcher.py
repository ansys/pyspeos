import os

from ansys.pyoptics.speos import LOG as logger
from ansys.pyoptics.speos.speos import Speos

MAX_MESSAGE_LENGTH = int(os.environ.get("SPEOS_MAX_MESSAGE_LENGTH", 256 * 1024**2))

try:
    import ansys.platform.instancemanagement as pypim

    _HAS_PIM = True
except ModuleNotFoundError:  # pragma: no cover
    _HAS_PIM = False


def launch_speos():
    if pypim.is_configured():
        logger.info("Starting Speos service remotely. The startup configuration will be ignored.")
        return launch_remote_speos()


def launch_remote_speos(
    version=None,
) -> Speos:
    """Start the Speos Service remotely using the product instance management API.
    When calling this method, you need to ensure that you are in an
    environment where PyPIM is configured. This can be verified with
    :func:`pypim.is_configured <ansys.platform.instancemanagement.is_configured>`.

    Parameters
    ----------
    version : str, optional
        The Speos Service version to run, in the 3 digits format, such as "212".
        If unspecified, the version will be chosen by the server.

    Returns
    -------
    ansys.pyoptics.speos.speos.Speos
        An instance of the Speos Service.
    """
    if not _HAS_PIM:  # pragma: no cover
        raise ModuleNotFoundError("The package 'ansys-platform-instancemanagement' is required to use this function.")

    pim = pypim.connect()
    instance = pim.create_instance(product_name="speos", product_version=version)
    instance.wait_for_ready()
    channel = instance.build_grpc_channel()
    return Speos(channel=channel, remote_instance=instance)
