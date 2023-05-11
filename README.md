# soxspipe

<!-- INFO BADGES -->  

[![](https://img.shields.io/pypi/pyversions/soxspipe)](https://pypi.org/project/soxspipe/)
[![](https://img.shields.io/pypi/v/soxspipe)](https://pypi.org/project/soxspipe/)
[![](https://img.shields.io/conda/vn/conda-forge/soxspipe)](https://anaconda.org/conda-forge/soxspipe)
[![](https://pepy.tech/badge/soxspipe)](https://pepy.tech/project/soxspipe)
[![](https://img.shields.io/github/license/thespacedoctor/soxspipe)](https://github.com/thespacedoctor/soxspipe)

<!-- STATUS BADGES -->  

[![](https://soxs-eso-data.org/ci/buildStatus/icon?job=soxspipe%2Fmaster&subject=build%20master)](https://soxs-eso-data.org/ci/blue/organizations/jenkins/soxspipe/activity?branch=master)
[![](https://soxs-eso-data.org/ci/buildStatus/icon?job=soxspipe%2Fdevelop&subject=build%20dev)](https://soxs-eso-data.org/ci/blue/organizations/jenkins/soxspipe/activity?branch=develop)
[![](https://cdn.jsdelivr.net/gh/thespacedoctor/soxspipe@master/coverage.svg)](https://raw.githack.com/thespacedoctor/soxspipe/master/htmlcov/index.html)
[![](https://readthedocs.org/projects/soxspipe/badge/?version=master)](https://soxspipe.readthedocs.io/en/master/)
[![](https://img.shields.io/github/issues/thespacedoctor/soxspipe/type:%20bug?label=bug%20issues)](https://github.com/thespacedoctor/soxspipe/issues?q=is%3Aissue+is%3Aopen+label%3A%22type%3A+bug%22+)

*The data-reduction pipeline for the SOXS instrument* (a python package with command-line tools).

Documentation for soxspipe is hosted by [Read the Docs](https://soxspipe.readthedocs.io/en/master/) ([development version](https://soxspipe.readthedocs.io/en/develop/) and [master version](https://soxspipe.readthedocs.io/en/master/)). The code lives on [github](https://github.com/thespacedoctor/soxspipe). Please report any issues you find [here](https://github.com/thespacedoctor/soxspipe/issues).

## Installation

The best way to install soxspipe is to use `conda` and install the package in its own isolated environment, as shown here:

``` bash
conda create -n soxspipe python=3.9 soxspipe -c conda-forge
conda activate soxspipe
```

To check installation was successful run `soxspipe -v`. This should return the version number of the install.

To upgrade to the latest version of soxspipe use the command:

``` bash
conda upgrade soxspipe -c conda-forge
```

## Initialisation 

Before using soxspipe you need to use the `init` command to generate a user settings file. Running the following creates a [yaml](https://learnxinyminutes.com/docs/yaml/) settings file in your home folder under `~/.config/soxspipe/soxspipe.yaml`:

```bash
soxspipe init
```

The file is initially populated with soxspipe's default settings which can be adjusted to your preference.

If at any point the user settings file becomes corrupted or you just want to start afresh, simply trash the `soxspipe.yaml` file and rerun `soxspipe init`.

