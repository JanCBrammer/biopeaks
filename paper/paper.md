---
title: 'biopeaks: a graphical user interface for feature extraction from heart- and
  breathing biosignals'
authors:
- affiliation: 1
  name: Jan C. Brammer
  orcid: 0000-0002-7664-3753
date: "06 March 2020"
bibliography: paper.bib
tags:
- Python
- GUI
- biosignals
- heart
- breathing
- PPG
- ECG
- feature extraction
affiliations:
- index: 1
  name: Behavioral Science Institute, Radboud University Nijmegen, Nijmegen, The Netherlands
---

# Statement of need

Physiological measurements increasingly gain popularity in academia and industry, sparked by the availability of
easy-to-use, low-cost biosignal sensors [@bitalino] along with a growing ecosystem of free,
open-source software for the analysis of biosignals [@neurokit; @biosppy]. However, an open-source, freely
available graphical user interfaces (GUI) for heart-and breathing biosignal analysis is currenly lacking. `biopeaks` addresses this need.
Compared to application programming interfaces [@neurokit; @biosppy], its GUI allows for
more intuitive and immediate visual interaction with the biosignal, which is especially valuable
during data preprocessing and exploration. At the time of writing, `biopeaks` is used in multiple projects at the Gemhlab [@gemh].

# Functionality

+ processing of open biosignal formats EDF [@edf], OpenSignals [@opensignals], as well as plain text files (.txt, .csv, .tsv)
+ interactive biosignal visualization
+ biosignal segmentation
+ automatic extrema detection (R-peaks in ECG, systolic peaks in PPG, as well as exhalation troughs and inhalation peaks in breathing signals)
with signal-specific, sensible defaults
+ automatic state-of-the-art artifact correction for ECG and PPG extrema
+ manual editing of extrema
+ extraction of instantaneous features: (heart- or breathing-) rate and period, as well as breathing amplitude
+ small number of steps from raw biosignal to feature extraction
+ does not require knowledge of (biomedical) digital signal processing
+ automatic analysis of multiple files (batch processing)
+ .csv export of extrema and instantaneous features for further analysis (e.g., heart rate variability)

An analyst who wants to extract information from heart or breathing biosignals performs multiple analysis steps.
First, they verify if the biosignal's quality is sufficient for analysis. Biosignals can be corrupted
for a number of reasons, including movement artifacts, poor sensor placement and many more. `biopeaks` allows
the analyst to quickly visualize a biosignal and interact with it (panning, zooming) to evaluate its quality.
If the analyst deems the biosignal's quality sufficient, they proceed to identify local extrema in the physiological time series.
Local extrema include R-peaks in electrocardiogram (ECG) and systolic peaks in photoplethysmogram (PPG), representing
the contraction of the ventricular heart muscle and subsequent ejection of blood to the arteries. In breathing biosignals,
the relevant local extrema are inhalation peaks and exhalation troughs. `biopeaks` detects these extrema automatically
using three modality-specific algorithms. Breathing extrema are detected using a variant of the "zero-crossing algorithm
with amplitude threshold" described on [@khodadad]. Systolic peaks in PPG signals are identified using an implementatin of "Method IV;
Event-Related Moving Averages with Dynamic Threshold" introduced by [@elgendi]. Lastly, the ECG R-peak detector is a
custom algorithm that has been evaluated on the Glasgow University Database (GUDB) [@gudb] which contains ECG signals along with R-peak annotations. The performance of the R-peak detector has been evaluated in terms of sensitivity (aka recall; i.e., how many of the correct extrema were detected?) and precision (i.e., how many of the detected extrema are correct extrema?). Peak detection has been evaluated on Einthoven lead II of all 25 records, with a tolerance of 1 sample for true positive peak detection. The GUDB has not been used to optimize the R-peak detector prior to the performance evaluation. The performance at rest (sitting) and in dynamic conditions (handbike) is as follows:

|           |    |sitting|handbike|
|:---------:|:--:|:-----:|:------:|
|precision  |mean|.998   |.984    |
|           |std |.002   |.022    |
|sensitivity|mean|.998   |.984    |
|           |std |.004   |.025    |

The benchmarking code is included in the `biopeaks` installation and can be run without downloading the GUDB (dataset is streamed).
Despite robust performance of the extrema detectors, algorithmically identified extrema can be misplaced (false positives) or extrema might be missed (false negatives),
if there are noisy segments in the biosignal. If left uncorrected, these errors can significantly distort subsequent analysis steps [@brentson]. To adress this problem, `biopeaks` offers intuitive
point-and-click extrema editing (i.e., removing and adding extrema) to ensure the correct placement of extrema. Additionally, for cardiac biosignals,
`biopeaks` offers state-of-the-art automatic extrema correction [@lipponen]. Finally, based on the local extrema, the analyst can extract features
from the biosignal. The features are based on temporal or amplitude differences between the local extrema.
Fig. 1 through 3 illustrate the extraction of instantaneous heart period, breathing period, and breathing (inhalation) amplitude respectively.

![figure1](fig_heartperiod.svg)

*Figure 1*: Extraction of heart period (panel B) based on R-peaks in an ECG (panel A). Note that this is conceptually identical to the extraction
of heart period based on systolic peaks in PPG.

![figure2](fig_breathingperiod.svg)

*Figure 2*: Extraction of breathing period (panel B) based on inhalation peaks in a breathing signal (panel A).

![figure3](fig_breathingamplitude.svg)

*Figure 3*: Extraction of inhalation amplitude (panel B) based on breathing extrema in a breathing signal (panel A).

In summary, `biopeaks` is designed to make heart- and breathing biosignal inspection, extrema detection and editing, as well as feature
extraction fast and intuitive. It does not aim to offer a suite of low-level signal processing tools (e.g., digital filter design),
and abstracts these details away with sensible biosignal-specific defaults. `biopeaks` is implemented in Python using the cross-platform
PySide2 framework (official Python bindings for Qt) [@pyside2], and leverages matplotlib [@matplotlib], numpy [@numpy], scipy [@scipy] and pandas [@pandas] for visualization and signal processing.
There are freely available alternatives to `biopeaks` that are implemented in MATLAB [@artiifact; @physiodatatoolbox] or C# [@signalplant].
However, the source code of these tools is not available [@artiifact; @signalplant] or they are not released under an open
source license [@artiifact; @physiodatatoolbox; @signalplant].


# Acknowledgements
Nastasia Griffioen, Babet Halberstadt, Joanneke Weerdmeester, and Abele Michela provided invaluable feedback throughout the development of `biopeaks`.


# References