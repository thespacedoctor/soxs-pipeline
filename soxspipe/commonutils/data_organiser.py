#!/usr/bin/env python
# encoding: utf-8
"""
*The SOXSPIPE Data Organiser*

:Author:
    David Young

:Date Created:
    March  9, 2023
"""
from fundamentals import tools
from builtins import object
import sys
import os
from soxspipe.commonutils.toolkit import get_calibrations_path
os.environ['TERM'] = 'vt100'


# OR YOU CAN REMOVE THE CLASS BELOW AND ADD A WORKER FUNCTION ... SNIPPET TRIGGER BELOW
# xt-worker-def

class data_organiser(object):
    """
    *The worker class for the data_organiser module*

    **Key Arguments:**
        - ``log`` -- logger
        - ``settings`` -- the settings dictionary
        - ``rootDir`` -- the root directory of the data to process

    **Usage:**

    To setup your logger, settings and database connections, please use the ``fundamentals`` package (`see tutorial here <http://fundamentals.readthedocs.io/en/latest/#tutorial>`_). 

    To initiate a data_organiser object, use the following:

    ```eval_rst
    .. todo::

        - add usage info
        - create a sublime snippet for usage
        - create cl-util for this class
        - add a tutorial about ``data_organiser`` to documentation
        - create a blog post about what ``data_organiser`` does
    ```

    ```python
    usage code 
    ```

    """
    # Initialisation
    # 1. @flagged: what are the unique attrributes for each object? Add them
    # to __init__

    def __init__(
            self,
            log,
            rootDir,
            settings=False
    ):

        import shutil

        self.log = log
        log.debug("instansiating a new 'data_organiser' object")
        self.settings = settings
        self.rootDir = rootDir

        # xt-self-arg-tmpx

        # TEST FOR SQLITE DATABASE
        self.dbPath = rootDir + "/soxspipe.db"
        try:
            with open(self.dbPath):
                pass
            self.freshRun = False
        except IOError:
            self.freshRun = True
            emptyDb = os.path.dirname(os.path.dirname(__file__)) + "/resources/soxspipe.db"
            shutil.copyfile(emptyDb, self.dbPath)
            print("soxspipe.db does not yet exist, this is a fresh reduction")

        # HERE ARE THE KEYS WE WANT PRESENTED IN THE SUMMARY OUTPUT TABLES
        self.keywords = [
            'file',
            'mjd-obs',
            'date-obs',
            'eso seq arm',
            'eso dpr catg',
            'eso dpr tech',
            'eso dpr type',
            'eso pro catg',
            'eso pro tech',
            'eso pro type',
            'exptime',
            'cdelt1',
            'cdelt2',
            'eso det read speed',
            'eso ins opti3 name',
            'eso ins opti4 name',
            'eso ins opti5 name',
            'eso det ncorrs name',
            'eso det out1 conad',
            'eso det out1 ron',
            "naxis",
            "object"
        ]

        # THE MINIMUM SET OF KEYWORD WE EVER WANT RETURNED
        self.keywordsTerse = [
            'file',
            'eso seq arm',
            'eso dpr catg',
            'eso dpr type',
            'eso dpr tech',
            'eso pro catg',
            'eso pro tech',
            'eso pro type',
            'exptime',
            'binning',
            'rospeed',
            'night-start-date',
            'night-start-mjd',
            'mjd-obs',
            'object'
        ]

        self.recipeMap = {
            "bias": "mbias",
            "dark": "mdark",
            "lamp,fmtchk": "disp_sol",
            "lamp,orderdef": "order_centres",
            "lamp,dorderdef": "order_centres",
            "lamp,qorderdef": "order_centres",
            "lamp,flat": "mflat",
            "lamp,wave": "spat_sol",
            "object": "stare",
            "std,flux": "stare"
        }

        # THESE ARE KEYS WE NEED TO FILTER ON, AND SO NEED TO CREATE ASTROPY TABLE
        # INDEXES
        self.filterKeywords = ['eso seq arm', 'eso dpr catg',
                               'eso dpr tech', 'eso dpr type', 'eso pro catg', 'eso pro tech', 'eso pro type', 'exptime', 'rospeed', 'binning', 'night-start-mjd']

        return None

    # 4. @flagged: what actions does each object have to be able to perform? Add them here
    # Method Attributes
    def get(self):
        """
        *get the data_organiser object*

        **Return:**
            - ``data_organiser``

        **Usage:**

        ```eval_rst
        .. todo::

            - add usage info
            - create a sublime snippet for usage
            - create cl-util for this method
            - update the package tutorial if needed
        ```

        ```python
        usage code 
        ```
        """
        self.log.debug('starting the ``get`` method')

        data_organiser = None

        self.log.debug('completed the ``get`` method')
        return data_organiser

    def sync_raw_frames(
            self):
        """*sync the raw frames between the project folder and the database *

        **Key Arguments:**
            # -

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
        self.log.debug('starting the ``sync_raw_frames`` method')

        from astropy.table import Table, unique
        import numpy as np
        import pandas as pd
        from tabulate import tabulate
        import sqlite3 as sql

        # GENERATE AN ASTROPY TABLES OF FITS FRAMES WITH ALL INDEXES NEEDED
        filteredFrames, fitsPaths, fitsNames = self.create_directory_table(pathToDirectory=self.rootDir, keys=self.keywords, filterKeys=self.filterKeywords)
        filteredFrames = filteredFrames.to_pandas(index=False)

        # SPLIT INTO RAW, REDUCED PIXELS, REDUCED TABLES
        proKeywords = ['eso pro type', 'eso pro tech', 'eso pro catg']
        keywordsTerseRaw = self.keywordsTerse[:]
        keywordsTerseReduced = self.keywordsTerse[:]
        filterKeywordsRaw = self.filterKeywords[:]
        filterKeywordsReduced = self.filterKeywords[:]

        mask = []
        for i in proKeywords:
            keywordsTerseRaw.remove(i)
            filterKeywordsRaw.remove(i)
            if not len(mask):
                mask = (filteredFrames[i] == "--")
            else:
                mask = np.logical_and(mask, (filteredFrames[i] == "--"))

        rawFrames = filteredFrames.loc[mask]
        pd.options.display.float_format = '{:,.4f}'.format

        rawGroups = rawFrames.groupby(filterKeywordsRaw).size().reset_index(name='counts')
        rawGroups.style.hide_index()
        pd.options.mode.chained_assignment = None
        if len(rawGroups.index):
            print("\n## RAW FRAME-SET SUMMARY\n")
            print(tabulate(rawGroups, headers='keys', tablefmt='github', showindex=False, stralign="right"))

        dprKeywords = ['eso dpr type', 'eso dpr tech', 'eso dpr catg']
        for i in dprKeywords:
            keywordsTerseReduced.remove(i)
            filterKeywordsReduced.remove(i)
        filterKeywordsReducedTable = filterKeywordsReduced[:]
        filterKeywordsReducedTable.remove("binning")
        keywordsTerseReducedTable = keywordsTerseReduced[:]
        keywordsTerseReducedTable.remove("binning")

        print("\n# CONTENT FILE INDEX\n")
        if len(rawGroups.index):
            print("\n## ALL RAW FRAMES\n")
            print(tabulate(rawFrames[keywordsTerseRaw], headers='keys', tablefmt='github', showindex=False, stralign="right", floatfmt=".3f"))
            # CONNECT TO THE DATABASE
            conn = sql.connect(self.dbPath)
            # SEND TO DATABASE
            rawFrames[keywordsTerseRaw].replace(['--'], None).to_sql('raw_frames', con=conn,
                                                                     index=False, if_exists='append')

        self.log.debug('completed the ``sync_raw_frames`` method')
        return None

    def create_directory_table(
            self,
            pathToDirectory,
            keys,
            filterKeys):
        """*create an astropy table based on the contents of a directory*

        **Key Arguments:**

        - `log` -- logger
        - `pathToDirectory` -- path to the directory containing the FITS frames
        - `keys` -- the keys needed to be returned for the imageFileCollection
        - `filterKeys` -- these are the keywords we want to filter on later

        **Return**

        - `masterTable` -- the primary astropy table listing all FITS files in the directory (including indexes on `filterKeys` columns)
        - `fitsPaths` -- a simple list of all FITS file paths
        - `fitsNames` -- a simple list of all FITS file name

        **Usage:**

        ```python
        # GENERATE AN ASTROPY TABLES OF FITS FRAMES WITH ALL INDEXES NEEDED
        masterTable, fitsPaths, fitsNames = create_directory_table(
            log=log,
            pathToDirectory="/my/directory/path",
            keys=["file","mjd-obs", "exptime","cdelt1", "cdelt2"],
            filterKeys=["mjd-obs","exptime"]
        )
        ```
        """
        self.log.debug('starting the ``create_directory_table`` function')

        from ccdproc import ImageFileCollection
        from astropy.time import Time, TimeDelta
        import numpy as np

        # GENERATE A LIST OF FITS FILE PATHS
        fitsPaths = []
        fitsNames = []
        for d in os.listdir(pathToDirectory):
            filepath = os.path.join(pathToDirectory, d)
            if os.path.isfile(filepath) and (os.path.splitext(filepath)[1] == ".fits" or ".fits.Z" in filepath):
                fitsPaths.append(filepath)
                fitsNames.append(d)

        recursive = False
        for d in os.listdir(pathToDirectory):
            if os.path.isdir(os.path.join(pathToDirectory, d)) and d in ('raw_frames', 'product'):
                recursive = True
                theseFiles = recursive_directory_listing(
                    log=log,
                    baseFolderPath=os.path.join(pathToDirectory, d),
                    whatToList="files"  # all | files | dirs
                )
                newFitsPaths = [n for n in theseFiles if ".fits" in n]
                newFitsNames = [os.path.basename(n) for n in theseFiles if ".fits" in n]
                fitsPaths += newFitsPaths
                fitsNames += newFitsNames

        if len(fitsPaths) == 0:
            print(f"No fits files found in directory `{pathToDirectory}`")
            return None, None, None

        # TOP-LEVEL COLLECTION
        if recursive:
            allFrames = ImageFileCollection(filenames=fitsPaths, keywords=keys)
        else:
            allFrames = ImageFileCollection(
                location=pathToDirectory, filenames=fitsNames, keywords=keys)
        masterTable = allFrames.summary

        # ADD FILLED VALUES FOR MISSING CELLS
        for fil in keys:
            if fil in filterKeys and fil not in ["exptime"]:

                try:
                    masterTable[fil].fill_value = "--"
                except:
                    masterTable.replace_column(fil, masterTable[fil].astype(str))
                    masterTable[fil].fill_value = "--"
            # elif fil in ["exptime"]:
            #     masterTable[fil].fill_value = "--"
            else:
                try:
                    masterTable[fil].fill_value = -99.99
                except:
                    masterTable[fil].fill_value = "--"
        masterTable = masterTable.filled()

        # SETUP A NEW COLUMN GIVING THE INT MJD THE CHILEAN NIGHT BEGAN ON
        # 12:00 NOON IN CHILE IS TYPICALLY AT 16:00 UTC
        # SO COUNT CHILEAN OBSERVING NIGHTS AS 15:00 UTC-15:00 UTC (11am-11am)
        if "mjd-obs" in masterTable.colnames:
            chile_offset = TimeDelta(4.0 * 60 * 60, format='sec')
            night_start_offset = TimeDelta(15.0 * 60 * 60, format='sec')
            chileTimes = Time(masterTable["mjd-obs"],
                              format='mjd', scale='utc') - chile_offset
            startNightDate = Time(masterTable["mjd-obs"],
                                  format='mjd', scale='utc') - night_start_offset
            # masterTable["utc-4hrs"] = (masterTable["mjd-obs"] - 2 / 3).astype(int)
            masterTable["utc-4hrs"] = chileTimes.strftime("%Y-%m-%dt%H:%M:%S")
            masterTable["night-start-date"] = startNightDate.strftime("%Y-%m-%d")
            masterTable["night-start-mjd"] = startNightDate.mjd.astype(int)
            masterTable.add_index("night-start-date")
            masterTable.add_index("night-start-mjd")

        if "eso det read speed" in masterTable.colnames:
            masterTable["rospeed"] = np.copy(masterTable["eso det read speed"])
            masterTable["rospeed"][masterTable[
                "rospeed"] == -99.99] = '--'
            masterTable["rospeed"][masterTable[
                "rospeed"] == '1pt/400k/lg'] = 'fast'
            masterTable["rospeed"][masterTable[
                "rospeed"] == '1pt/400k/lg/AFC'] = 'fast'
            masterTable["rospeed"][masterTable[
                "rospeed"] == '1pt/100k/hg'] = 'slow'
            masterTable["rospeed"][masterTable[
                "rospeed"] == '1pt/100k/hg/AFC'] = 'slow'
            masterTable.add_index("rospeed")

        if "naxis" in masterTable.colnames:
            masterTable["table"] = np.copy(masterTable["naxis"]).astype(str)
            masterTable["table"][masterTable[
                "table"] == '0'] = 'T'
            masterTable["table"][masterTable[
                "table"] != 'T'] = 'F'

        if "cdelt2" in masterTable.colnames:
            masterTable["binning"] = np.core.defchararray.add(
                masterTable["cdelt1"].astype('int').astype('str'), "x")
            masterTable["binning"] = np.core.defchararray.add(masterTable["binning"],
                                                              masterTable["cdelt2"].astype('int').astype('str'))
            masterTable["binning"][masterTable[
                "binning"] == '-99x-99'] = '--'
            masterTable["binning"][masterTable[
                "binning"] == '1x-99'] = '--'
            masterTable.add_index("binning")

            # myArray[myArray < 10.] = -99

        # ADD INDEXES ON ALL KEYS
        for k in keys:
            try:
                masterTable.add_index(k)
            except:
                pass

        # SORT IMAGE COLLECTION
        masterTable.sort(['eso pro type', 'eso seq arm', 'eso dpr catg', 'eso dpr tech', 'eso dpr type', 'eso pro catg', 'eso pro tech', 'mjd-obs'])

        self.log.debug('completed the ``create_directory_table`` function')
        return masterTable, fitsPaths, fitsNames

    # use the tab-trigger below for new method
    # xt-class-method

    # 5. @flagged: what actions of the base class(es) need ammending? ammend them here
    # Override Method Attributes
    # method-override-tmpx
