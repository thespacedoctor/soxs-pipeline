#!/usr/bin/env python
# encoding: utf-8
"""
*use a first-guess dispersion map to convert wavelengths to pixels*

:Author:
    David Young

:Date Created:
    April 15, 2021
"""
from builtins import object
import sys
import os
os.environ['TERM'] = 'vt100'
from fundamentals import tools
from os.path import expanduser
import unicodecsv as csv
from soxspipe.commonutils.polynomials import chebyshev_order_wavelength_polynomials
import numpy as np


def dispersion_map_to_pixel_arrays(
        log,
        dispersionMapPath,
        lineList):
    """*use a first-guess dispersion map to append x,y fits to line-list data frame.* 

    Return a line-list with x,y fits given a first guess dispersion map.*

    **Key Arguments:**

    - `log` -- logger
    - `dispersionMapPath` -- path to the dispersion map
    - `lineList` -- a data-frame including 'order', 'wavelength' and 'slit_pos' columns

    **Usage:**

    ```python
    myDict = {
        "order": [11, 11, 11],
        "wavelength": [850.3, 894.3, 983.2],
        "slit_pos": [0, 0, 0]
    }
    lineList = pd.DataFrame(myDict)
    lineList = dispersion_map_to_pixel_arrays(
        log=log,
        dispersionMapPath="/path/to/map.csv",
        lineList=lineList
    )
    ```           
    """
    log.debug('starting the ``dispersion_map_to_pixel_arrays`` function')

    # READ THE FILE
    home = expanduser("~")
    dispersion_map = dispersionMapPath.replace("~", home)

    # READ IN THE X- AND Y- GENERATING POLYNOMIALS FROM DISPERSION MAP FILE
    coeff = {}
    poly = {}
    with open(dispersion_map, 'rb') as csvFile:
        csvReader = csv.DictReader(
            csvFile, dialect='excel', delimiter=',', quotechar='"')
        for row in csvReader:
            axis = row["axis"]
            order_deg = int(row["order-deg"])
            wavelength_deg = int(row["wavelength-deg"])
            slit_deg = int(row["slit-deg"])
            coeff[axis] = [float(v) for k, v in row.items() if k not in [
                "axis", "order-deg", "wavelength-deg", "slit-deg"]]
            poly[axis] = chebyshev_order_wavelength_polynomials(
                log=log, order_deg=order_deg, wavelength_deg=wavelength_deg, slit_deg=slit_deg).poly
    csvFile.close()

    # CONVERT THE ORDER-SORTED WAVELENGTH ARRAYS INTO ARRAYS OF PIXEL TUPLES
    lineList["fit_x"] = poly['x'](lineList, *coeff['x'])
    lineList["fit_y"] = poly['y'](lineList, *coeff['y'])

    # FILTER DATA FRAME
    # FIRST CREATE THE MASK
    mask = (lineList["fit_x"] > 0) & (lineList["fit_y"] > 0)
    lineList = lineList.loc[mask]

    log.debug('completed the ``dispersion_map_to_pixel_arrays`` function')
    return lineList
