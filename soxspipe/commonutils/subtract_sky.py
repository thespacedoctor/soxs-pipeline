#!/usr/bin/env python
# encoding: utf-8
"""
*Subtract the sky background using the Kelson Method*

:Author:
    David Young

:Date Created:
    April 14, 2022
"""
import pandas as pd
import numpy.ma as ma
import numpy as np
from fundamentals import tools
from builtins import object
import sys
import os
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib import cm
from copy import copy
from datetime import datetime
from matplotlib import colors
from soxspipe.commonutils import keyword_lookup
from scipy.interpolate import BSpline, splrep
from soxspipe.commonutils.filenamer import filenamer
from soxspipe.commonutils.toolkit import quicklook_image
from soxspipe.commonutils.toolkit import twoD_disp_map_image_to_dataframe
from os.path import expanduser
os.environ['TERM'] = 'vt100'
pd.options.mode.chained_assignment = None


class subtract_sky(object):
    """
    *Subtract the sky background using the Kelson Method*

    A model of the sky-background is created using a method similar to that described in Kelson, D. (2003), *Optimal Techniques in Two-dimensional Spectroscopy: Background Subtraction for the 21st Century (http://dx.doi.org/10.1086/375502). This model-background is then subtracted from the object spectrum.

    **Key Arguments:**
        - ``log`` -- logger
        - ``settings`` -- the settings dictionary
        - ``objectFrame`` -- the image frame in need of sky subtraction
        - ``twoDMap`` -- 2D dispersion map image path
        - ``qcTable`` -- the data frame to collect measured QC metrics
        - ``productsTable`` -- the data frame to collect output products
        - ``dispMap`` -- path to dispersion map. Default * False*

    **Usage:**

    To setup your logger, settings and database connections, please use the ``fundamentals`` package (`see tutorial here <http://fundamentals.readthedocs.io/en/latest/#tutorial>`_).

    To initiate a subtract_sky object, use the following:

    ```eval_rst
    .. todo::

        - create cl-util for this class
        - add a tutorial about ``subtract_sky`` to documentation
    ```

    ```python
    from soxspipe.commonutils import subtract_sky
    skymodel = subtract_sky(
        log=log,
        settings=settings,
        objectFrame=objectFrame,
        twoDMap=twoDMap,
        qcTable=qc,
        productsTable=products,
        dispMap=dispMap
    )
    skymodelCCDData, skySubtractedCCDData, qcTable, productsTable = skymodel.subtract()
    ```

    """

    def __init__(
            self,
            log,
            twoDMap,
            objectFrame,
            qcTable,
            productsTable,
            dispMap=False,
            settings=False,
    ):
        self.log = log
        log.debug("instansiating a new 'subtract_sky' object")
        self.settings = settings
        self.objectFrame = objectFrame
        self.twoDMap = twoDMap
        self.dispMap = dispMap
        self.qc = qcTable
        self.products = productsTable

        # INITIAL ACTIONS
        self.mapDF = twoD_disp_map_image_to_dataframe(log=self.log, twoDMapPath=twoDMap, assosiatedFrame=self.objectFrame)
        quicklook_image(
            log=self.log, CCDObject=objectFrame, show=False, ext=False, stdWindow=5, title="Object Frame with dispersion solution grid", surfacePlot=True, dispMap=dispMap, dispMapDF=self.mapDF)

        # KEYWORD LOOKUP OBJECT - LOOKUP KEYWORD FROM DICTIONARY IN RESOURCES
        # FOLDER
        self.kw = keyword_lookup(
            log=self.log,
            settings=self.settings
        ).get
        kw = self.kw
        self.arm = objectFrame.header[kw("SEQ_ARM")]
        self.dateObs = objectFrame.header[kw("DATE_OBS")]

        self.skymodelCCDData, self.skySubtractedCCDData = self.create_placeholder_images()

        # GET A TEMPLATE FILENAME USED TO NAME PRODUCTS
        self.filenameTemplate = filenamer(
            log=self.log,
            frame=self.objectFrame,
            settings=self.settings
        )

        return None

    def subtract(self):
        """
        *generate and subtract a sky-model from the input frame*

        **Return:**
            - ``skymodelCCDData`` -- CCDData object containing the model sky frame
            - ``skySubtractedCCDData`` -- CCDData object containing the sky-subtacted frame
            - ``qcTable`` -- the data frame containing measured QC metrics
            - ``productsTable`` -- the data frame containing collected output products
        """
        self.log.debug('starting the ``get`` method')

        uniqueOrders = self.mapDF['order'].unique()
        utcnow = datetime.utcnow()
        utcnow = utcnow.strftime("%Y-%m-%dT%H:%M:%S")

        for o in uniqueOrders:
            imageMapOrder = self.mapDF[self.mapDF["order"] == o]
            imageMapOrderWithObject, imageMapOrder = self.get_over_sampled_sky_from_order(imageMapOrder, o, ignoreBP=False)
            imageMapOrder = self.fit_bspline_to_sky(imageMapOrder, o,)
            self.add_data_to_placeholder_images(imageMapOrder)
            if o == 25:
                qc_plot_path = self.plot_sky_sampling(order=o, imageMapOrderWithObjectDF=imageMapOrderWithObject, imageMapOrderDF=imageMapOrder)
                basename = os.path.basename(qc_plot_path)
                self.products = self.products.append({
                    "soxspipe_recipe": "soxs-stare",
                    "product_label": "SKY_MODEL_QC_PLOTS",
                    "file_name": basename,
                    "file_type": "PDF",
                    "obs_date_utc": self.dateObs,
                    "reduction_date_utc": utcnow,
                    "product_desc": f"QC plots for the sky-background modelling",
                    "file_path": qc_plot_path
                }, ignore_index=True)

        filename = self.filenameTemplate.replace("_SLIT", "_SKYMODEL")
        home = expanduser("~")
        outDir = self.settings["intermediate-data-root"].replace("~", home)
        filePath = f"{outDir}/{filename}"
        self.products = self.products.append({
            "soxspipe_recipe": "soxs-stare",
            "product_label": "SKY_MODEL",
            "file_name": filename,
            "file_type": "FITS",
            "obs_date_utc": self.dateObs,
            "reduction_date_utc": utcnow,
            "product_desc": f"The sky background model",
            "file_path": filePath
        }, ignore_index=True)

        # WRITE CCDDATA OBJECT TO FILE
        HDUList = self.skymodelCCDData.to_hdu(
            hdu_mask='QUAL', hdu_uncertainty='ERRS', hdu_flags=None)
        HDUList[0].name = "FLUX"
        HDUList.writeto(filePath, output_verify='exception',
                        overwrite=True, checksum=True)
        print(filePath)

        filename = self.filenameTemplate.replace("_SLIT", "_SKYSUB")
        home = expanduser("~")
        outDir = self.settings["intermediate-data-root"].replace("~", home)
        filePath = f"{outDir}/{filename}"
        self.products = self.products.append({
            "soxspipe_recipe": "soxs-stare",
            "product_label": "SKY_SUBTRACTED_OBJECT",
            "file_name": filename,
            "file_type": "FITS",
            "obs_date_utc": self.dateObs,
            "reduction_date_utc": utcnow,
            "product_desc": f"The sky-subtracted object",
            "file_path": filePath
        }, ignore_index=True)
        print(filePath)

        # WRITE CCDDATA OBJECT TO FILE
        HDUList = self.skySubtractedCCDData.to_hdu(
            hdu_mask='QUAL', hdu_uncertainty='ERRS', hdu_flags=None)
        HDUList[0].name = "FLUX"
        HDUList.writeto(filePath, output_verify='exception',
                        overwrite=True, checksum=True)

        self.log.debug('completed the ``get`` method')
        return self.skymodelCCDData, self.skySubtractedCCDData, self.qc, self.products

    def get_over_sampled_sky_from_order(
            self,
            imageMapOrder,
            order,
            ignoreBP=True):
        """*unpack the over sampled sky from an order*

        **Key Arguments:**
            - ``imageMapOrder`` -- single order dataframe from object image and 2D map
            - ``order`` -- the order number
            - ``ignoreBP`` -- ignore bad-pixels? Deafult *True*

        **Return:**
            - None

        **Usage:**

        ```python
        usage code
        ```

        ---

        ```eval_rst
        .. todo::

            - add usage info
            - create a sublime snippet for usage
            - write a command-line tool for this method
            - update package tutorial with command-line tool info if needed
        ```
        """
        self.log.debug('starting the ``get_over_sampled_sky_from_order`` method')

        # MEDIAN CLIPPING FIRST USED TO CLIP MOST DEVIANT PIXELS (BAD AND CRHs)
        median_clipping_sigma = self.settings["sky-subtraction"]["median_clipping_sigma"]
        median_clipping_iterations = self.settings["sky-subtraction"]["median_clipping_iterations"]
        # ROLLING WINDOW LENGTH IN DATA POINTS
        median_rolling_window_size = self.settings["sky-subtraction"]["median_rolling_window_size"]
        # PECENTILE CLIPPING USED TO CLIP THE OBJECT(S) BEFORE FITTING A SKY MODEL
        percential_clipping_sigma = self.settings["sky-subtraction"]["percential_clipping_sigma"]
        percential_clipping_iterations = self.settings["sky-subtraction"]["percential_clipping_iterations"]
        percential_rolling_window_size = self.settings["sky-subtraction"]["percential_rolling_window_size"]

        # FINDING A DYNAMIC SIZE FOR PERCENTILE FILTERING WINDOW
        windowSize = int(len(imageMapOrder.loc[imageMapOrder["y"] == imageMapOrder["y"].median()].index))

        imageMapOrder.sort_values("wavelength", inplace=True)
        imageMapOrder["clipped"] = False

        if ignoreBP:
            # REMOVE FILTERED ROWS FROM DATA FRAME
            mask = (imageMapOrder['masked'] == True)
            imageMapOrder.drop(index=imageMapOrder[mask].index, inplace=True)

        # CLIP THE MOST DEVIANT PIXELS WITHIN A WAVELENGTH ROLLING WINDOW - BAD-PIXELS AND CRHs
        print(f'# Clipping extremely deviant pixels via a rolling wavelength window (typically bad-pixels and CRHs)')
        imageMapOrder = self.rolling_window_clipping(imageMapOrderDF=imageMapOrder, windowSize=int(median_rolling_window_size), sigma_clip_limit=median_clipping_sigma, max_iterations=median_clipping_iterations, median_centre_func=True)
        imageMapOrderWithObject = imageMapOrder.copy()

        # NOW SOME MORE ROBUST CLIPPING WITHIN A WAVELENGTH ROLLING WINDOW TO ALSO REMOVE OBJECT(S)
        print(f'# Robustly clipping deviant pixels via a rolling wavelength window (now including object(s))')
        imageMapOrder["residual_global_sigma_old"] = imageMapOrder["residual_global_sigma"]
        imageMapOrder = self.rolling_window_clipping(imageMapOrderDF=imageMapOrder, windowSize=int(percential_rolling_window_size), sigma_clip_limit=percential_clipping_sigma, max_iterations=percential_clipping_iterations)

        self.log.debug('completed the ``get_over_sampled_sky_from_order`` method')
        return imageMapOrderWithObject, imageMapOrder

    def plot_sky_sampling(
            self,
            order,
            imageMapOrderWithObjectDF,
            imageMapOrderDF):
        """*generate a plot of sky sampling*

        **Key Arguments:**
            - ``order`` -- the order number.
            - ``imageMapOrderWithObjectDF`` -- dataframe with various processed data without object clipped
            - ``imageMapOrderDF`` -- dataframe with various processed data for order

        **Return:**
            - ``filePath`` -- path to the generated QC plots PDF

        **Usage:**

        ```python
        self.plot_sky_sampling(
            order=myOrder, 
            imageMapOrderWithObjectDF=imageMapOrderWithObject, 
            imageMapOrderDF=imageMapOrder
        )
        ```
        """
        self.log.debug('starting the ``plot_sky_sampling`` method')

        # SET COLOURS FOR VARIOUS STAGES
        medianColor = "#dc322f"
        percentileColor = "#dc322f"
        skyColor = "purple"
        rawColor = "#93a1a1"
        # SET PLOT LAYER ORDERS
        medianZ = 3
        skyZ = 3
        percentileZ = 2
        unclippedZ = 1
        # SET MARKER SIZES
        rawMS = 0.5
        medianMS = 0.5
        percentileMS = 0.5

        # MAKE A COPY OF THE FRAME TO NOT ALTER ORIGINAL DATA
        frame = self.objectFrame.copy()

        # SETUP THE PLOT SUB-PANELS
        fig = plt.figure(figsize=(8, 9), constrained_layout=True, dpi=320)
        gs = fig.add_gridspec(10, 4)
        # CREATE THE GID OF AXES
        onerow = fig.add_subplot(gs[1:2, :])
        tworow = fig.add_subplot(gs[2:4, :])
        threerow = fig.add_subplot(gs[4:5:, :])
        fourrow = fig.add_subplot(gs[5:6:, :])
        fiverow = fig.add_subplot(gs[6:7:, :])
        sixrow = fig.add_subplot(gs[7:8:, :])
        sevenrow = fig.add_subplot(gs[8:9:, :])
        eightrow = fig.add_subplot(gs[9:10:, :])

        # FIND ORDER PIXELS - MASK THE REST
        nonOrderMask = np.ones_like(frame.data)
        for x, y in zip(imageMapOrderWithObjectDF["x"], imageMapOrderWithObjectDF["y"]):
            nonOrderMask[y][x] = 0

        # CONVERT TO BOOLEAN MASK AND MERGE WITH BPM
        nonOrderMask = ma.make_mask(nonOrderMask)
        combinedMask = (nonOrderMask == 1) | (frame.mask == 1)
        frame.mask = (nonOrderMask == 1)

        # RAW IMAGE PANEL
        # ROTATE THE IMAGE FOR BETTER LAYOUT
        rotatedImg = np.flipud(np.rot90(frame, 1))
        # FORCE CONVERSION OF CCDData OBJECT TO NUMPY ARRAY
        dataArray = np.asarray(frame)
        maskedDataArray = np.ma.array(frame.data, mask=combinedMask)
        std = np.nanstd(maskedDataArray)
        mean = np.nanmean(maskedDataArray)
        vmax = mean + 2 * std
        vmin = mean - 1 * std
        im = onerow.imshow(rotatedImg, vmin=vmin, vmax=vmax, cmap='gray', alpha=1)
        medianValue = np.median(rotatedImg.data.ravel())
        color = im.cmap(im.norm(medianValue))
        patches = [mpatches.Patch(color=color, label="unprocessed frame")]
        onerow.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

        onerow.set_xlabel(
            "y-axis", fontsize=10)
        onerow.set_ylabel(
            "x-axis", fontsize=10)
        ylimMinImage = imageMapOrderWithObjectDF["y"].min() - 10
        ylimMaxImage = imageMapOrderWithObjectDF["y"].max() + 10
        onerow.set_ylim(imageMapOrderWithObjectDF["x"].min() - 10, imageMapOrderWithObjectDF["x"].max() + 10)
        onerow.set_xlim(ylimMinImage, ylimMaxImage)
        # onerow.text(5, 5, 'your legend', bbox={'facecolor': 'white', 'pad': 10})
        onerow.invert_xaxis()

        # ORIGINAL DATA AND PERCENTILE SMOOTHED WAVELENGTH VS FLUX
        raw = tworow.plot(
            imageMapOrderWithObjectDF["wavelength"].values,
            imageMapOrderWithObjectDF["flux"].values, label='unprocessed (unp)', c=rawColor, zorder=0)
        # RAW MARKERS
        tworow.scatter(
            imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "wavelength"].values,
            imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "flux"].values, label='unclipped', s=rawMS, c=rawColor, alpha=0.5, zorder=unclippedZ)
        # ROBUSTLY CLIPPED
        tworow.scatter(
            imageMapOrderDF.loc[imageMapOrderDF["clipped"] == True, "wavelength"].values,
            imageMapOrderDF.loc[imageMapOrderDF["clipped"] == True, "flux"].values, label='clipped', s=percentileMS, marker="x", c=percentileColor, zorder=percentileZ, alpha=0.5)
        # MEDIAN CLIPPED
        # label='median clipped'
        label = None
        tworow.scatter(
            imageMapOrderWithObjectDF.loc[imageMapOrderWithObjectDF["clipped"] == True, "wavelength"].values,
            imageMapOrderWithObjectDF.loc[imageMapOrderWithObjectDF["clipped"] == True, "flux"].values, label=label, s=medianMS, marker="x", c=medianColor, zorder=medianZ, alpha=0.5)
        # MEDIAN LINE
        # label='median-smoothed (ms)'
        label = None
        # tworow.plot(
        #     imageMapOrderWithObjectDF.loc[imageMapOrderWithObjectDF["clipped"] == False, "wavelength"].values,
        #     imageMapOrderWithObjectDF.loc[imageMapOrderWithObjectDF["clipped"] == False, "flux_smoothed"].values, label=label, c=medianColor, zorder=medianZ)
        # PERCENTILE LINE
        tworow.plot(
            imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "wavelength"].values,
            imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "flux_smoothed"].values, label='percentile-smoothed', c=percentileColor, zorder=percentileZ)

        # SIGMA RESIDUAL
        weights = tworow.plot(
            imageMapOrderWithObjectDF.loc[imageMapOrderDF["clipped"] == False, "wavelength"].values,
            imageMapOrderWithObjectDF.loc[imageMapOrderDF["clipped"] == False, "residual_windowed_std"].values * 5 - imageMapOrderWithObjectDF.loc[imageMapOrderDF["clipped"] == False, "residual_windowed_std"].max() * 1.2, label='5$\sigma$ residual scatter (shifted)', c="#002b36")
        ylimmin = -imageMapOrderWithObjectDF.loc[imageMapOrderDF["clipped"] == False, "residual_windowed_std"].max() * 1.3
        if ylimmin < -3000:
            ylimmin = -300
        tworow.set_ylim(ylimmin, imageMapOrderWithObjectDF["flux_smoothed"].max() * 1.2)
        tworow.set_ylabel(
            "counts", fontsize=10)
        tworow.legend(loc=2, fontsize=8, bbox_to_anchor=(1.05, 1), borderaxespad=0.)
        tworow.set_xticks([], [])

        # WAVELENGTH RESIDUAL PANEL
        threerow.scatter(imageMapOrderWithObjectDF.loc[imageMapOrderWithObjectDF["clipped"] == False, "wavelength"].values, imageMapOrderWithObjectDF.loc[imageMapOrderWithObjectDF["clipped"] == False, "residual_global_sigma"].values, s=rawMS, alpha=0.5, c=rawColor, zorder=unclippedZ)
        threerow.scatter(imageMapOrderWithObjectDF.loc[imageMapOrderWithObjectDF["clipped"] == True, "wavelength"].values, imageMapOrderWithObjectDF.loc[imageMapOrderWithObjectDF["clipped"] == True, "residual_global_sigma"].values, s=medianMS, marker="x", c=medianColor, zorder=medianZ, alpha=0.5)
        threerow.scatter(imageMapOrderDF.loc[imageMapOrderDF["clipped"] == True, "wavelength"].values, imageMapOrderDF.loc[imageMapOrderDF["clipped"] == True, "residual_global_sigma_old"].values, s=percentileMS, marker="x", c=percentileColor, zorder=percentileZ, alpha=0.5)
        std = imageMapOrderWithObjectDF.loc[imageMapOrderWithObjectDF["clipped"] == False, "residual_global_sigma"].std()
        median = imageMapOrderWithObjectDF.loc[imageMapOrderWithObjectDF["clipped"] == False, "residual_global_sigma"].median()
        threerow.set_ylim(median - 3 * std, median + 7 * std)
        threerow.set_xlabel(
            "wavelength (nm)", fontsize=10)
        threerow.set_ylabel("residual ($\sigma$)", fontsize=10)

        # SLIT-POSITION RESIDUAL PANEL (SHOWING OBJECT)
        fourrow.scatter(
            imageMapOrderWithObjectDF.loc[imageMapOrderWithObjectDF["clipped"] == True, "slit_position"].values,
            imageMapOrderWithObjectDF.loc[imageMapOrderWithObjectDF["clipped"] == True, "residual_global_sigma"].values, label='deviations', s=medianMS, marker="x", c=medianColor, zorder=medianZ, alpha=0.5)
        fourrow.scatter(
            imageMapOrderDF.loc[imageMapOrderDF["clipped"] == True, "slit_position"].values,
            imageMapOrderDF.loc[imageMapOrderDF["clipped"] == True, "residual_global_sigma_old"].values, label='deviations', s=percentileMS, marker="x", c=percentileColor, zorder=percentileZ, alpha=0.5)
        fourrow.set_ylim(median - 3 * std, median + 7 * std)
        fourrow.set_xlabel(
            "slit-position relative to slit centre (arcsec)", fontsize=10)
        fourrow.set_ylabel("residual ($\sigma$)", fontsize=10)
        fourrow.scatter(
            imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "slit_position"].values,
            imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "residual_global_sigma_old"].values, label='deviations', s=rawMS, alpha=0.5, c=rawColor, zorder=unclippedZ)

        # IMAGE SHOWING CLIPPED PIXEL MASK
        im = fiverow.imshow(rotatedImg, vmin=vmin, vmax=vmax, cmap='gray', alpha=1)
        # medianValue = np.median(rotatedImg.data.ravel())
        # color = im.cmap(im.norm(medianValue))
        # patches = [mpatches.Patch(color=color, label="clipped frame")]
        # fiverow.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

        percentileClipMask = nonOrderMask
        percentileClipMask = np.zeros_like(frame.data)
        for x, y in zip(imageMapOrderDF.loc[imageMapOrderDF["clipped"] == True, "x"].values, imageMapOrderDF.loc[imageMapOrderDF["clipped"] == True, "y"].values):
            percentileClipMask[y][x] = 1
        percentileClipMask = ma.make_mask(percentileClipMask)
        imageMask = np.ma.array(np.ones_like(frame.data), mask=~percentileClipMask)
        # MAKE A COLOR MAP OF FIXED COLORS
        cmap = colors.ListedColormap([percentileColor, percentileColor])
        bounds = [0, 5, 10]
        norm = colors.BoundaryNorm(bounds, cmap.N)
        cmap.set_bad(medianColor, 0.)
        fiverow.imshow(np.flipud(np.rot90(imageMask, 1)), cmap=cmap, norm=norm, alpha=1., interpolation='nearest')
        medianClipMask = np.zeros_like(frame.data)
        for x, y in zip(imageMapOrderWithObjectDF.loc[imageMapOrderWithObjectDF["clipped"] == True, "x"].values, imageMapOrderWithObjectDF.loc[imageMapOrderWithObjectDF["clipped"] == True, "y"].values):
            medianClipMask[y][x] = 1
        medianClipMask = ma.make_mask(medianClipMask)
        imageMask = np.ma.array(np.ones_like(frame.data), mask=~medianClipMask)
        # MAKE A COLOR MAP OF FIXED COLORS
        cmap = colors.ListedColormap([medianColor, medianColor])
        bounds = [0, 5, 10]
        norm = colors.BoundaryNorm(bounds, cmap.N)
        cmap.set_bad(medianColor, 0.)
        fiverow.imshow(np.flipud(np.rot90(imageMask, 1)), cmap=cmap, norm=norm, alpha=1., interpolation='nearest')

        nonOrderMask = (nonOrderMask == 0)
        imageMask = np.ma.array(np.ones_like(frame.data), mask=nonOrderMask)
        cmap = copy(cm.gray)
        cmap.set_bad("green", 0.0)
        fiverow.imshow(np.flipud(np.rot90(imageMask, 1)), vmin=-10, vmax=-9, cmap=cmap, alpha=1.)
        fiverow.set_xlabel(
            "y-axis", fontsize=10)
        fiverow.set_ylabel(
            "x-axis", fontsize=10)
        fiverow.set_ylim(imageMapOrderWithObjectDF["x"].min() - 10, imageMapOrderWithObjectDF["x"].max() + 10)
        fiverow.set_xlim(ylimMinImage, ylimMaxImage)
        fiverow.invert_xaxis()

        # PLOT WAVELENGTH VS FLUX SKY MODEL
        sixrow.scatter(
            imageMapOrderDF["wavelength"].values,
            imageMapOrderDF["flux"].values, label='unclipped', s=rawMS, c=rawColor, alpha=0.5, zorder=unclippedZ)
        skymodel = sixrow.plot(
            imageMapOrderDF["wavelength"].values,
            imageMapOrderDF["sky_model"].values, label='sky model', c=skyColor, zorder=skyZ)
        if ylimmin < -3000:
            ylimmin = -300
        sixrow.set_ylim(ylimmin, imageMapOrderWithObjectDF["flux_smoothed"].max() * 1.2)
        sixrow.set_ylabel(
            "counts", fontsize=10)
        sixrow.legend(loc=2, fontsize=8, bbox_to_anchor=(1.05, 1), borderaxespad=0.)

        # BUILD IMAGE OF SKY MODEL
        skyModelImage = np.zeros_like(frame.data)
        for x, y, skypixel in zip(imageMapOrderDF["x"], imageMapOrderDF["y"], imageMapOrderDF["sky_model"]):
            skyModelImage[y][x] = skypixel
        nonOrderMask = (nonOrderMask == 0)
        skyModelImage = np.ma.array(skyModelImage, mask=nonOrderMask)
        cmap = copy(cm.gray)
        std = np.nanstd(skyModelImage)
        mean = np.nanmean(skyModelImage)
        vmax = mean + 2 * std
        vmin = mean - 1 * std
        im = sevenrow.imshow(np.flipud(np.rot90(skyModelImage, 1)), vmin=vmin, vmax=std, cmap=cmap, alpha=1.)
        # sevenrow.set_xlabel(
        #     "y-axis", fontsize=10)
        sevenrow.set_ylabel(
            "x-axis", fontsize=10)
        sevenrow.set_ylim(imageMapOrderWithObjectDF["x"].min() - 10, imageMapOrderWithObjectDF["x"].max() + 10)
        sevenrow.set_xlim(ylimMinImage, ylimMaxImage)
        sevenrow.invert_xaxis()
        medianValue = np.median(skyModelImage.ravel())
        color = im.cmap(im.norm(medianValue))
        patches = [mpatches.Patch(color=color, label="sky model")]
        sevenrow.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
        sevenrow.set_xticks([], [])

        # BUILD SKY-SUBTRACTED IMAGE
        skySubImage = np.zeros_like(frame.data)
        for x, y, skypixel in zip(imageMapOrderDF["x"], imageMapOrderDF["y"], imageMapOrderDF["sky_subtracted_flux"]):
            skySubImage[y][x] = skypixel
        skySubMask = (nonOrderMask == 1) | (medianClipMask == 1)
        skySubImage = np.ma.array(skySubImage, mask=skySubMask)
        cmap = copy(cm.gray)
        std = np.nanstd(skySubImage)
        mean = np.nanmedian(skySubImage)
        vmax = mean + 0.2 * std
        vmin = mean - 0.2 * std
        im = eightrow.imshow(np.flipud(np.rot90(skySubImage, 1)), vmin=vmin, vmax=std, cmap=cmap, alpha=1.)
        eightrow.set_xlabel(
            "y-axis", fontsize=10)
        eightrow.set_ylabel(
            "x-axis", fontsize=10)
        eightrow.set_ylim(imageMapOrderWithObjectDF["x"].min() - 10, imageMapOrderWithObjectDF["x"].max() + 10)
        eightrow.set_xlim(ylimMinImage, ylimMaxImage)
        eightrow.invert_xaxis()
        medianValue = np.median(skySubImage.data.ravel())
        color = im.cmap(im.norm(medianValue))
        patches = [mpatches.Patch(color=color, label="sky-subtracted frame")]
        eightrow.legend(handles=patches, bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)

        fig.suptitle(f"{self.arm} sky model: order {order}", fontsize=12, y=0.97)

        filename = self.filenameTemplate.split("SLIT")[0] + f"SKYMODEL_QC_PLOTS_ORDER_{int(order)}.pdf"
        home = expanduser("~")
        outDir = self.settings["intermediate-data-root"].replace("~", home)
        filePath = f"{outDir}/{filename}"
        plt.savefig(filePath, dpi='figure')

        self.log.debug('completed the ``plot_sky_sampling`` method')
        return filePath

    def rolling_window_clipping(
            self,
            imageMapOrderDF,
            windowSize,
            sigma_clip_limit=5,
            max_iterations=10,
            median_centre_func=False):
        """*clip pixels in a rolling wavelength window*

        **Key Arguments:**
            - ``imageMapOrderDF`` --  dataframe with various processed data for a given order
            - ``windowSize`` -- the window-size used to perform rolling window clipping (number of data-points)
            - ``sigma_clip_limit`` -- clip data values straying beyond this sigma limit. Default *5*
            - ``max_iterations`` -- maximum number of iterations when clipping
            - ``median_centre_func`` -- use a median centre function for rolling window instead of quantile (use to clip most deviate pixels only). Default *False*

        **Return:**
            - ``imageMapOrderDF`` -- image order dataframe with 'clipped' == True for those pixels that have been clipped via rolling window clipping

        **Usage:**

        ```python
        imageMapOrder = self.rolling_window_clipping(
            imageMapOrderDF=imageMapOrder,
            windowSize=23,
            sigma_clip_limit=4,
            max_iterations=10,
            median_centre_func=True
        )
        ```
        """
        self.log.debug('starting the ``rolling_window_clipping`` method')

        maxiterations = 10
        i = 1
        newlyClipped = -1
        allPixels = len(imageMapOrderDF.index)

        while i <= max_iterations:

            # CALCULATE PERCENTILE SMOOTH DATA & RESIDUALS
            if i == 1:
                if median_centre_func:
                    imageMapOrderDF["flux_smoothed"] = imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "flux"].rolling(window=windowSize, center=True).median()
                else:
                    imageMapOrderDF["flux_smoothed"] = imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "flux"].rolling(window=windowSize, center=True).quantile(.3)

            imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "flux_minus_smoothed_residual"] = imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "flux"] - imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "flux_smoothed"]
            imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "residual_windowed_std"] = imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "flux_minus_smoothed_residual"].rolling(windowSize).std()
            imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "residual_windowed_sigma"] = imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "flux_minus_smoothed_residual"] / imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "residual_windowed_std"]

            if median_centre_func:
                # CLIP ABOVE AND BELOW
                imageMapOrderDF.loc[imageMapOrderDF["residual_windowed_sigma"].abs() > sigma_clip_limit, "clipped"] = True
            else:
                # CLIP ONLY HIGH VALUES
                imageMapOrderDF.loc[imageMapOrderDF["residual_windowed_sigma"] > sigma_clip_limit, "clipped"] = True

            if newlyClipped == -1:
                totalClipped = len(imageMapOrderDF.loc[imageMapOrderDF["clipped"] == True].index)
                newlyClipped = totalClipped
            else:
                newlyClipped = len(imageMapOrderDF.loc[imageMapOrderDF["clipped"] == True].index) - totalClipped
                totalClipped = len(imageMapOrderDF.loc[imageMapOrderDF["clipped"] == True].index)
            if i > 1:
                # Cursor up one line and clear line
                sys.stdout.write("\x1b[1A\x1b[2K")
            percent = (float(totalClipped) / float(allPixels)) * 100.
            print(f'\tITERATION {i}: {newlyClipped} deviant pixels have been newly clipped within a {windowSize} data-point rolling window ({totalClipped} pixels clipped in total = {percent:1.1f}%)')
            if newlyClipped == 0:
                break
            i += 1

        imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "flux_scatter_windowed_std"] = imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "flux"].rolling(windowSize).std()
        std = imageMapOrderDF.loc[imageMapOrderDF["clipped"] == False, "flux_minus_smoothed_residual"].std()
        imageMapOrderDF["residual_global_sigma"] = imageMapOrderDF["flux_minus_smoothed_residual"] / std

        self.log.debug('completed the ``rolling_window_clipping`` method')
        return imageMapOrderDF

    def fit_bspline_to_sky(
            self,
            imageMapOrder,
            order):
        """*fit a bspline to the unclipped sky pixels (wavelength vs flux)*

        **Key Arguments:**
            - ``imageMapOrder`` -- single order dataframe, containing sky flux with object(s) and CRHs removed
            - ``order`` -- the order number

        **Return:**
            - ``imageMapOrder`` -- same `imageMapOrder` as input but now with `sky_model` (bspline fit of the sky) and `sky_subtracted_flux` columns 

        **Usage:**

        ```python
        imageMapOrder = self.fit_bspline_to_sky(
            imageMapOrder,
            myOrder
        )
        ```

        """
        self.log.debug('starting the ``fit_bspline_to_sky`` method')

        goodWl = imageMapOrder.loc[imageMapOrder["clipped"] == False]["wavelength"]
        goodFlux = imageMapOrder.loc[imageMapOrder["clipped"] == False]["flux"]
        imageMapOrder["weights"] = 1 / imageMapOrder["flux_scatter_windowed_std"].abs()
        imageMapOrder["weights"] = imageMapOrder["weights"].replace(np.nan, 0)
        goodWeights = imageMapOrder.loc[imageMapOrder["clipped"] == False, "weights"]

        rowFitOrder = 3
        xmin, xmax = goodWl.min(), goodWl.max()

        N = int(goodWl.shape[0] / 25)
        seedKnots = np.linspace(xmin, xmax, N)

        # t for knots
        # c of coefficients
        # k for order
        t, c, k = splrep(goodWl, goodFlux, t=seedKnots[1:-1], w=goodWeights, s=0.0, k=rowFitOrder, task=-1)
        spline = BSpline(t, c, k, extrapolate=True)

        imageMapOrder["sky_model"] = spline(imageMapOrder["wavelength"].values)
        imageMapOrder["sky_subtracted_flux"] = imageMapOrder["flux"] - imageMapOrder["sky_model"]

        self.log.debug('completed the ``fit_bspline_to_sky`` method')
        return imageMapOrder

    def create_placeholder_images(
            self):
        """*create placeholder images for the sky model and sky-subtracted frame*

        **Key Arguments:**
            # -

        **Return:**
            - ``skymodelCCDData`` -- placeholder for sky model image
            - ``skySubtractedCCDData`` -- placeholder for sky-subtracted image


        **Usage:**

        ```python
        skymodelCCDData, skySubtractedCCDData = self.create_placeholder_images()
        ```
        """
        self.log.debug('starting the ``create_placeholder_images`` method')

        # CREATE AN IMAGE ARRAY TO HOST WAVELENGTH AND SLIT-POSITIONS
        skymodelCCDData = self.objectFrame.copy()
        skymodelCCDData.data[:] = np.nan
        skySubtractedCCDData = skymodelCCDData.copy()

        self.log.debug('completed the ``create_placeholder_images`` method')
        return skymodelCCDData, skySubtractedCCDData

    def add_data_to_placeholder_images(
            self,
            imageMapOrderDF):
        """*add sky-model and sky-subtracted data to placeholder images*

        **Key Arguments:**
            - ``imageMapOrderDF`` -- single order dataframe from object image and 2D map

        **Usage:**

        ```python
        self.add_data_to_placeholder_images(imageMapOrder)
        ```
        """
        self.log.debug('starting the ``add_data_to_placeholder_images`` method')

        for x, y, skypixel in zip(imageMapOrderDF["x"], imageMapOrderDF["y"], imageMapOrderDF["sky_model"]):
            self.skymodelCCDData.data[y][x] = skypixel
        for x, y, skypixel in zip(imageMapOrderDF["x"], imageMapOrderDF["y"], imageMapOrderDF["sky_subtracted_flux"]):
            self.skySubtractedCCDData.data[y][x] = skypixel

        self.log.debug('completed the ``add_data_to_placeholder_images`` method')
        return None

    # use the tab-trigger below for new method
    # xt-class-method
