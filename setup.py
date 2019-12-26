# -*- coding: utf-8 -*-

from setuptools import setup, find_namespace_packages

setup(
    name="biopeaks",
    version="1.0.3",
    description="A graphical user interface for the analysis of OpenSignals ECG - and breathing biosignals",
    url="https://github.com/JohnDoenut/biopeaks",
    author="Jan C. Brammer",
    author_email="j.brammer@psych.ru.nl",
    keywords="ECG Breathing Biosignals Bitalino OpenSignals GUI",
    packages=find_namespace_packages(exclude=["misc"]),
    python_requires=">=3.7",
    license="GPL-3.0",
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "biopeaks=biopeaks.__main__:main",
        ],
    }
)
