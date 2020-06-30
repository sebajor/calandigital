# calandigital

Helper package to ease the development of CASPER's ROACH1 and ROACH2 scripts.

It is the spiritual successor of the [roach_tools package](https://github.com/FrancoCalan/roach_tools), made to be simpler and
more user friendly.

calandigital features can be divided in two: 

1. helper functions to ease the development of new scripts.
2. out-of-the-box scripts of commonly used operations in ROACH.

## Installation
calandigital works in python2.7 only, so make sure you are using this version in your system or your virtual environment.

Installation instruction only for Linux-based system provided:

0. It is recommended to use this software in a [python virtual enviroment](https://virtualenv.pypa.io/en/stable/)
1. Install these packages (Ubuntu command): `sudo apt install python-dev python-tk g++`
2. `git clone` or download/unzip repository
3. Install repository dependencies, in calandigital root folder: `pip install -r REQUIREMENTS` (install pip if necessary)
4. Install repository: `python setup.py install`

## Helper Functions
After installation the helper functions can be called from a python script if the calandigital package is imported. These are the currently implemented functions in the calandigital package:

- [x] `initialize_roach`: starts roach communication and loads boffile.
- [x] `read_snapshots`: reads data of a list of snapshots blocks.
- [x] `read_data`: reads data form a bram given the bram width and depth.
- [x] `read_interleave_data`: reads data of a list of brams and then interleaves the data (used for wideband spectrometers).
- [x] `read_deinterleave_data`: reads data of a bram and then deinterleaves the data (used for small spectrometers).
- [x] `write_interleaved_data`: deinterleaves an array of data and writes it into a list of brams.
- [x] `read_dram_data`: reads data form a DRAM given the bram width and depth.
- [x] `scale_and_dBFS_specdata`: scales data by the accumulation length and converts it to dBFS (dB Full Scale).
- [x] `float2fixed`: converts data from floating point to fixed point, with optional overflow warnings.

For example, if we want to make a script to initialize the ROACH we can write:
```python
import calandigital as cd
roach = cd.initialize_roach(<ROACH_IP>, boffile=<BOFFILE>, upload=True)
```
## Scripts
After installation, scripts can be run from terminal. For more information use `<script_name> -h`. These are the currently implemented scripts:

- [x] `initialize_roach.py`: starts roach communication and loads boffile.
- [x] `plot_snapshots.py`: plot snapshot data from a model snapshot blocks.
- [x] `plot_spectra.py`: plot spectra data from a model spectrometer model.
- [x] `calibrate_adc5g.py`: calibrate ADC5G ADCs from a ROACH2.
- [x] `synchronize_adc5g.py`: synchronize ADC5G ADCs from a ROACH2.
- [x] `set_valon5007.py`: set power and frequency of a [Valon 5007 synthesizer](http://valontechnology.com/5007/5007.htm) (usually used for ROACH clock).

## Additional Subpackages
Calandigital also provides some subpackages for aditional functionalities (check subpackages READMEs for more information):
- [x] `adc5g_devel`: a strip down version of NRAO's [adc5g_devel](https://github.com/nrao/adc5g_devel). Used in the `calibrate_adc5g.py` script.
- [x] `qdr`: used to calibrate ROACH2's QDR memories. Extracted from [CASPER mlib_devel repo](https://github.com/casper-astro/mlib_devel/tree/roach2)
- [x] `dummy_roach`: used to simulate a ROACH connection.

## External Links
* [simulink_models](https://github.com/FrancoCalan/simulink_models): Sister repository with simulink models, compiled .bof files, and script files for various examples and projects.
* [Calan Digital Wiki](https://sites.google.com/site/calandigital/): Wiki site with ROACH tutorials and information about our (Milimeter-Wave Laboratory) digital back-end projects.
* [CASPER Site](https://casper.berkeley.edu/): Oficial CASPER site, the developers of the ROACH and other digital platforms for radioastronomy.

## Author
Franco Curotto

Millimeter-wave Laboratory, Department of Astronomy, University of Chile

http://www.das.uchile.cl/lab_mwl
