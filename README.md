# geomqa

## Synopsis
Measure Geometric Distortion of Magnetic Resonance Images of Large Field-of-View 
Cylindrical Phantom

## Usage

```bash
geomqa [options] n o
```
- `n`: List of MRI NIfTI files
- `o`: Results directory

## Options
- `-h`: display help message, and quit
- `-niftyreg`: directory containing niftyreg programs
- `--version`: display version and exit
- `--any-version`: don't abort if version checks fail 

## Description

### Data Acquisition
The large field-of-view QA test is intended as an integration test of the 
geometric accuracy of final images with realistic fields-of-view at, 
or displaced from, the magnetic iso-centre. 

Images should be acquired using identical parameters to those used for 
surgical navigation and planning on for example:
- BrainLAB Buzz (i.e. for open craniotomy, biopsy and functional neurosurgery)
- Medtronic StealthStation
- Gamma Knife stereotactic radiosurgery
 
_Given that geometric distortion depends on acquisition parameters the results 
from one acquisition cannot be applied directly to other sequences/acquisition 
parameters._ 

### Data Analysis
1. The MR image is:
   1. rigid-aligned to a CT image of the same phantom with `reg_aladin` resulting in
an MR image in CT space `mr2ct_rigid.nii.gz` and the rigid-body transformation 
needed to achieve this `mr2ct_rigid.aff`
   2. non rigid-aligned to the CT with `reg_f3d` with a 15mm control point spacing
resulting in an MR image warped into CT space `mr2ct_nonrigid.nii.gz` and the 
rigid-body control point grid need to achieve this `mr2ct_cpp.nii.gz`

    _Both the rigid and non-rigid registration steps can fail and the results should
    by checked visually in `mrview`_ 

2. The displacement field `displ_field_ct.nii.gz` is calculated from the control 
point grid `mr2ct_cpp.nii.gz` with `reg_transform`
  
3. The distortion, measured in mm `mag_displ_field_ct.nii.gz`, is calculated as the magnitude
 of the displacement field using `mrmath`

4. The distortion is transformed into MRI space, `mag_displ_field_mri.nii.gz`, using 
`reg_transform` and `reg_resample`

5. The distortion is saved, in a PDF, as contours plotted on a central sagittal, 
coronal and axial slice of the MR image.


## Software Requirements
- [MRtrix3](https://www.mrtrix.org/) (version 3.0.1)
- [niftyreg](https://github.com/KCL-BMEIS/niftyreg) (version 1.5.59)

The versions of `MRtrix` and  `niftyreg` are verified at runtime.

## Installing
1. Create a directory to store the package e.g.:

    ```bash
    mkdir geomqa
    ```

2. Create a new virtual environment in which to install `geomqa`:

    ```bash
    python3 -m venv geomqa-env
    ```
   
3. Activate the virtual environment:

    ```bash
    source geomqa-env/bin/activate
    ```

4. Upgrade `pip` and `build`:

    ```bash
    pip install --upgrade pip
    pip install --upgrade build
    ```

5. Install using `pip`:
    ```bash
    pip install git+https://github.com/SWastling/geomqa.git
    ```

## License
See [MIT license](./LICENSE)

## Authors and Acknowledgements
Written by [Dr Stephen Wastling](mailto:stephen.wastling@nhs.net) 

The original version of the code was written by Dr Mark White and then updated 
by Dr Sjoerd Vos whilst they were based at the National Hospital for 
Neurology and Neurosurgery.
