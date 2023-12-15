
#!/usr/bin/env python
# encoding: utf-8
"""
Documentation for soxspipe can be found here: http://soxspipe.readthedocs.org

Usage:
    soxspipe prep <workspaceDirectory>
    soxspipe session ((ls|new|<sessionId>)|new <sessionId>)
    soxspipe [-Vx] mbias <inputFrames> [-o <outputDirectory> -s <pathToSettingsFile>]
    soxspipe [-Vx] mdark <inputFrames> [-o <outputDirectory> -s <pathToSettingsFile>]
    soxspipe [-Vx] disp_sol <inputFrames> [-o <outputDirectory> -s <pathToSettingsFile>]
    soxspipe [-Vx] order_centres <inputFrames> [-o <outputDirectory> -s <pathToSettingsFile>]
    soxspipe [-Vx] mflat <inputFrames> [-o <outputDirectory> -s <pathToSettingsFile>]
    soxspipe [-Vx] spat_sol <inputFrames> [-o <outputDirectory> -s <pathToSettingsFile>]
    soxspipe [-Vx] stare <inputFrames> [-o <outputDirectory> -s <pathToSettingsFile>]

Options:
    prep                                   prepare a folder of raw data (workspace) for data reduction
    session ls                             list all available data-reduction sessions in the workspace
    session new [<sessionId>]              start a new data-reduction session, optionally give a name up to 16 characters A-Z, a-z, 0-9 and/or _-
    session <sessionId>                    use an existing data-reduction session (use `session ls` to see all IDs)
    mbias                                  the master bias recipe
    mdark                                  the master dark recipe
    mflat                                  the master flat recipe
    disp_sol                               the disp solution recipe
    order_centres                          the order centres recipe
    spat_sol                               the spatial solution recipe
    stare                                  reduce stare mode science frames

    inputFrames                            path to a directory of frames or a set-of-files file

    -h, --help                             show this help message
    -v, --version                          show version
    -s, --settings <pathToSettingsFile>    the settings file
    -V, --verbose                          more verbose output
    -x, --overwrite                        more verbose output
"""
################# GLOBAL IMPORTS ####################
import os
import sys
import readline
import glob
from docopt import docopt
from fundamentals import tools, times
from subprocess import Popen, PIPE, STDOUT
os.environ['TERM'] = 'vt100'


def tab_complete(text, state):
    return (glob.glob(text + '*') + [None])[state]


def main(arguments=None):
    """
    *The main function used when `cl_utils.py` is run as a single script from the cl, or when installed as a cl command*
    """

    # DETERMINE CURRENT DATA-REDUCTION SESSION
    from fundamentals.logs import emptyLogger
    from soxspipe.commonutils import data_organiser
    eLog = emptyLogger()
    do = data_organiser(
        log=eLog,
        rootDir="."
    )
    currentSession, allSessions = do.session_list(silent=True)

    # QUICKLY SKIP IF PRODUCT EXIST
    if len(sys.argv[1:]) == 2:
        if sys.argv[2].split(".")[-1].lower() == "sof":
            from soxspipe.commonutils import toolkit
            productPath = toolkit.predict_product_path(sys.argv[2])
            if os.path.exists(productPath):
                print(f"The product of this recipe already exists at '{productPath}'. To overwrite this product, rerun the pipeline command with the overwrite flag (-x).")
                sys.exit(0)

    clCommand = sys.argv[0].split("/")[-1] + " " + " ".join(sys.argv[1:])

    # setup the command-line util settings
    arguments = None
    if "-s" not in sys.argv and "prep" not in sys.argv and "session" not in sys.argv and currentSession:
        settingsFile = f"./sessions/{currentSession}/soxspipe.yaml"
        exists = os.path.exists(settingsFile)
        sys.argv.append("-s")
        sys.argv.append(settingsFile)

    su = tools(
        arguments=None,
        docString=__doc__,
        logLevel="WARNING",
        options_first=False,
        projectName="soxspipe",
        defaultSettingsFile=True
    )
    arguments, settings, log, dbConn = su.setup()

    # SET ASTROPY LOGGING LEVEL
    try:
        from astropy import log as astrolog
        astrolog.setLevel("WARNING")
    except:
        pass

    # tab completion for raw_input
    readline.set_completer_delims(' \t\n;')
    readline.parse_and_bind("tab: complete")
    readline.set_completer(tab_complete)

    # UNPACK REMAINING CL ARGUMENTS USING `EXEC` TO SETUP THE VARIABLE NAMES
    # AUTOMATICALLY
    a = {}
    for arg, val in list(arguments.items()):
        if arg[0] == "-":
            varname = arg.replace("-", "") + "Flag"
        else:
            varname = arg.replace("<", "").replace(">", "")
        a[varname] = val
        if arg == "--dbConn":
            dbConn = val
            a["dbConn"] = val
        log.debug('%s = %s' % (varname, val,))

    ## START LOGGING ##
    startTime = times.get_now_sql_datetime()
    log.debug(
        '--- STARTING TO RUN THE cl_utils.py AT %s' %
        (startTime,))

    # set options interactively if user requests
    if "interactiveFlag" in a and a["interactiveFlag"]:

        # load previous settings
        moduleDirectory = os.path.dirname(__file__) + "/resources"
        pathToPickleFile = "%(moduleDirectory)s/previousSettings.p" % locals()
        try:
            with open(pathToPickleFile):
                pass
            previousSettingsExist = True
        except:
            previousSettingsExist = False
        previousSettings = {}
        if previousSettingsExist:
            previousSettings = pickle.load(open(pathToPickleFile, "rb"))

        # x-raw-input
        # x-boolean-raw-input
        # x-raw-input-with-default-value-from-previous-settings

        # save the most recently used requests
        pickleMeObjects = []
        pickleMe = {}
        theseLocals = locals()
        for k in pickleMeObjects:
            pickleMe[k] = theseLocals[k]
        pickle.dump(pickleMe, open(pathToPickleFile, "wb"))

    verbose = a['verboseFlag']

    try:
        # PACK UP SOME OF THE CL SWITCHES INTO SETTINGS DICTIONARY
        if a['outputDirectory']:
            settings["workspace-root-dir"] = a['outputDirectory']
        else:
            from soxspipe.commonutils import data_organiser
            do = data_organiser(
                log=log,
                rootDir="."
            )
            currentSession, allSessions = do.session_list(silent=True)
            if currentSession:
                settings["workspace-root-dir"] = f"./sessions/{currentSession}/"

        if a["mbias"]:
            from soxspipe.recipes import soxs_mbias
            recipe = soxs_mbias(
                log=log,
                settings=settings,
                inputFrames=a["inputFrames"],
                verbose=verbose,
                overwrite=a["overwriteFlag"]
            )
            mbiasFrame = recipe.produce_product()

        if a["mdark"]:
            from soxspipe.recipes import soxs_mdark
            recipe = soxs_mdark(
                log=log,
                settings=settings,
                inputFrames=a["inputFrames"],
                verbose=verbose,
                overwrite=a["overwriteFlag"]
            )
            mdarkFrame = recipe.produce_product()

        if a["disp_sol"]:
            from soxspipe.recipes import soxs_disp_solution
            disp_map = soxs_disp_solution(
                log=log,
                settings=settings,
                inputFrames=a["inputFrames"],
                verbose=verbose,
                overwrite=a["overwriteFlag"]
            ).produce_product()

        if a["order_centres"]:
            from soxspipe.recipes import soxs_order_centres
            order_table = soxs_order_centres(
                log=log,
                settings=settings,
                inputFrames=a["inputFrames"],
                verbose=verbose,
                overwrite=a["overwriteFlag"]
            ).produce_product()

        if a["spat_sol"]:
            from soxspipe.recipes import soxs_spatial_solution
            disp_map, mapImage2D, res_plots = soxs_spatial_solution(
                log=log,
                settings=settings,
                inputFrames=a["inputFrames"],
                verbose=verbose,
                overwrite=a["overwriteFlag"]
            ).produce_product()

        if a["mflat"]:
            from soxspipe.recipes import soxs_mflat
            recipe = soxs_mflat(
                log=log,
                settings=settings,
                inputFrames=a["inputFrames"],
                verbose=verbose,
                overwrite=a["overwriteFlag"]
            )
            mflatFrame = recipe.produce_product()

        if a["stare"]:
            from soxspipe.recipes import soxs_stare
            recipe = soxs_stare(
                log=log,
                settings=settings,
                inputFrames=a["inputFrames"],
                verbose=verbose,
                overwrite=a["overwriteFlag"]
            )

            reducedStare = recipe.produce_product()

        if a['prep']:
            from soxspipe.commonutils import data_organiser
            do = data_organiser(
                log=log,
                rootDir=a["workspaceDirectory"]
            )
            do.prepare()

        if a['session'] and a['ls']:
            from soxspipe.commonutils import data_organiser
            do = data_organiser(
                log=log,
                rootDir="."
            )
            currentSession, allSessions = do.session_list()

        if a['session'] and a['sessionId'] and not a['new']:
            from soxspipe.commonutils import data_organiser
            do = data_organiser(
                log=log,
                rootDir="."
            )
            do.session_switch(a['sessionId'])

        if a['session'] and a['new']:
            from soxspipe.commonutils import data_organiser
            do = data_organiser(
                log=log,
                rootDir="."
            )
            sessionId = do.session_create(sessionId=a['sessionId'])

    except Exception as e:
        log.error(f'{e}\n{clCommand}', exc_info=True)

    # CALL FUNCTIONS/OBJECTS

    if "dbConn" in locals() and dbConn:
        dbConn.commit()
        dbConn.close()
    ## FINISH LOGGING ##
    endTime = times.get_now_sql_datetime()
    runningTime = times.calculate_time_difference(startTime, endTime)
    sys.argv[0] = os.path.basename(sys.argv[0])
    log.print(f'\nRecipe Command: {(" ").join(sys.argv)}')
    log.print(f'Recipe Run Time: {runningTime}\n\n')

    if not a['prep'] and not a['session']:
        print(f"{'='*70}\n")

    return


if __name__ == '__main__':

    main()
