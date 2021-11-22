#!/usr/bin/env python
# encoding: utf-8
"""
*reduce science frames take in soxs stare mode*

:Author:
    David Young & Marco Landoni

:Date Created:
    October 18, 2021
"""
################# GLOBAL IMPORTS ####################
from builtins import object
import sys
import os
os.environ['TERM'] = 'vt100'
from fundamentals import tools
from soxspipe.commonutils import set_of_files
from ._base_recipe_ import _base_recipe_
import numpy as np
from astropy.nddata import CCDData
import ccdproc
from astropy import units as u
from soxspipe.commonutils import keyword_lookup


class soxs_stare_mode(_base_recipe_):
    """
    *The soxs_stare_mode recipe*

    **Key Arguments**

        - ``log`` -- logger
        - ``settings`` -- the settings dictionary
        - ``inputFrames`` -- input fits frames. Can be a directory, a set-of-files (SOF) file or a list of fits frame paths.   


    See `produce_product` method for usage.

    ```eval_rst
    .. todo::

        - add usage info
        - create a sublime snippet for usage
        - create cl-util for this class
        - add a tutorial about ``soxs_stare_mode`` to documentation
    ```
    """
    # Initialisation

    def __init__(
            self,
            log,
            settings=False,
            inputFrames=[],
            verbose=False

    ):
        # INHERIT INITIALISATION FROM  _base_recipe_
        super(soxs_stare_mode, self).__init__(
            log=log, settings=settings)
        self.log = log
        log.debug("instansiating a new 'soxs_stare_mode' object")
        self.settings = settings
        self.inputFrames = inputFrames
        self.verbose = verbose
        self.recipeName = "soxs-soxs-stare"
        self.recipeSettings = settings[self.recipeName]
        # xt-self-arg-tmpx

        # INITIAL ACTIONS
        # CONVERT INPUT FILES TO A CCDPROC IMAGE COLLECTION (inputFrames >
        # imagefilecollection)
        sof = set_of_files(
            log=self.log,
            settings=self.settings,
            inputFrames=self.inputFrames
        )
        self.inputFrames, self.supplementaryInput = sof.get()

        # VERIFY THE FRAMES ARE THE ONES EXPECTED BY soxs_stare_mode - NO MORE, NO LESS.
        # PRINT SUMMARY OF FILES.
        print("# VERIFYING INPUT FRAMES")
        self.verify_input_frames()
        sys.stdout.write("\x1b[1A\x1b[2K")
        print("# VERIFYING INPUT FRAMES - ALL GOOD")

        # SORT IMAGE COLLECTION
        self.inputFrames.sort(['mjd-obs'])
        if self.verbose:
            print("# RAW INPUT FRAMES - SUMMARY")
            print(self.inputFrames.summary, "\n")

        # PREPARE THE FRAMES - CONVERT TO ELECTRONS, ADD UNCERTAINTY AND MASK
        # EXTENSIONS
        self.inputFrames = self.prepare_frames(
            save=self.settings["save-intermediate-products"])

        return None

    def verify_input_frames(
            self):
        """*verify the input frame match those required by the soxs_stare_mode recipe*

        **Return:**
            - ``None``

        If the fits files conform to required input for the recipe everything will pass silently, otherwise an exception shall be raised.
        """
        self.log.debug('starting the ``verify_input_frames`` method')

        kw = self.kw

        # BASIC VERIFICATION COMMON TO ALL RECIPES
        self._verify_input_frames_basics()

        imageTypes = self.inputFrames.values(
            keyword=kw("DPR_TYPE").lower(), unique=True)
        imageTech = self.inputFrames.values(
            keyword=kw("DPR_TECH").lower(), unique=True)
        imageCat = self.inputFrames.values(
            keyword=kw("DPR_CATG").lower(), unique=True)

        if self.arm == "NIR":
            # WANT ON AND OFF PINHOLE FRAMES
            # MIXED INPUT IMAGE TYPES ARE BAD
            if len(imageTypes) > 1:
                imageTypes = " and ".join(imageTypes)
                print(self.inputFrames.summary)
                raise TypeError(
                    "Input frames are a mix of %(imageTypes)s" % locals())

            if imageTypes[0] != "LAMP,FMTCHK":
                raise TypeError(
                    "Input frames for soxspipe soxs_stare_mode need to be ********* lamp on and lamp off frames for NIR" % locals())

            for i in imageTech:
                if i not in ['ECHELLE,PINHOLE', 'IMAGE']:
                    raise TypeError(
                        "Input frames for soxspipe soxs_stare_mode need to be ********* lamp on and lamp off frames for NIR" % locals())

        else:
            for i in imageTypes:
                if i not in ["LAMP,FMTCHK", "BIAS", "DARK"]:
                    raise TypeError(
                        "Input frames for soxspipe soxs_stare_mode need to be ********* and a master-bias and possibly a master dark for UVB/VIS" % locals())

        # LOOK FOR ****
        arm = self.arm
        if arm not in self.supplementaryInput or "DISP_MAP" not in self.supplementaryInput[arm]:
            raise TypeError(
                "Need a **** for %(arm)s - none found with the input files" % locals())

        self.imageType = imageTypes[0]
        self.log.debug('completed the ``verify_input_frames`` method')
        return None

    def produce_product(
            self):
        """*The code to generate the product of the soxs_stare_mode recipe*

        **Return:**
            - ``productPath`` -- the path to the final product

        **Usage**

        ```python
        from soxspipe.recipes import soxs_stare_mode
        recipe = soxs_stare_mode(
            log=log,
            settings=settings,
            inputFrames=fileList
        )
        soxs_stare_modeFrame = recipe.produce_product()
        ```
        """
        self.log.debug('starting the ``produce_product`` method')

        arm = self.arm
        kw = self.kw
        dp = self.detectorParams

        productPath = None

        self.clean_up()

        self.log.debug('completed the ``produce_product`` method')
        return productPath

    # use the tab-trigger below for new method
    # xt-class-method

    # Override Method Attributes
    # method-override-tmpx
