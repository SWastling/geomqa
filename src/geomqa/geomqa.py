"""Measure Geometric Distortion of MRI of Large Field-of-View Cylindrical Phantom"""

import argparse
import pathlib
import re
import subprocess as sp
import sys

import importlib_metadata as metadata
import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np

import geomqa.config as config
import geomqa.vercheck as vercheck

try:
    __version__ = metadata.version("geomqa")
except metadata.PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"


def remove_niigz(string):
    """
    remove the .nii.gz from the end of a filename

    :param string: string possibly including nii or nii.gz suffix
    :type string: str
    :return: string without .nii.gz suffix
    :rtype: str
    """

    string = re.sub(r"\.nii.gz", "", string, re.I)
    string = re.sub(r"\.nii", "", string, re.I)
    return string


def contour(b_fp, c_fp, fig_fp):

    """
    Create a plot showing a central sagittal, coronal and axial slice through
    a base image with a contour plot overlay

    :param b_fp: Filepath of base image
    :type b_fp: nib.nifti1.Nifti1Image
    :param c_fp: Filepath of contour image
    :type c_fp: nib.nifti1.Nifti1Image
    :param fig_fp:
    :type fig_fp: pathlib.Path

    The resulting plot has the following arrangement on an A4 page:

            Figure Title

    ^ +---------+   ^ +---------+
    | |         |   | |         |
      |   Sag   |     |   Cor   |
    S |    0    |   S |    1    |
      |         |     |         |
      |         |     |         |
      +---------+     +---------+
           A  -->     <--  R
    ^ +---------+
    | |         |
      |  Axial  |
    A |    2    |     comment str
      |         |
      |         |
      +---------+
      <--  R

    """

    # load and transform to canonical orientation
    b_nii = nib.funcs.as_closest_canonical(nib.load(b_fp))
    c_nii = nib.funcs.as_closest_canonical(nib.load(c_fp))

    # load the transformed image data
    b = b_nii.get_fdata()
    c = c_nii.get_fdata()

    # extract image parameters
    vox_sizes = b_nii.header.get_zooms()
    clim = np.percentile(b, (1.0, 99.0))

    # set up the figure
    fig, axs = plt.subplots(2, 2)
    fig.set_size_inches((8.27, 11.70))  # A4

    fig_title = "Distortion of %s" % b_fp.name
    fig.suptitle(fig_title, fontweight="bold", fontsize=14)
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])

    # set the contour plot values and associated colours
    cp_cols = ["gray"] + ["g"] * 2 + ["orange"] + ["r"] * 4 + ["purple"] * 3
    cp_vals = [0.1, 0.5, 1.0, 1.5, 2, 3, 4, 5, 10, 15, 20]

    # lists containing properties for [sagittal, coronal, axial] plots
    axes_list = [axs[0, 0], axs[0, 1], axs[1, 0]]
    aspect_ratios = [
        vox_sizes[2] / vox_sizes[1],
        vox_sizes[2] / vox_sizes[0],
        vox_sizes[1] / vox_sizes[0],
    ]
    axis_labels = ["SAIP", "SRIL", "ARPL"]
    base_slices = [
        b[b.shape[0] // 2, :, :].T,
        b[:, b.shape[1] // 2, :].T,
        b[:, :, b.shape[2] // 2].T,
    ]
    contour_slices = [
        c[c.shape[0] // 2, :, :].T,
        c[:, c.shape[1] // 2, :].T,
        c[:, :, c.shape[2] // 2].T,
    ]
    sizes = list(b.shape)

    # loop over the three axes sagittal, coronal then axial
    for ax, xax, yax, aspect_ratio, axis_label, base_slice, contour_slice in zip(
        axes_list,
        [1, 0, 0],
        [2, 2, 1],
        aspect_ratios,
        axis_labels,
        base_slices,
        contour_slices,
    ):

        # plot the base image
        ax.imshow(
            base_slice,
            vmin=clim[0],
            vmax=clim[1],
            aspect=1,
            cmap="gray",
            interpolation="nearest",
            origin="lower",
        )

        # add the contour overlay
        cp = ax.contour(contour_slice, cp_vals, colors=cp_cols, origin="lower")
        plt.clabel(cp, inline=1, fontsize=10, fmt="%1.1f")

        # add axis orientation labels
        lims = [0, sizes[xax], 0, sizes[yax]]
        poss = [
            [lims[1] / 2.0, lims[3]],
            [(1 + 0.01) * lims[1], lims[3] / 2.0],
            [lims[1] / 2.0, 0 - 0.01 * lims[3]],
            [lims[0] - 0.01 * lims[1], lims[3] / 2.0],
        ]
        anchors = [
            ["center", "bottom"],
            ["left", "center"],
            ["center", "top"],
            ["right", "center"],
        ]
        for pos, anchor, lab in zip(poss, anchors, axis_label):
            ax.text(
                pos[0],
                pos[1],
                lab,
                horizontalalignment=anchor[0],
                verticalalignment=anchor[1],
            )

        # set the size and shape of the axes and turn off ticks
        ax.axis(lims)
        ax.set_aspect(aspect_ratio)
        ax.set_frame_on(False)
        ax.axes.get_yaxis().set_visible(False)
        ax.axes.get_xaxis().set_visible(False)

    # ensure the axs[1, 1] is the same size and shape as axs[1, 0]
    axs[1, 1].axis(lims)
    axs[1, 1].set_aspect(aspect_ratio)
    axs[1, 1].get_yaxis().set_visible(False)
    axs[1, 1].get_xaxis().set_visible(False)
    axs[1, 1].set_frame_on(False)
    axs[1, 1].text(
        0.5,
        0.5,
        "The contours show the distortion of the MRI\n"
        "in mm overlayed on the MRI. Distortion is\n"
        "quantified as the magnitude of the\n"
        "displacement field from the non-rigid\n"
        "registration of the MRI to a CT image of\n"
        "the phantom.\n\n If no contours are shown\n"
        "distortions are <0.1 mm.",
        transform=axs[1, 1].transAxes,
        style="italic",
        ha="center",
        va="center",
        bbox={"facecolor": "gray", "alpha": 0.5, "boxstyle": "round"},
    )

    plt.savefig(fig_fp, orientation="portrait")


def main():
    parser = argparse.ArgumentParser(
        description="Measure Geometric Distortion of Magnetic Resonance Images "
        "of Large Field-of-View Cylindrical Phantom"
    )

    parser.add_argument(
        "n", help="list of MRI NIfTI files", nargs="+", type=pathlib.Path
    )
    parser.add_argument("o", help="Results directory", type=pathlib.Path)
    parser.add_argument(
        "-niftyreg",
        default=pathlib.Path(config.DEFAULT_NIFTYREG),
        help="directory containing niftyreg programs (default: %(default)s)",
        type=pathlib.Path,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--any-version",
        dest="any_version",
        default=False,
        action="store_true",
        help="don't abort if version checks of external software fail",
    )

    if len(sys.argv) == 1:
        sys.argv.append("-h")

    args = parser.parse_args()

    print("* checking versions of external software")
    vercheck.check_lib_ver(
        "MRtrix", vercheck.get_mrtrix_ver(), config.MRTRIX_VERSIONS, args.any_version
    )

    niftyreg_dp = args.niftyreg
    vercheck.check_lib_ver(
        "niftyreg",
        vercheck.get_niftyreg_ver(niftyreg_dp),
        config.NIFTYREG_VERSIONS,
        args.any_version,
    )

    # paths to niftyreg commands
    reg_aladin_fp = niftyreg_dp / "reg_aladin"
    reg_f3d_fp = niftyreg_dp / "reg_f3d"
    reg_resample_fp = niftyreg_dp / "reg_resample"
    reg_transform_fp = niftyreg_dp / "reg_transform"

    ct_fp = pathlib.Path(__file__).resolve().parent / "ct.nii.gz"
    ctmask_fp = pathlib.Path(__file__).resolve().parent / "ctmask.nii.gz"

    # directory to store intermediate images e.g. result of rigid registration
    out_dp = args.o.resolve()

    for mri_file in sorted(args.n):
        mri_fp = mri_file.resolve()

        print("* processing %s" % mri_fp.name)
        results_dp = out_dp / remove_niigz(mri_fp.name)
        results_dp.mkdir(parents=True, exist_ok=True)

        # create symlink to CT in results directory for visual check of registration
        ct_lnk_fp = results_dp / "ct.nii.gz"
        ct_lnk_fp.symlink_to(ct_fp)

        # filepaths
        rigid_fp = results_dp / "mr2ct_rigid.nii.gz"
        affine_fp = results_dp / "mr2ct_rigid.aff"
        nonrigid_fp = results_dp / "mr2ct_nonrigid.nii.gz"
        cpp_fp = results_dp / "mr2ct_cpp.nii.gz"
        disp_field_fp = results_dp / "displ_field_ct.nii.gz"
        mag_displ_field_ct_fp = results_dp / "mag_displ_field_ct.nii.gz"
        mr2ct_deformation_fp = results_dp / "mr2ct_deformation.nii.gz"
        ct2mr_deformation_fp = results_dp / "ct2mr_deformation.nii.gz"
        mag_displ_field_mri_fp = results_dp / "mag_displ_field_mri.nii.gz"
        fig_fp = out_dp / (remove_niigz(mri_fp.name) + "_distortion_results.pdf")

        # generate commands
        rigid_cmd = [
            reg_aladin_fp,
            "-ref",
            ct_fp,
            "-flo",
            mri_fp,
            "-rmask",
            ctmask_fp,
            "-res",
            rigid_fp,
            "-rigOnly",
            "-aff",
            affine_fp,
        ]

        nonrigid_cmd = [
            reg_f3d_fp,
            "-ref",
            ct_fp,
            "-flo",
            rigid_fp,
            "-rmask",
            ctmask_fp,
            "-res",
            nonrigid_fp,
            "-cpp",
            cpp_fp,
            "-be",
            "0.005",
            "-maxit",
            "500",
            "-sx",
            "15",
            "-ln",
            "4",
            "-lp",
            "2",
        ]

        mrview_cmd = [
            "mrview",
            ct_fp,
            "-voxel",
            "271,257,134",
            "-mode",
            "2",
            "-intensity_range",
            "1000,1500",
            "-overlay.load",
            rigid_fp,
            "-overlay.opacity",
            "0.6",
            "-overlay.colour",
            "1,0,0",
            "-overlay.intensity",
            "200,4095",
            "-overlay.threshold_min",
            "200",
            "-overlay.load",
            nonrigid_fp,
            "-overlay.opacity",
            "0.6",
            "-overlay.colour",
            "0,0,1",
            "-overlay.intensity",
            "200,4095",
            "-overlay.threshold_min",
            "200",
        ]

        disp_cmd = [reg_transform_fp, "-ref", ct_fp, "-disp", cpp_fp, disp_field_fp]

        mag_displ_field_cmd = [
            "mrmath",
            "-axis",
            "4",
            disp_field_fp,
            "norm",
            mag_displ_field_ct_fp,
        ]

        compose_cmd = [
            reg_transform_fp,
            "-ref",
            ct_fp,
            "-comp",
            affine_fp,
            cpp_fp,
            mr2ct_deformation_fp,
        ]

        invert_cmd = [
            reg_transform_fp,
            "-ref",
            ct_fp,
            "-invNrr",
            mr2ct_deformation_fp,
            mri_fp,
            ct2mr_deformation_fp,
        ]

        resample_cmd = [
            reg_resample_fp,
            "-ref",
            mri_fp,
            "-flo",
            mag_displ_field_ct_fp,
            "-trans",
            ct2mr_deformation_fp,
            "-res",
            mag_displ_field_mri_fp,
            "-inter",
            "1",
        ]

        # run commands
        print("** registering MRI to CT")
        print("*** rigid registration with reg_aladin")
        sp.run(rigid_cmd, check=True)

        print("*** non-rigid registration with reg_f3d")
        sp.run(nonrigid_cmd, check=True)

        print("*** displaying registered images with FSLeyes")
        sp.Popen(mrview_cmd, stderr=sp.PIPE, stdout=sp.PIPE)

        print("** calculating displacement field in CT-space with reg_transform")
        sp.run(disp_cmd, check=True)

        print("** calculating root mean square of displacement field in CT-space")
        sp.run(mag_displ_field_cmd, check=True)

        print("** transforming results into MRI space")
        print("*** composing mr2ct_rigid.aff and mr2ct_cpp.nii.gz with reg_transform")
        sp.run(compose_cmd, check=True)

        print("*** inverting composed transformation with reg_transform")
        sp.run(invert_cmd, check=True)

        print("*** resampling into MRI space with reg_resample")
        sp.run(resample_cmd, check=True)

        print("** plotting results")
        contour(mri_fp, mag_displ_field_mri_fp, fig_fp)


if __name__ == "__main__":  # pragma: no cover
    main()
