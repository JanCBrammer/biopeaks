# Installation

## As executable

For Windows you can download [biopeaks.exe](https://github.com/JanCBrammer/biopeaks/releases/latest). Double-click the 
executable to run it. You don't need a Python installation on your computer to run the executable.
Currently, there are no executables available for macOS or Linux
(please [open an issue](https://help.github.com/en/github/managing-your-work-on-github/creating-an-issue) if you're interested).

## As Python package

### Instructions for users without a Python installation
If you don't have experience with installing Python packages and/or if you
aren't sure if you have Python on your computer start by setting up Python.
Go to <https://docs.conda.io/en/latest/miniconda.html> and install the latest
miniconda distribution for your operating system.
Follow these [instructions](https://conda.io/projects/conda/en/latest/user-guide/install/index.html)
in case you're unsure about the installation. Once you've installed miniconda, open the
[Anaconda Prompt](https://docs.anaconda.com/anaconda/user-guide/getting-started/)
and run the following commands (hit enter once you've typed each of the lines below and wait for
the commands to be executed):

```
conda config --add channels conda-forge
conda config --set channel_priority strict
conda create -y -n biopeaks python=3.9 scipy numpy matplotlib pandas
conda activate biopeaks
pip install biopeaks PySide6 
```

After the successful installation, open the application by typing
```
biopeaks
```
Note that every time you open the Anaconda Prompt, you need to activate the
biopeaks environment before starting the application:
```
conda activate biopeaks
biopeaks
```

### Instructions for users who already have a Python installation
Have a look at the project's [pyproject.toml file](https://github.com/JanCBrammer/biopeaks/blob/master/pyproject.toml)
for an up-to-date list of the dependencies. In order to manage the dependencies, it is highly recommended to install
`biopeaks` into an isolated environment using [miniconda](https://docs.conda.io/en/latest/miniconda.html),
[Poetry](https://python-poetry.org/), or other tools for creating and managing virtual environments.

Once you've set up an environment containing all the dependencies, install `biopeaks` with

```
pip install biopeaks
```

You can then open the application by typing

```
biopeaks
```
