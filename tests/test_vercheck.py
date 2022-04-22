import os
import pathlib
from unittest import mock

import pytest

import geomqa.config as config
import geomqa.vercheck as vercheck


def test_get_mrtrix_ver(capsys):
    # Test what happens if mrtrix is in path
    assert vercheck.get_mrtrix_ver() in config.MRTRIX_VERSIONS

    # Test what happens if mrtrix not in path
    with mock.patch.dict(os.environ, {"PATH": ""}):
        with pytest.raises(SystemExit) as pytest_wrapped_e:
            vercheck.get_mrtrix_ver()

        assert pytest_wrapped_e.type == SystemExit
        assert pytest_wrapped_e.value.code == 1
        captured = capsys.readouterr()
        assert captured.out == ""
        assert (
            captured.err == "ERROR: mrinfo (an mrtrix command) used to "
            "check version is not in your path, exiting\n"
        )


def test_get_niftyreg_ver():
    niftyreg_dp = pathlib.Path(config.DEFAULT_NIFTYREG)
    assert vercheck.get_niftyreg_ver(niftyreg_dp) in config.NIFTYREG_VERSIONS


def test_get_niftyreg_ver_error():
    not_dir = pathlib.Path("a")
    with pytest.raises(FileNotFoundError) as pytest_wrapped_e:
        vercheck.get_niftyreg_ver(not_dir)

    assert pytest_wrapped_e.value.args[0] == "niftyreg not found"


def test_check_lib_ver(capsys):

    # Library check fail and exit
    with pytest.raises(SystemExit) as pytest_wrapped_e:
        vercheck.check_lib_ver("lib_a", "2.0.0", ["1.0.0", "1.0.1"], False)

    assert pytest_wrapped_e.type == SystemExit
    assert pytest_wrapped_e.value.code == 1
    captured = capsys.readouterr()
    assert (
        captured.out == "** FAIL using non-validated lib_a version\n*** "
        "expected 1.0.0 or 1.0.1, got 2.0.0\n"
    )
    assert captured.err == "** exiting\n"

    # Library check fail and don't exit
    vercheck.check_lib_ver("lib_a", "2.0.0", ["1.0.0", "1.0.1"], True)
    captured = capsys.readouterr()
    assert (
        captured.out == "** FAIL using non-validated lib_a version\n*** "
        "expected 1.0.0 or 1.0.1, got 2.0.0\n"
    )

    # Library check pass and don't exit
    vercheck.check_lib_ver("lib_a", "2.0.0", ["1.0.0", "2.0.0"], True)
    captured = capsys.readouterr()
    assert captured.out == "** PASS version check on lib_a (2.0.0)\n"
