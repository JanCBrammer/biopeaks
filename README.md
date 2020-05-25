![logo](biopeaks/images/logo.png)

+ [General Information](#general-information)
+ [Citation](#citation)
+ [User Guide](#user-guide)
+ [Contributor Guide](#contributor-guide)
+ [Tests](#tests)
+ [Changelog](#changelog)
+ [Further Resources](#further-resources)


# General Information

`biopeaks` is a graphical user interface for electrocardiogram (ECG), photoplethysmogram (PPG) and breathing biosignals.
It processes these biosignals semi-automatically with sensible defaults and features the following
functionality:

* works with files in the open biosignal formats [EDF](https://en.wikipedia.org/wiki/European_Data_Format)
as well as [OpenSignals](https://bitalino.com/en/software)
* interactive biosignal visualization
* biosignal segmentation
* automatic extrema detection (R-peaks in ECG, systolic peaks in PPG, exhalation troughs and inhalation
peaks in breathing signals)
* automatic state-of-the-art [artifact correction](https://www.tandfonline.com/doi/full/10.1080/03091902.2019.1640306)
 for ECG and PPG extrema
* manual editing of extrema (useful in case of poor biosignal quality)
* calculation of instantaneous (heart- or breathing-) rate and period, as well as
breathing amplitude
* batch processing


# Citation
Click on the badge below to cite `biopeaks` in a format of your choice.


[![DOI](https://www.zenodo.org/badge/172897525.svg)](https://www.zenodo.org/badge/latestdoi/172897525)


# User Guide

## Installation
Note that currently, `biopeaks` has been built and tested on Windows. It should
run on Linux and macOS as well.


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


## Layout of the interface

![blank](biopeaks/images/screenshot_blank.png)

In the **menubar**, you can find three sections: **_biosignal_**, **_peaks_**,
and **_statistics_**.
These contain methods for the interaction with your biosignals. On the left 
side, there's
an **optionspanel** that allows you to customize your workflow.
To the right of the **optionspanel** is the **datadisplay** which consists of 
three panels. The upper
panel contains the biosignal as well as peaks identified in the biosignal, 
while the middle panel can be used
to optionally display a marker channel. The lower panel contains any statistics 
derived from the peaks. Adjust the height of the panels by dragging the 
segmenters
between them up or down. Beneath the **optionspanel**, in the lower left
corner, you find the **displaytools**. These allow you to interact with the
biosignal. Have a
look in the [functionality section](#functionality) for details on these
elements.


## Getting started
The following work-flow is meant as an introduction to the interface. Many other
work flows are possible and might make more sense given your 
requirements. Note that `biopeaks` works with the OpenSignals text file format
as well as EDF files. However, you can analyze any data as long as you format the
data according to either the [OpenSignals convention](http://bitalino.com/datasheets/OpenSignals_File_Formats.pdf)
or the [EDF convention](https://www.edfplus.info/specs/index.html). The functions
used in the exemplary work-flow are described in detail in the [functionality section](#functionality).

### examplary workflow on a single file
Before you start, select the desired options in the **optionspanel**. Make sure
that the **_processing mode_** is set to _single file_ and
[load the biosignal](#load-biosignal) to visually check its quality using the [**displaytools**](#displaytools).
Next, you could [segment the biosignal](#segment-biosignal) based on a specific time interval
or events in the markers. Now you can [identify the peaks](#find-peaks) in the biosignal.
If the quality of the biosignal is sufficient, the peaks should be placed in the
correct locations. However, if there are noisy intervals in the biosignal, peaks might be
misplaced or not detected at all (i.e., false positives or false negatives).

![noise](biopeaks/images/screenshot_noise.png)

If this is the case you can [edit the peak locations](#edit-peaks). Once you are
confident that all the peaks are placed correctly you can [calculate statistics](#calculate-statistics).
Finally, you can [save the biosignal](#save-biosignal), [peaks](#save-peaks), and/or
[statistics](#save-statistics), depending on your requirements. If you have
segmented the biosignal it is a good idea to save it so you can reproduce the work-flow
later if necessary. Also, save the peaks if you're planning on [reloading](#load-peaks) them later
or using them for your own computations.

## Functionality

+ [load biosignal](#load-biosignal)
+ [segment biosignal](#segment-biosignal)
+ [save biosignal](#save-biosignal)
+ [find peaks](#find-peaks)
+ [save peaks](#save-peaks)
+ [load peaks](#load-peaks)
+ [edit peaks](#edit-peaks)
+ [auto-correct peaks](#auto-correct-peaks)
+ [calculate statistics](#calculate-statistics)
+ [save statistics](#save-statistics)
+ [batch processing](#batch-processing)
+ [display tools](#displaytools)


### load biosignal
Before loading the biosignal, you need to select the modality of your biosignal
in **optionspanel** -> **_processing options_** -> _modality_ (ECG for
electrocardiogram, PPG for photoplethysmogram, and RESP for breathing).
Next, under **optionspanel** -> **_channels_** you need to
specify which channel contains the _biosignal_ corresponding to your
modality. Optionally, in addition to the _biosignal_, you can select a
_marker_. This is useful if you recorded a channel
that marks interesting events such as the onset of an experimental condition,
button presses etc.. You can use the _marker_ to display any other
channel alongside your _biosignal_. Once these options are selected,
you can load the biosignal: **menubar** -> **_biosignal_** -> _load_. A
dialog will let you select the file containing the biosignal. The file format
(EDF or OpenSignals) is detected automatically. If the biosignal
has been loaded successfully it is displayed in the upper **datadisplay**. If
you selected a _marker_, it will be displayed in the middle
**datadisplay**. The current file name is always displayed in the lower right
corner of the interface.

![biosignal](biopeaks/images/screenshot_biosignal.png)

### segment biosignal
**menubar** -> **_biosignal_** -> _select segment_ opens the **segmentdialog**
on the right side of the **datadisplay**.

![segmentdialog](biopeaks/images/screenshot_segmentdialog.png)

Specify start and end of the segment in seconds either by entering values in
the respective fields, or with the mouse. For the latter option, first click on
the mouse icon in the respective field and then left-click anywhere on the
upper **datadisplay** to select a time point. To see which time point is
currently under the mouse cursor have a look at the x-coordinate
displayed in the lower right corner of the **datadisplay** (displayed when you hover 
the mouse over the upper **datadisplay**).
If you click **_preview segment_**
the segment will be displayed as a shaded region in the upper **datadisplay**
but the segment won't be cut out yet. 

![segmenthighlight](biopeaks/images/screenshot_segmenthighlight.png)

You can change the start and end values
and preview the segment until you are certain that the desired segment is
selected. Then you can cut out the segment with **_confirm
segment_**. This also closes the **segmentdialog**. Alternatively, the
**segmentdialog** can be closed any time by clicking **_abort segmentation_**.
Clicking **_abort segmentation_** discards any values that might have been
selected. You can segment the biosignal at any time. Other data (peaks,
statistics) will be also be segmented if they are already computed. Note that
the selected segment must have a minimum duration of five seconds.

### save biosignal
**menubar** -> **_biosignal_** -> _save_ opens a file dialog that lets you
select a directory and file name for saving the biosignal.
Note that saving the biosignal is only possible after segmentation. The file is
saved in its original format containing all channels.

### find peaks
First make sure that the correct modality is selected in **optionspanel** -> **_processing options_** -> _modality_, 
since `biopeaks` uses a modality-specific peak detector.
Then, **menubar** -> **_peaks_** -> _find_ automatically identifies the peaks in the
biosignal. The peaks appear as dots displayed on top of the biosignal. 

![peaks](biopeaks/images/screenshot_peaks.png)

### save peaks
**menubar** -> **_peaks_** -> _save_ opens a file dialog that lets you select a
directory and file name for saving the peaks in a CSV file. The format of the
file depends on the _modality_. For ECG and PPG, `biopeaks` saves a column containing
the occurrences of R-peaks or systolic peaks respectively in seconds. The first element contains the header
"peaks". For breathing, `biopeaks` saves two columns containing the occurrences
of inhalation peaks and exhalation troughs respectively in seconds. The first
row contains the header "peaks, troughs". Note that if there are less peaks
than troughs or vice versa, the column with less elements will be padded with
a NaN.

### load peaks
**menubar** -> **_peaks_** -> _load_ opens a file dialog that lets you select
the file containing the peaks. Note that prior to loading the peaks, you have
to load the associated biosignal. Also, loading peaks won't work if there are
already peaks in memory (i.e., if there are already peaks displayed in the
upper **datadisplay**). Note that it's only possible to load peaks that have
been saved with `biopeaks` or adhere to the same format. The peaks appear as
dots displayed on top of the biosignal.

### calculate statistics
**menubar** -> **_statistics_** -> _calculate_ automatically calculates all
possible statistics for the selected _modality_. The statistics will be 
displayed in the lowest **datadisplay**.

![statistics](biopeaks/images/screenshot_statistics.png)

### save statistics
First select the statistics that you'd like to save: **optionspanel** ->
**_select statictics for saving_**. Then, 
**menubar** -> **_statistics_** -> _save_, opens a file dialog
that lets you choose a directory and file name for saving a CSV file. The
format of the file depends on the _modality_. Irrespective
of the modality the first two columns contain period and rate (if both have
been chosen for saving).
For breathing, there will be an additional third column containing the tidal
amplitude (if it has been chosen for saving). The first row contains the
header. Note that the statistics are
interpolated to match the biosignal's timescale (i.e., they represent
instantaneous statistics sampled at the biosignal's sampling rate).

### edit peaks
It happens that the automatic peak detection places peaks wrongly or fails to
detect some peaks. You can
catch these errors by visually inspecting the peak placement. If you spot
errors in peak placement you can correct those manually. To do so make sure to
select **optionspanel** -> **peak options** -> _editable_. Now click on the
upper **datadisplay** once to enable peak editing. To delete a peak place the 
mouse cursor in it's vicinity and press "d". To add a peak,
press "a". Editing peaks is most convenient if you zoom in on the biosignal
region that you want to edit using the [**displaytools**](#displaytools).
The statistics in the lowest **datadisplay**
can be a useful guide when editing peaks. Isolated, unusually large or small
values in period or rate can indicate misplaced peaks. Note, that when editing breathing
extrema, any edits that break the alternation of peaks and troughs
(e.g., two consecutive peaks) will automatically be discarded when you save
the extrema. If you already calculated statistics, don't forget to calculate
them again after peak editing.

### auto-correct peaks
If the _modality_ is ECG or PPG, you can automatically correct the peaks with
**menubar** -> **_peaks_** -> _autocorrect_. Note that the auto-correction tries
to spread the peaks evenly across the signal which can lead to peaks that are
slightly misplaced. Also, the auto-correction does not guarantee that
all errors in peak placement will be caught. It is always good to check for errors manually!
 
### batch processing
> :warning: There is no substitute for manually checking the biosignal's
> quality as well as the placement of the peaks. Manually checking and editing
> peak placement is the only way to guarantee sensible statistics. Only use
> batch processing if you are sure that the biosignal's quality is sufficient!
> :warning:

You can configure your batch processing in the **optionspanel**.
To enable batch processing, select 
**_processing options_** -> _mode_ -> multiple files. Make sure to
select the correct _modality_ in the **_processing options_** as well. Also select
the desired _biosignal channel_ in **_channels_**. Further, indicate if you'd
like to save the peaks during batch processing: **_peak options_** ->
_save during batch processing_. You can also choose to apply the auto-correction
to the peaks by selecting **_peak options_** ->
_correct during batch processing_. Also, select the statistics you'd like
to save: **_select statictics for saving_**. Now, select
all files that should be included in the batch: **menubar** -> **_biosignal_**
-> _load_. A dialog will let you select the files (select multiple files with
the appropriate keyboard commands of your operating system). Next, a dialog
will ask you to choose a directory for saving the peaks (if you enabled that
option). The peaks will be saved to a file with the same name as the biosignal
file, with a "_peaks" extension.
Finally, a dialog will ask you to select a directory for saving the statistics
(if you chose any statistics for saving). The statistics will be saved to a
file
with the same name as the biosignal file, with a "_stats" extension. Once all
dialogs are closed, `biopeaks` carries out the following actions for each file
in the batch: loading the biosignal, identifying the
peaks, calculating the statistics and finally saving the desired data (peaks
and/or statistics). Note that nothing will be shown in the **datadisplay**
while the batch is processed. You can keep track of the progress by looking
at the file name displayed in the lower right corner of the interface.
Note that segmentation or peak editing are not possible during batch
processing.

### displaytools
The **displaytools** allow you to interact with the biosignal. Have a look
[here](https://matplotlib.org/3.1.1/users/navigation_toolbar.html) for a
detailed description of how to use them.



# Contributor Guide
Please report any bug or question by [opening an issue](https://help.github.com/en/github/managing-your-work-on-github/creating-an-issue).
Pull requests for new features, improvements, and bug fixes are very welcome!

The application is structured according to a variant of the
[model-view-controller architecture](https://martinfowler.com/eaaDev/uiArchs.html).
To understand the relationship of the model, view, and controller have a look
at how each of them is instantiated in `__main__.py`. For
example, the view class has references to the model class as well as the
controller class, whereas the model has no reference to any of the other
components of the architecture (i.e., the model is agnostic to the view and
controller).

# Tests

## Frontend
The OpenSignals test data have been recorded with\
software: opensignals v2.0.0, 20190805\
hardware: BITalino (r)evolution (firmware 1281)

The EDF test data have been downloaded from https://www.teuniz.net/edf_bdf_testfiles/

Please make sure to have [pytest](https://docs.pytest.org/en/latest/) as well as
[pytest-qt](https://pypi.org/project/pytest-qt/) installed before running the frontend tests.

The tests can be run using [pytest](https://docs.pytest.org/en/latest/):
```
pytest -v
```


## Backend
In order to validate the performance of the ECG peak detector `heart.ecg_peaks()`,
please download the [Glasgow University Database (GUDB)](http://researchdata.gla.ac.uk/716/).
In addition you need to install the [wfdb](https://github.com/MIT-LCP/wfdb-python) package either with conda
```
conda install -c conda-forge wfdb
```
or pip.

```
pip install wfdb
```
You can then run the `benchmark_ECG` script in the test folder.

In order to validate the performance of the PPG peak detector `heart.ppg_peaks()`
please download the [Capnobase IEEE TBME benchmark dataset](http://www.capnobase.org/index.php?id=857).
After extracting the PPG signals and peak annotations you can run the `benchmark_PPG` script in the test folder.

# Changelog

### Version 1.3.1 (May 06, 2020)
+ bugfix: corrected control-flow of artifact classification during auto-correction of ECG and PPG peaks.
+ bugfix: using PySide2 resources instead of PyQt5 resources

### Version 1.3.0 (April 27, 2020)
+ enhancement: using the official Qt Python bindings (PySide2) instead of PyQt5.
+ bugfix: enforcing minimal figure height to comply with requirements of Matplotlib > 3.2.0.

### Version 1.2.2 (April 15, 2020)
+ enhancement: faster auto-correction of ECG and PPG peaks with pandas rolling window.
+ bugfix: corrected error in calculation of subspace 22 during auto-correction of ECG and PPG peaks.
+ bugfix: during segmentation, extrema at segment boundaries are now excluded from segment.

### Version 1.2.1 (April 01, 2020)
+ enhancement: auto-correction of ECG and PPG peaks is now optional (instead
of being applied by default during the calculation of the statistics).
+ enhancement: improved baseline removal for respiration signals.

### Version 1.2.0 (March 20, 2020)
+ enhancement: added peak detection for photoplethysmogram (PPG) (heart.ppg_peaks()), based on
[Elgendi et al., (2013)](https://journals.plos.org/plosone/article/comments?id=10.1371/journal.pone.0076585).
The performance of heart.ppg_peaks() has been evaluated on the PPG signals of all
42 subjects in the [Capnobase IEEE TBME benchmark dataset](http://www.capnobase.org/index.php?id=857).
The dataset has not been used to optimize `heart.ppg_peaks()` in any way prior to
the performance evaluation. The tolerance for peak detection was set to 50 milliseconds in
accordance with [Elgendi et al., (2013)](https://journals.plos.org/plosone/article/comments?id=10.1371/journal.pone.0076585).

|metric     |summary|version 1.2.0
|:---------:|:-----:|:-----------:
|precision  |mean   |.996         
|           |std    |.004         
|sensitivity|mean   |.999         
|           |std    |.001         

+ bugfix: the PATCH version has been reset to 0 after incrementing MINOR version (https://semver.org/)

### Version 1.1.6 (March 06, 2020)
+ enhancement: some small improvements of the statistics panel in **datadisplay**.

### Version 1.1.5 (March 01, 2020)
+ enhancement: added support for [EDF files](https://en.wikipedia.org/wiki/European_Data_Format).
+ enhancement: `ecg.ecg_peaks()` now filters out power-line noise at 50Hz. This
further increases the performance on the [Glasgow University Database (GUDB)](http://researchdata.gla.ac.uk/716/).
Again, the GUBD has not been used to optimize `ecg.ecg_peaks()` in any way prior to
the performance evaluation. The tolerance for peak detection was set to one
sample.

|condition|metric     |summary|version 1.0.2|version 1.0.3|version 1.1.5
|:-------:|:---------:|:-----:|:-----------:|:-----------:|:-----------:
|sitting  |precision  |mean   |.999         |.998         |.998
|         |           |std    |.002         |.005         |.002
|         |sensitivity|mean   |.996         |.996         |.998
|         |           |std    |.008         |.004         |.004
|handbike |precision  |mean   |.904         |.930         |.984
|         |           |std    |.135         |.127         |.022
|         |sensitivity|mean   |.789         |.857         |.984
|         |           |std    |.281         |.247         |.025

### Version 1.0.5 (February 09, 2020)
+ enhancement: improved ECG artifact detection and correction.

### Version 1.0.4 (January 08, 2020)
+ bugfix: `controller.edit_peaks()` works properly again.
+ enhancement: moved the modality menu to processing options.

### Version 1.0.3 (December 26, 2019)
+ enhancement: improved sensitivity of `ecg.ecg_peaks()` without decreasing
precision in moderately dynamic conditions (handbike) while maintaining
high performance in resting conditions (sitting). Performance has been
evaluated on lead 2 of all 25 subjects in the [Glasgow University Database (GUDB)](http://researchdata.gla.ac.uk/716/).
The GUBD has not been used to optimize `ecg.ecg_peaks()` in any way prior to
the performance evaluation. The tolerance for peak detection was set to one
sample.

|condition|metric     |summary|version 1.0.2|version 1.0.3
|:-------:|:---------:|:-----:|:-----------:|:-----------:
|sitting  |precision  |mean   |.999         |.998         
|         |           |std    |.002         |.005         
|         |sensitivity|mean   |.996         |.996         
|         |           |std    |.008         |.004         
|handbike |precision  |mean   |.904         |.930         
|         |           |std    |.135         |.127         
|         |sensitivity|mean   |.789         |.857         
|         |           |std    |.281         |.247         

### Version 1.0.2 (December 1, 2019)
+ enhancement: `resp.resp_extrema()` is now based on zerocrossings and makes
fewer assumptions about breathing rate.

### Version 1.0.1 (November 28, 2019)
+ bugfix: `controller.save_signal()` now preserves the header if the data are
saved to the same location (i.e., if `model.rpathsignal` and `model.wpathsignal` are
identical).


# Further Resources
Check out these free alternatives:
+ https://www.medisig.com/signalplant/
+ https://physiodatatoolbox.leidenuniv.nl/
+ http://www.artiifact.de/
