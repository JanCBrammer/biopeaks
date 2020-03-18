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

An analyst who wants to extract information from heart or breathing biosignals must perform multiple steps. For all
these steps, a GUI offers advantages over application programming interfaces.

First, they must verify if the biosignal quality is sufficient for analysis. Biosignals can be corrupted
for a number of reasons, including movement artifacts, poor sensor placement and many more. `biopeaks` allows
the analyst to quickly visualize a biosignal and interact with it (panning, zooming) in order to evaluate its quality.

If the analyst deems the biosignal's quality sufficient they proceed to identify local extrema.
Local extrema include R-peaks in electrocardiogram (ECG), corresponding to the contraction of the heart muscle
and subsequent ejection of blood, as well as inhalation peaks and exhalation troughs in breathing biosignals.
`biopeaks` detects these extrema automatically with sensible algorithmic defaults. Algorithmically identified
extrema can be misplaced (false positives) or extrema might be missed (false negative). These
errors can happen if there are small noisy segments in an otherwise clean biosignal. If left uncorrected, these
errors significantly distort the subsequent analysis steps [@]. This is why `biopeaks` offers intuitive manual extrema editing
(i.e., removing and adding extrema). Additionally, for cardiac biosignals, `biopeaks` automatically performs
state-of-the-art extrema correction [@lipponen].

Finally, based on the extrema, the analyst can extract features from the biosignal. The features are based on temporal or
amplitude differences between the extrema. For example, have a look at Fig. 1 through 3, which illustrate the extraction of
heart period, breathing period, and breathing (inhalation) amplitude respectively.

![figure1](figure1)
*Figure 1*: Extraction of heart period from R-peaks in an ECG signal

![figure2](figure2)
*Figure 2*: Extraction of breathing period from inhalation peaks in a breathing signal

![figure3](figure3)
*Figure 3*: Extraction of inhalation amplitude from breathing extrema in a breathing signal


In summary, `biopeaks` is designed to make biosignal inspection, extrema detection and editing, as well as feature
extraction as fast and intuitive as possible. It is a pure Python implementation using the cross-platform
PyQt5 framework. `biopeaks` is built on matplotlib [@matplotlib], numpy [@numpy], scipy [@scipy] and pandas [@pandas].

The GUI has the following functionality:
+ works with files in the open biosignal formats EDF [@edf] as well as OpenSignals [@opensignals]
+ interactive biosignal visualization
+ biosignal segmentation
+ automatic extrema detection (R-peaks in ECG, exhalation troughs and inhalation peaks in breathing signals)
with signal-specific, sensible defaults
+ automatic state-of-the-art artifact correction for cardiac extrema [@lipponen]
+ manual editing of extrema (useful in case of poor biosignal quality)
+ extraction of instantaneous features: (heart- or breathing-) rate and period, as well as breathing amplitude
+ few steps from raw biosignal to feature extraction
+ does not require knowledge of (biomedical) digital signal processing
+ automatic analysis of multiple files (batch processing)
+ .csv export of extrema and instantaneous features for further analysis (e.g., heart rate variability)

There are free alternatives to `biopeaks` that do not require a (Matlab) license [@artiifact; @physiodatatoolbox; @signalplant].
However, these come with the following drawbacks:

+ require file conversion to toolbox-specific format [@artiifact; @physiodatatoolbox]
+ not open-source [artiifact; signalplant]
+ require some knowledge of (biomedical) digital signal processing [@artiifact; @physiodatatoolbox; @signalplant]
+ many steps from raw data to feature extraction [@artiifact; @physiodatatoolbox; @signalplant]
+ no possibility to export instantaneous features [@physiodatatoolbox; @signalplant]

At the time of writing, `biopeaks` is used in multiple projects at the Gemhlab [@gemh].


# Acknowledgements
I thank Nastasia Griffioen, Babet Halberstadt, and Joanneke Weerdmeester for their invaluable feedback throughout
the development of `biopeaks`. 


# References