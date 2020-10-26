# -*- coding: utf-8 -*-

from setuptools import setup, find_namespace_packages


with open("README.md") as readme:
    long_description = readme.read()

# Update local links such that project description on PyPI points to GitHub.
long_description = long_description.replace("](docs/images",
                                            "](https://github.com/JanCBrammer/biopeaks/raw/master/docs/images")

setup(
    name="biopeaks",
    version="1.4.1",
    description="A graphical user interface for feature extraction from heart- and breathing biosignals.",
    url="https://github.com/JanCBrammer/biopeaks",
    author="Jan C. Brammer",
    author_email="jan.c.brammer@gmail.com",
    long_description=long_description,
    long_description_content_type="text/markdown",
    project_urls={"Documentation": "https://jancbrammer.github.io/biopeaks",
                  "Source": "https://github.com/JanCBrammer/biopeaks"},
    keywords="ECG PPG Breathing Biosignals Bitalino OpenSignals EDF GUI",
    packages=find_namespace_packages(exclude=["misc", "paper"]),
    python_requires=">=3.7",
    license="GPL-3.0",
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "biopeaks=biopeaks.__main__:main",
        ],
    }
)
