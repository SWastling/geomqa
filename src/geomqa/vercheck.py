import subprocess as sp
import sys


def get_mrtrix_ver():
    """
    Determine mrtrix version installed on system

    :return: version of mrtrix
    :rtype: str
    """

    try:
        sp_out = sp.run(
            ["mrinfo", "-version"], capture_output=True, text=True, check=True
        )
    except FileNotFoundError:
        sys.stderr.write(
            "ERROR: mrinfo (an mrtrix command) used to check "
            "version is not in your path, exiting\n"
        )
        sys.exit(1)

    mrinfo_out = sp_out.stdout.strip()
    mrinfo_out_first_line = mrinfo_out.splitlines()[0]

    # First line should be of the form == mrinfo 3.0.1-26-g0f28beae ==
    return mrinfo_out_first_line.split(" ")[2]


def get_niftyreg_ver(niftyreg_dp):
    """
    Determine niftyreg version

    :param niftyreg_dp: path to niftyreg directory
    :type niftyreg_dp: pathlib.Path
    :return: version of niftyreg
    :rtype: str
    """
    if not niftyreg_dp.is_dir():
        raise FileNotFoundError("niftyreg not found")

    reg_aladin_fp = niftyreg_dp / "reg_aladin"
    sp_out = sp.run([reg_aladin_fp, "-version"], capture_output=True, text=True)

    return sp_out.stdout.strip()


def check_lib_ver(lib_name, lib_ver, expected_lib_ver_list, any_ver):
    """
    Compare the actual library version to the expected version

    :param lib_name: name of library
    :type lib_name: str
    :param lib_ver: version of library
    :type lib_ver: str
    :param expected_lib_ver_list: expected version of library
    :type expected_lib_ver_list: list
    :param any_ver: don't abort if any_ver is True
    :rtype: bool
    """
    if lib_ver in expected_lib_ver_list:
        print("** PASS version check on %s (%s)" % (lib_name, lib_ver))
    else:
        print("** FAIL using non-validated %s version" % lib_name)
        print("*** expected %s, got %s" % (" or ".join(expected_lib_ver_list), lib_ver))

        if not any_ver:
            sys.stderr.write("** exiting\n")
            sys.exit(1)
