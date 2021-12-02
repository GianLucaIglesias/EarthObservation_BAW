import subprocess
import sys
import platform

from pathlib import Path, WindowsPath

SNAP_BIN = Path(r"C:\Program Files\snap\bin")
SNAP_EXE = Path(r"snap64.exe")


def get_snap_exe():
    """ Function returning the snap exe referring to the machine on which SNAP is supposed to be installed. """
    machine_OS, machine_type = platform.system(), platform.machine()

    if not machine_OS == "Windows":
        raise ValueError("The function is only tested for the SNAP standard installation on Windows.")
    if machine_type.endswith('64'):
        return 'snap64.exe'
    else:
        raise ValueError("The function was only tested for x64 bit systems.")


def snap_exists(snap_bin=None):  # may be extended by analysing the machine on which python is running and see whether the versions match
    """ Functions testing whether a SNAP Toolbox distribution is accessible on a windows machine. """
    snap_exe = get_snap_exe()

    if snap_bin:
        snap_app = Path(snap_bin) / Path(snap_exe)
    else:
        snap_app = Path(SNAP_BIN) / Path(snap_exe)

    if snap_app.exists():
        return snap_app
    else:
        print(f"No SNAP executable found where expected: {snap_app}")
        return False

#  DOESN'T WORK, DUE TO CONFUSION WITH THE SHELL SUBPROCESS COMMAND:
#   need to inidcate directory to snap bin and then exectue: snap64.exe --nosplash --nogui --modules --help

# def show_all_snap_options(snap_bin=SNAP_BIN, snap_exe=SNAP_EXE):
#     process = subprocess.Popen(["snap64.exe", "--nosplash", "--nogui", "--modules", "--help"],
#                                cwd=r"C:\Program Files\snap\bin", shell=True)
#     out, err = process.communicate()


def show_help_on_gpt(operator='all'):
    cmd_list = ["gpt"]
    if not operator == 'all':
        cmd_list.append(operator)
    cmd_list.append('-h')

    process = subprocess.Popen(cmd_list, shell=True)
    process.wait()

    if not process.returncode == 0:
        print(f"Wuuuups, something went wrong! ")

