import pathlib

import nibabel as nib
import numpy as np
import pytest

import geomqa.geomqa as geomqa

THIS_DIR = pathlib.Path(__file__).resolve().parent
TEST_DATA_DIR = THIS_DIR / "test_data"
SCRIPT_NAME = "geomqa"
SCRIPT_USAGE = f"usage: {SCRIPT_NAME} [-h]"


def perror(r, t):
    """
    calculate the percentage error between two arrays; a reference and
    a test

    Based on test used in FSL Evaluation and Example Data Suite (FEEDS)

    :param r: reference
    :type r: np.ndarray
    :param t: test
    :type t: np.ndarray
    return: percentage error of r and t
    type: float
    """

    return 100.0 * np.sqrt(np.mean(np.square(r - t)) / np.mean(np.square(r)))


@pytest.mark.parametrize(
    "string, expected_output",
    [("a", "a"), ("a.b", "a.b"), ("a.nii", "a"), ("a.nii.gz", "a")],
)
def test_remove_niigz(string, expected_output):
    assert geomqa.remove_niigz(string) == expected_output


def test_contour(tmp_path):

    fig_fp = tmp_path / "contour.pdf"
    data_dir = TEST_DATA_DIR / "qa_example"
    qa_nii = data_dir / "input" / "mri.nii.gz"
    ref_mag_displ_field_mri_fp = data_dir / "input" / "contour.nii.gz"
    geomqa.contour(qa_nii, ref_mag_displ_field_mri_fp, fig_fp)
    assert fig_fp.is_file()


def test_prints_help_1(script_runner):
    result = script_runner.run(SCRIPT_NAME)
    assert result.success
    assert result.stdout.startswith(SCRIPT_USAGE)


def test_prints_help_2(script_runner):
    result = script_runner.run(SCRIPT_NAME, "-h")
    assert result.success
    assert result.stdout.startswith(SCRIPT_USAGE)


def test_prints_help_for_invalid_option(script_runner):
    result = script_runner.run(SCRIPT_NAME, "-!")
    assert not result.success
    assert result.stderr.startswith(SCRIPT_USAGE)


def test_geomqa(tmp_path, script_runner):

    pthresh = 1.0

    data_dir = TEST_DATA_DIR / "qa_example"
    input_dir = data_dir / "input"
    qa_nii = input_dir / "mri.nii.gz"

    # Reference data to check against

    # Use mrconvert to extract slices from volumes to create test data
    # e.g. mrconvert displ_field_ct.nii.gz -coord 2 134 displ_field_ct_ax_134.nii.gz

    ref_results_dir = data_dir / "output" / "mri"
    ref_rigid_aff_fp = ref_results_dir / "mr2ct_rigid.aff"
    ref_rigid_fp = ref_results_dir / "mr2ct_rigid_ax_134.nii.gz"
    ref_nonrigid_fp = ref_results_dir / "mr2ct_nonrigid_ax_134.nii.gz"
    ref_cpp_fp = ref_results_dir / "mr2ct_cpp.nii.gz"
    ref_disp_field_fp = ref_results_dir / "displ_field_ct_ax_134.nii.gz"
    ref_mag_displ_field_ct_fp = ref_results_dir / "mag_displ_field_ct_ax_134.nii.gz"
    ref_mr2ct_deformation_fp = ref_results_dir / "mr2ct_deformation_ax_134.nii.gz"
    ref_ct2mr_deformation_fp = ref_results_dir / "ct2mr_deformation_ax_87.nii.gz"
    ref_mag_displ_field_mri_fp = ref_results_dir / "mag_displ_field_mri_ax_87.nii.gz"

    results_dir = tmp_path / "mri"
    ct_fp = results_dir / "ct.nii.gz"
    rigid_aff_fp = results_dir / "mr2ct_rigid.aff"
    rigid_fp = results_dir / "mr2ct_rigid.nii.gz"
    nonrigid_fp = results_dir / "mr2ct_nonrigid.nii.gz"
    cpp_fp = results_dir / "mr2ct_cpp.nii.gz"
    disp_field_fp = results_dir / "displ_field_ct.nii.gz"
    mag_displ_field_ct_fp = results_dir / "mag_displ_field_ct.nii.gz"
    mr2ct_deformation_fp = results_dir / "mr2ct_deformation.nii.gz"
    ct2mr_deformation_fp = results_dir / "ct2mr_deformation.nii.gz"
    mag_displ_field_mri_fp = results_dir / "mag_displ_field_mri.nii.gz"
    fig_fp = tmp_path / "mri_distortion_results.pdf"

    result = script_runner.run(SCRIPT_NAME, str(qa_nii), str(tmp_path))
    assert result.success

    assert results_dir.is_dir()
    assert ct_fp.is_symlink()
    assert rigid_aff_fp.is_file()
    assert np.allclose(np.loadtxt(ref_rigid_aff_fp), np.loadtxt(rigid_aff_fp))

    assert rigid_fp.is_file()
    ref_rigid_nii = nib.load(ref_rigid_fp)
    rigid_nii = nib.load(rigid_fp)
    assert perror(ref_rigid_nii.get_fdata(), rigid_nii.get_fdata()[:, :, 134]) < pthresh

    assert nonrigid_fp.is_file()
    ref_nonrigid_nii = nib.load(ref_nonrigid_fp)
    nonrigid_nii = nib.load(nonrigid_fp)
    assert (
        perror(ref_nonrigid_nii.get_fdata(), nonrigid_nii.get_fdata()[:, :, 134])
        < pthresh
    )

    assert cpp_fp.is_file()
    ref_cpp_nii = nib.load(ref_cpp_fp)
    cpp_nii = nib.load(cpp_fp)
    assert perror(ref_cpp_nii.get_fdata(), cpp_nii.get_fdata()) < pthresh

    assert disp_field_fp.is_file()
    ref_disp_field_nii = nib.load(ref_disp_field_fp)
    disp_field_nii = nib.load(disp_field_fp)
    assert (
        perror(
            np.squeeze(ref_disp_field_nii.get_fdata()),
            np.squeeze(disp_field_nii.get_fdata()[:, :, 134, :, :]),
        )
        < pthresh
    )

    assert mag_displ_field_ct_fp.is_file()
    ref_mag_displ_field_ct_nii = nib.load(ref_mag_displ_field_ct_fp)
    mag_displ_field_ct_nii = nib.load(mag_displ_field_ct_fp)
    assert (
        perror(
            np.squeeze(ref_mag_displ_field_ct_nii.get_fdata()),
            mag_displ_field_ct_nii.get_fdata()[:, :, 134],
        )
        < pthresh
    )

    assert mr2ct_deformation_fp.is_file()
    ref_mr2ct_deformation_nii = nib.load(ref_mr2ct_deformation_fp)
    mr2ct_deformation_nii = nib.load(mr2ct_deformation_fp)
    assert (
        perror(
            np.squeeze(ref_mr2ct_deformation_nii.get_fdata()),
            np.squeeze(mr2ct_deformation_nii.get_fdata()[:, :, 134, :, :]),
        )
        < pthresh
    )

    assert ct2mr_deformation_fp.is_file()
    ref_ct2mr_deformation_nii = nib.load(ref_ct2mr_deformation_fp)
    ct2mr_deformation_nii = nib.load(ct2mr_deformation_fp)
    assert (
        perror(
            np.squeeze(ref_ct2mr_deformation_nii.get_fdata()),
            np.squeeze(ct2mr_deformation_nii.get_fdata()[:, :, 87, :, :]),
        )
        < pthresh
    )

    assert mag_displ_field_mri_fp.is_file()
    ref_mag_displ_field_mri_nii = nib.load(ref_mag_displ_field_mri_fp)
    mag_displ_field_mri_nii = nib.load(mag_displ_field_mri_fp)
    assert (
        perror(
            np.squeeze(ref_mag_displ_field_mri_nii.get_fdata()),
            mag_displ_field_mri_nii.get_fdata()[:, :, 87],
        )
        < pthresh
    )

    assert fig_fp.is_file()
