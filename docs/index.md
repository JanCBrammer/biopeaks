Welcome to `biopeaks`, a straightforward graphical user interface for feature extraction from electrocardiogram (ECG), photoplethysmogram (PPG) and breathing biosignals.
It processes these biosignals semi-automatically with sensible defaults and offers the following functionality:

* processes files in the open biosignal formats [EDF](https://en.wikipedia.org/wiki/European_Data_Format)
as well as [OpenSignals (Bitalino)](https://bitalino.com/en/software)
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


Have a look at the documentation to find out more: 

+ [Installation](installation.md)
+ [User Guide](user_guide.md)
+ [Contributor Guide](contributor_guide.md)
+ [Tests](tests.md)
+ [Changelog](changelog.md)
+ [Further Resources](additional_resources.md)
+ [Citation](citation.md)
+ [GitHub repository](https://github.com/JanCBrammer/biopeaks)
