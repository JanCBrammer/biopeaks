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
    orcid:
    affiliation: "1"
affiliations:
  - name: Behavioral Science Institute, Radboud University Nijmegen, Nijmegen, The Netherlands
date: 06 March 2020
bibliography: paper.bib
---

Recording of heart and breathing biosignals has become affordable and relatively easy to do.
Consequently, a growing number of academic fields and industries include these physiological measurements
in research and development. Complementary to the availability of low-cost sensors, there is a growing
ecosystem of free, open-source tools for the analysis of biosignals (NeuroKit, Biosppy, van Gendt, pyHRV, hrv etc.).
However, these tools do not offer  graphical user interfaces (GUI). `biopeaks` addresses this need.

Heart and breathing biosignals require extrema detection in order to extract features
such as rate, period, or amplitude. During extrema detection and subsequent feature extraction,
the ability to visually interact with the biosignals is crucial for checking the
biosignal's quality as well as verifying and editing the placement of the extrema.
For these tasks, a GUI offers advantages over APIs (NeuroKit etc.).

`biopeaks` is designed to make biosignal inspection, extrema detection and editing, as well as feature
extraction as fast and intuitive as possible. It is a pure Python implementation using the cross-platform
PyQt5 framework.

The GUI has the following functionality:
+ works with files in the open biosignal formats EDF (reference) as well as OpenSignals (reference)
+ interactive biosignal visualization
+ biosignal segmentation
+ automatic extrema detection (R-peaks in ECG, exhalation troughs and inhalation peaks in breathing signals)
with signal-specific, sensible defaults
+ automatic state-of-the-art artifact correction for ECG (reference)
+ manual editing of extrema (useful in case of poor biosignal quality)
+ calculation of instantaneous features: (heart- or breathing-) rate and period, as well as breathing amplitude
+ few steps from raw signal to feature extraction
+ does not require knowledge of (biomedical) digital signal processing
+ batch processing
+ export of extrema and instantaneous features for further processing (e.g., heart rate variability analyses)

There are free alternatives that do not require a (Matlab) license (
https://physiodatatoolbox.leidenuniv.nl/

http://www.artiifact.de/

https://www.medisig.com/signalplant/). However, these come with the following drawbacks:

+ require file conversion (physiodatatoolbox, artiifact)
+ not open-source (signalplant, artiifact)
+ require some knowledge of (biomedical) digital signal processing (all)
+ many steps from raw data to feature extraction (all)
+ no possibility to export instantaneous features (signalplant, physiodatatoolbox)

At the time of writing, `biopeaks` is used in multiple projects at the Gemhlab (reference).


# Acknowledgements
I thank Nastasia Griffioen, Babet Halberstadt, and Joanneke Weerdmeester for
their invaluable feedback throughout the development of `biopeaks`. 


# References