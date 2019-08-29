# 1. General Information
**biopeaks** is an application for feature extraction from biosignals recorded
with the Bitalino and OpenSignals. It offers a graphical user interface for displaying and
segmenting the data. Most importantly it offers solutions for automatically
identifying and manually editing fiducial points in the data. Specifically,
you can extract R-peaks locations in ECG data, as well as extrema
and amplitude in breathing data (i.e. inhalation peaks, exhalation troughs
and the associated amplitudes).


# 2. User Guide

## 2.1. Installation

## 2.2. Getting started

### 2.2.1. single file processing
You can load the data either from a specific channel (analogue channels 1-6) or
the channel can be inferred from the selected modality. The latter option
only works if the channel has been declared as belonging to the selected
modality in the OpenSignals recording software, for example an ECG channel
must be specified as "ECG"

biopeaks only works with OpenSignals text file format; you can use biopeaks
to analyze any data as long as you format your data according to the
OpenSignals convention (link to example)

after you've checked "edit peaks", click on the figure once to enable editing;

for ECG data, biopeaks saves the timestamps of the R-peaks in seconds;
for respiration data, biopeaks saves the timestamps of inhalation peaks and
exhalation troughs in seconds, as well as the depth of breathing at these
timestamps

note, that when editing breathing extrema, any edits that break the
alternation of peaks and troughs (e.g. two consecutive peaks) will
automatically be thrown out when you save the peaks

note that prior to loading the peaks, you have to load the associated data; also loading peaks
won't work if there are already peaks in memory

note that markers can only be loaded from the dataset that is currently in
memory
note that changing the marker channel and docking the markers is only possible
until the signal has been segmented, i.e. after you segmented you data, you can
only load the markers if you saved the segmented data and reloaded them;
note that markers can be any channel that can be loaded from the marker channel
menu (i.e. you could also load another modality to be displayed along your
primary modality)
note that any current data zooming will be undone when when docking markers

### 2.2.2. batch processing

# 3. Contributor Guide
include link that describes MVC architecture:
https://martinfowler.com/eaaDev/uiArchs.html
also include diagram of components (M,V,C) indicating their relationships with
arrows

# 4. Tests
test data have been recorded with
software: opensignals v2.0.0, 20190805
hardware: bitalino revolution (firmware 1281)

# 5. Further Resources
list links to other open source toolboxes