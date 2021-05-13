#!/usr/bin/env python
# encoding: utf-8
"""
*small reusable functions used throughout soxspipe*

:Author:
    David Young

:Date Created:
    September 18, 2020
"""
from builtins import object
import sys
import os
os.environ['TERM'] = 'vt100'
from fundamentals import tools
from soxspipe.commonutils.polynomials import chebyshev_xy_polynomial
import unicodecsv as csv
import numpy as np
import matplotlib.pyplot as plt
import random
import numpy.ma as ma
import pandas as pd


def cut_image_slice(
        log,
        frame,
        width,
        length,
        x,
        y,
        median=False,
        plot=False):
    """*cut and return an N-pixel wide and M-pixels long slice, centred on a given coordinate from an image frame. Also return the origin pixel value for the slice*

    **Key Arguments:**

    - ``log`` -- logger
    - ``frame`` -- the data array to cut the slice from (masked array)
    - ``width`` -- width of the slice (odd number)
    - ``length`` -- length of the slice
    - ``x`` -- x-coordinate
    - ``y`` -- y-coordinate
    - ``median`` -- collapse the slice to a median value across its width
    - ``plot`` -- generate a plot of slice. Useful for debugging.

    **Usage:**

    ```python
    from soxspipe.commonutils.toolkit import cut_image_slice
    slice = cut_image_slice(log=self.log, frame=self.pinholeFlat.data,
                                    width=1, length=sliceLength, x=x_fit, y=y_fit, plot=False)
    if slice is None:
        return None
    ```           
    """
    log.debug('starting the ``cut_image_slice`` function')

    # print(frame.shape)
    halfSlice = length / 2

    #
    if (width % 2) != 0:
        halfwidth = (width - 1) / 2
    else:
        halfwidth = width / 2

    # CHECK WE ARE NOT GOING BEYOND BOUNDS OF FRAME
    if (x > frame.shape[1] - halfSlice) or (y > frame.shape[0] - halfwidth) or (x < halfSlice) or (y < halfwidth):
        return None

    slice = frame[int(y - halfwidth):int(y + halfwidth + 1),
                  int(x - halfSlice):int(x + halfSlice)]

    # print(int(x - halfSlice), y)
    # print(slice.data.shape)

    if median:
        slice = ma.median(slice, axis=0)
        # print(slice.mask)

    if plot and random.randint(1, 101) < 10000:
        # CHECK THE SLICE POINTS IF NEEDED
        x = np.arange(0, len(slice))
        plt.figure(figsize=(8, 5))
        plt.plot(x, slice, 'ko')
        plt.xlabel('Position')
        plt.ylabel('Flux')
        plt.show()

    log.debug('completed the ``cut_image_slice`` function')
    return slice

# use the tab-trigger below for new function
# xt-def-function


def quicklook_image(
        log,
        CCDObject,
        show=True):
    """*generate a quicklook image of a CCDObject - useful for development/debugging*

    **Key Arguments:**

    - ``log`` -- logger
    - ``CCDObject`` -- the CCDObject to plot
    - ``show`` -- show the image. Set to False to skip.

    ```python
    from soxspipe.commonutils.toolkit import quicklook_image
    quicklook_image(
        log=self.log, CCDObject=myframe, show=True)
    ```           
    """
    log.debug('starting the ``quicklook_image`` function')

    if not show:
        return

    frame = CCDObject
    rotatedImg = np.rot90(frame, 1)
    rotatedImg = np.flipud(np.rot90(frame, 1))

    std = np.std(frame.data)
    mean = np.mean(frame.data)
    vmax = mean + 3 * std
    vmin = mean - 3 * std
    plt.figure(figsize=(12, 5))
    plt.imshow(rotatedImg, vmin=vmin, vmax=vmax,
               cmap='gray', alpha=1, aspect='auto')
    plt.colorbar()
    plt.xlabel(
        "y-axis", fontsize=10)
    plt.ylabel(
        "x-axis", fontsize=10)
    plt.gca().invert_yaxis()
    plt.show()

    log.debug('completed the ``quicklook_image`` function')
    return None


def unpack_order_table(
        log,
        orderTablePath):
    """*unpack an order table and return a top-level `orderTableMeta` data-frame and a second `orderTablePixels` data-frame with the central-trace coordinates of each order given

    **Key Arguments:**

    - ``orderTablePath`` -- path to the order table

    **Usage:**

    ```python
    # UNPACK THE ORDER TABLE
    from soxspipe.commonutils.toolkit import unpack_order_table
    orderTableMeta, orderTablePixels = unpack_order_table(
        log=self.log, orderTablePath=orderTablePath)
    ```           
    """
    log.debug('starting the ``functionName`` function')

    # READ CSV FILE TO PANDAS DATAFRAME
    orderTableMeta = pd.read_csv(orderTablePath, index_col=False,
                                 na_values=['NA', 'MISSING'])

    # ADD Y-COORD LIST
    ycoords = [np.arange(l, u, 1) for l, u in zip(
        orderTableMeta["ymin"].values, orderTableMeta["ymax"].values)]
    orders = [np.full_like(a, o) for a, o in zip(
        ycoords, orderTableMeta["order"].values)]

    # RUN COORDINATES THROUGH POLYNOMIALS TO GET X-COORDS
    xcoords_centre = []
    xcoords_edgeup = []
    xcoords_edgelow = []
    for index, row in orderTableMeta.iterrows():
        cent_coeff = [float(v) for k, v in row.items() if "CENT_" in k]
        poly = chebyshev_xy_polynomial(log=log, deg=int(row["degy_cent"])).poly
        xcoords_centre.append(np.array(poly(ycoords[index], *cent_coeff)))
        if "degy_edge" in row:
            degy_edge = int(row["degy_edge"])
            edgeup_coeff = [float(v)
                            for k, v in row.items() if "EDGEUP_" in k]
            poly = chebyshev_xy_polynomial(
                log=log, deg=degy_edge).poly
            xcoords_edgeup.append(
                np.array(poly(ycoords[index], *edgeup_coeff)))

            edgelow_coeff = [float(v)
                             for k, v in row.items() if "EDGELOW_" in k]
            poly = chebyshev_xy_polynomial(
                log=log, deg=degy_edge).poly
            xcoords_edgelow.append(
                np.array(poly(ycoords[index], *edgelow_coeff)))

    # CREATE DATA FRAME FROM A DICTIONARY OF LISTS
    myDict = {
        "order": np.concatenate(orders),
        "ycoord": np.concatenate(ycoords),
        'xcoord_centre': np.concatenate(xcoords_centre)
    }
    # ADD ODER EDGES IF NEEDED
    if len(xcoords_edgeup):
        myDict['xcoord_edgeup'] = np.concatenate(xcoords_edgeup)
        myDict['xcoord_edgelow'] = np.concatenate(xcoords_edgelow)

    # CREATE DATA FRAME FROM A DICTIONARY OF LISTS
    orderTablePixels = pd.DataFrame(myDict)

    log.debug('completed the ``functionName`` function')
    return orderTableMeta, orderTablePixels
