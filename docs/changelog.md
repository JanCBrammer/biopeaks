# Changelog

### Version 1.4.0 (August 04, 2020)
+ enhancement: added support for plain text files (.txt, .csv, .tsv).
+ enhancement: stream [Glasgow University Database (GUDB)](http://researchdata.gla.ac.uk/716/) for ECG benchmarking (download is no longer required).

### Version 1.3.2 (June 07, 2020)
+ enhancement: visibility of configuration panel can now be toggled (more screen space for signals).
+ bugfix: fixed index-out-of-range error in `heart._correct_misaligned()`.

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