---
title: 'biopeaks: a graphical user interface for feature extraction from heart- and breathing biosignals'
tags:
  - Python
  - GUI
  - biosignals
  - heart
  - breathing
  - extrema detection
  - feature extraction
authors:
  - name: Jan C. Brammer
    orcid: 0000-0002-7664-3753
    affiliation: 1
affiliations:
  - name: Behavioral Science Institute, Radboud University Nijmegen, Nijmegen, The Netherlands
    index: 1
date: 06 March 2020
bibliography: paper.bib
---

The recording of heart and breathing biosignals has become affordable and relatively easy to do.
Consequently, a growing number of academic fields and industries include these physiological measurements
in research and development. Complementary to the availability of low-cost sensors, there is a growing
ecosystem of free, open-source tools for the analysis of biosignals [@neurokit; @biosppy].
However, these tools do not offer graphical user interfaces (GUI). `biopeaks` addresses this need.

Heart and breathing biosignals require local extrema detection in order to extract features
such as rate, period, or amplitude. Local extrema include R-peaks in electrocardiogram (ECG),
corresponding to the contraction of the heart muscle and subsequent ejection of blood,
as well as inhalation peaks and exhalation troughs in breathing biosignals.
During extrema detection and feature extraction, the ability to visually interact with the biosignals
is crucial for checking the biosignal's quality as well as verifying and editing the placement of the extrema.
For these tasks, a GUI offers advantages over APIs.

`biopeaks` is designed to make biosignal inspection, extrema detection and editing, as well as feature
extraction as fast and intuitive as possible. It is a pure Python implementation using the cross-platform
PyQt5 framework. `biopeaks` is built on matplotlib [@matplotlib], numpy [@numpy], scipy [@scipy] and pandas [@pandas].

The GUI has the following functionality:
+ works with files in the open biosignal formats EDF [@edf] as well as OpenSignals [@opensignals]
+ interactive biosignal visualization
+ biosignal segmentation
+ automatic extrema detection (R-peaks in ECG, exhalation troughs and inhalation peaks in breathing signals)
with signal-specific, sensible defaults
+ automatic state-of-the-art artifact correction for ECG [@lipponen]
+ manual editing of extrema (useful in case of poor biosignal quality)
+ calculation of instantaneous features: (heart- or breathing-) rate and period, as well as breathing amplitude
+ few steps from raw signal to feature extraction
+ does not require knowledge of (biomedical) digital signal processing
+ batch processing
+ export of extrema and instantaneous features for further analysis (e.g., heart rate variability)

There are free alternatives that do not require a (Matlab) license [@artiifact; @physiodatatoolbox; @signalplant].
However, these come with the following drawbacks:

+ require file conversion [@artiifact; @physiodatatoolbox]
+ not open-source [artiifact; signalplant]
+ require some knowledge of (biomedical) digital signal processing [@artiifact; @physiodatatoolbox; @signalplant]
+ many steps from raw data to feature extraction [@artiifact; @physiodatatoolbox; @signalplant]
+ no possibility to export instantaneous features [@physiodatatoolbox; @signalplant]

At the time of writing, `biopeaks` is used in multiple projects at the Gemhlab [@gemh].


# Acknowledgements
I thank Nastasia Griffioen, Babet Halberstadt, and Joanneke Weerdmeester for
their invaluable feedback throughout the development of `biopeaks`. 


# References