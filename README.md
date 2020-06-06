![logo](docs/images/logo.png)

# Citation
Click on the badge below to cite `biopeaks` in a format of your choice.

[![DOI](https://www.zenodo.org/badge/172897525.svg)](https://www.zenodo.org/badge/latestdoi/172897525)


# General Information

`biopeaks` is a graphical user interface for feature extraction from electrocardiogram (ECG), photoplethysmogram (PPG) and breathing biosignals.
It processes these biosignals semi-automatically with sensible defaults and offers the following functionality:

* processes files in the open biosignal formats [EDF](https://en.wikipedia.org/wiki/European_Data_Format)
as well as [OpenSignals](https://bitalino.com/en/software)
* interactive biosignal visualization
* biosignal segmentation
* benchmarked, automatic extrema detection (R-peaks in ECG, systolic peaks in PPG, exhalation troughs and inhalation
peaks in breathing signals)
* automatic state-of-the-art [artifact correction](https://www.tandfonline.com/doi/full/10.1080/03091902.2019.1640306)
 for ECG and PPG extrema
* manual editing of extrema (useful in case of poor biosignal quality)
* calculation of instantaneous (heart- or breathing-) rate and period, as well as
breathing amplitude
* batch processing

Visit the [documentation]() for additional information.


## Installation

### Instructions for users without a Python installation
If you don't have experience with installing Python packages and/or if you
aren't sure if you have Python on your computer start by setting up Python.
Go to https://docs.conda.io/en/latest/miniconda.html and install the latest 
miniconda distribution for your operating system.
Follow these [instructions](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)
in case you're unsure about the installation. Once you've installed miniconda, open the
[Anaconda Prompt](https://docs.anaconda.com/anaconda/user-guide/getting-started/)
and run the following commands (hit enter once you've typed each of the lines below and wait for 
the commands to be executed):

```
conda config --add channels conda-forge
conda config --set channel_priority strict 
conda create -y -n biopeaks python=3.7 scipy numpy pyside2 matplotlib pandas
conda activate biopeaks
pip install biopeaks
```

After the successful installation, open the application by typing
```
biopeaks
```
Note that every time you open the Anaconda Prompt, you need to activate the
biopeaks environment before starting the application:
```
conda activate biopeaks
biopeaks
```

### Instructions for users who already have a Python installation

#### dependencies
Make sure that the following requirements are met for your Python environment:

python >= 3.7\
pyside2 >= 5.13.2\
qt >= 5.12.5\
numpy >= 1.18.1\
scipy >= 1.4.1\
pandas >= 0.25.3\
matplotlib >= 3.2.1

Once you have all the dependencies, install `biopeaks` with

```
pip install biopeaks
```

In order to manage the dependencies, it is highly recommended to install
`biopeaks` into an isolated environment (e.g., conda, or virtualenv).