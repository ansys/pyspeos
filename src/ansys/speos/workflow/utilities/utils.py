import os
import subprocess


def start_server(version: int = 241, msg_size_mb: int = 4) -> None:
    """
    start a SpeosRPC Server.

    Parameters
    ----------
    version: int
        version number
    msg_size_mb: int
        message size in MB
    """
    stdout_file = os.path.join(r"D:\Temp\\", "stdout.txt")
    stderr_file = os.path.join(r"D:\Temp\\", "stderr.txt")
    command = [
        r"SpeosRPC_Server.exe",
        r"-m",
        r"{}".format(msg_size_mb * 1024 * 1024),
    ]
    cwd = os.path.join(os.path.dirname(os.environ["ANSYS{}_DIR".format(version)]), "Optical Products", "SPEOS_HPC")
    with open(stdout_file, "wb") as out, open(stderr_file, "wb") as err:
        subprocess.Popen(command, shell=True, stdout=out, stderr=err, cwd=cwd)
