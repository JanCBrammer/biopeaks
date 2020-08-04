# -*- coding: utf-8 -*-

from setuptools import setup, find_namespace_packages

setup(
    name="biopeaks",
    version="1.4.0",
    description="A graphical user interface for feature extraction from heart- and breathing biosignals.",
    url="https://github.com/JanCBrammer/biopeaks",
    author="Jan C. Brammer",
    author_email="jan.c.brammer@gmail.com",
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
