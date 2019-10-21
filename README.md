# 1. General Information


`biopeaks` is a graphical user interface for the processing of biosignals recorded
with the Bitalino and OpenSignals. You can visualize, segment, and analyze
electrocardiogram (ECG) as well as breathing signals. The following features
can be extracted from ECG and breathing biosignals: extrema locations
(ECG: R-peaks; breathing: inhalation peaks, exhalation troughs), period, and rate.
Additionally, you can extract tidal amplitude from breathing signals.
The extraction of these features is the fundamental first step for many subsequent
analyses, such heart rate variability. Errors during feature extraction can significantly
distort subsequent analyses (link example HRV). Therefore, the intention of `biopeaks`
is to make feature extraction convenient and precise. Especially the visualization
of the biosignals along with the extracted features is crucial in determining signal
quality and usability of the data. The ability to manually edit the extracted features
is equally important, since no algorithm can perfectly identify all features,
especially if the biosignals are of poor quality.


# 2. User Guide

## 2.1. Installation

Go to https://www.anaconda.com/distribution/ and install the lastest distribution
for your operating system. Follow the installation instructions in case you're unsure
about something: https://docs.anaconda.com/anaconda/install/

### requirements

+ wfdb

## 2.2. Getting started
In the menubar, you can find three sections: data, peaks, and statistics. These
contain methods for the interaction with your signals. On the left hand side, there's
an optionspanel that allows you costumize your workflow.
To the right of the optionspanel there are three windows which will contain your
signal, as well as the statistics derived from the signal.
In the following I will describe all these elements in more detail. `biopeaks` 
works with the OpenSignals text file format. However, you can analyze any data
as long as you format your data according to the OpenSignals convention (link to
example). The workflows in the following are for you to get familiar with the interface
(they can be altered in many ways that might make more sense given your requirements).


### 2.2.1. single file processing
Before you start your workflow, set the desired options in the optionspanel.
Make sure that the `processing modality` is set single file (this is the default)
and select your modality in channels (ECG for electrocardiogram, and RESP for
breathing). Further, you need to specify which channel contains the data corresponding
to your modality. You can let the channel be inferred from the modality, or select
a specific analog channel (1 through 6). The first option only works if the channel
has been declared as belonging to the selected
modality in the OpenSignals recording software, for example an ECG channel
must be specified as "ECG". In addition to the data channel, you can select a
marker channel. This is useful if you recorded a channel that marks interesting
events such as the onset of an experimental condition, button presses
etc.. You can display any other channel alongside your datachannel. Note however
that you can only interact with the datachannel. 
Once you have set all the options you can start using methods from the menubar.

* load data
* inspect data (describe how to use navitools --> link to separate section).
* optionally segment data
* optionally save segmented data
* find peaks
* optionally edit peaks\
	after you've checked "edit peaks", click on the figure once to enable editing;
	HR can be a useful guide when editing peaks. Spikes and unusually large or small
	HR values indicate misplaced peaks. You can calculate HR before you start editing
	to have an indication of potentially misplaced peaks. After you corrected those
	peaks, simply calculate the HR again.
	note, that when editing breathing extrema, any edits that break the
	alternation of peaks and troughs (e.g. two consecutive peaks) will
	automatically be thrown out when you save the peaks
* optionally save peaks\
	for ECG data, biopeaks saves the timestamps of the R-peaks in seconds;
	for respiration data, biopeaks saves the timestamps of inhalation peaks and
	exhalation troughs in seconds
* calculate stats (optionally save)


note that prior to loading the peaks, you have to load the associated data; also
loading peaks won't work if there are already peaks in memory

it is advisable to find the signals extrema before segmenting the signal, since
the extrema detection algorithms work best on larger datasets (>2 min).

### 2.2.2. batch processing
In red box:\
There is no substitute for checking your signal's quality as well as the placing
of the detected extrema. This is the only way to guarantee sensible statistics.

If you have multiple files it can be tedious to manually execute all analysis steps
on each of them.
No segmentation during batch processing. Select statistics. Optionally save peaks
and/or statistics.



# 3. Contributor Guide
include link that describes MVC architecture:
https://martinfowler.com/eaaDev/uiArchs.html
also include diagram of components (M,V,C) indicating their relationships with
arrows

# 4. Tests
test data have been recorded with
software: opensignals v2.0.0, 20190805\
hardware: bitalino revolution (firmware 1281)

# 5. Further Resources
list links to other packages for further analyses based on biosignals features;
HRV: pyHRV
HR, HRV: biosppy