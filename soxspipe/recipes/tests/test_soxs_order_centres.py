from __future__ import print_function
from builtins import str
import os
import unittest
import shutil
import unittest
import yaml
from soxspipe.utKit import utKit
from fundamentals import tools
from os.path import expanduser
home = expanduser("~")

packageDirectory = utKit("").get_project_root()
settingsFile = packageDirectory + "/test_settings_xsh.yaml"
# settingsFile = home + "/.config/soxspipe/soxspipe.yaml"
su = tools(
    arguments={"settingsFile": settingsFile},
    docString=__doc__,
    logLevel="WARNING",
    options_first=False,
    projectName=None,
    defaultSettingsFile=False
)
arguments, settings, log, dbConn = su.setup()

packageDirectory = utKit("").get_project_root()
settingsFile2 = packageDirectory + "/test_settings_soxs_sim.yaml"
# settingsFile = home + "/.config/soxspipe/soxspipe.yaml"
su = tools(
    arguments={"settingsFile": settingsFile2},
    docString=__doc__,
    logLevel="DEBUG",
    options_first=False,
    projectName=None,
    defaultSettingsFile=False
)
arguments2, settings2, log2, dbConn2 = su.setup()

# SETUP AND TEARDOWN FIXTURE FUNCTIONS FOR THE ENTIRE MODULE
moduleDirectory = os.path.dirname(__file__)
utKit = utKit(moduleDirectory)
log, dbConn, pathToInputDir, pathToOutputDir = utKit.setupModule()
utKit.tearDownModule()

try:
    shutil.rmtree(pathToOutputDir)
except:
    pass
# COPY INPUT TO OUTPUT DIR
shutil.copytree(pathToInputDir, pathToOutputDir)

# Recursively create missing directories
if not os.path.exists(pathToOutputDir):
    os.makedirs(pathToOutputDir)

# xt-setup-unit-testing-files-and-folders


class test_soxs_order_centres(unittest.TestCase):

    import pytest

    # @pytest.mark.full
    # def test_soxs_order_centres_real_nir_function(self):
    #     sofPath = "~/xshooter-pipeline-data/unittest_data/soxs/ORDER_CENTRE/sof/SOXS_NIR_ORDER_CENTRE.sof"
    #     # sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-orderpos/nir"

    #     from soxspipe.recipes import soxs_order_centres
    #     this = soxs_order_centres(
    #         log=log2,
    #         settings=settings2,
    #         inputFrames=sofPath,
    #         overwrite=True
    #     )
    #     this.produce_product()

    # def test_soxs_order_centres_soxs_sim_nir_function(self):
    #     sofPath = "~/xshooter-pipeline-data/unittest_data/soxs-sim/ORDER_CENTRE/sof/SOXSIM_NIR_ORDER_CENTRE.sof"
    #     # sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-orderpos/nir"
    #     from soxspipe.recipes import soxs_order_centres
    #     this = soxs_order_centres(
    #         log=log2,
    #         settings=settings2,
    #         inputFrames=sofPath,
    #         overwrite=True
    #     )
    #     this.produce_product()

    def test_xsh_order_centres_nir_function(self):
        sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-order-centres/sof/20170818_NIR_ORDER_CENTRE.sof"
        # sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-orderpos/nir"
        from soxspipe.recipes import soxs_order_centres
        this = soxs_order_centres(
            log=log,
            settings=settings,
            inputFrames=sofPath,
            overwrite=True
        )
        this.produce_product()

    def test_xsh_order_centres_uvb_function(self):

        sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-order-centres/sof/20170818_UVB_ORDER_CENTRE_DLAMP_1x1_fast.sof"
        from soxspipe.recipes import soxs_order_centres
        this = soxs_order_centres(
            log=log,
            settings=settings,
            inputFrames=sofPath,
            overwrite=True
        )
        this.produce_product()

        sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-order-centres/sof/20170818_UVB_ORDER_CENTRE_QLAMP_1x1_fast.sof"
        from soxspipe.recipes import soxs_order_centres
        this = soxs_order_centres(
            log=log,
            settings=settings,
            inputFrames=sofPath,
            overwrite=True
        )
        this.produce_product()

    def test_xsh_order_centres_vis_function(self):
        sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-order-centres/sof/20170818_VIS_ORDER_CENTRE_1x1_fast.sof"
        from soxspipe.recipes import soxs_order_centres
        this = soxs_order_centres(
            log=log,
            settings=settings,
            inputFrames=sofPath,
            overwrite=True
        )
        this.produce_product()

    @pytest.mark.full
    def test_soxs_order_centres_function_exception(self):

        from soxspipe.recipes import soxs_order_centres
        try:
            sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-orderpos/sof/order_centre_uvb.sof"
            from soxspipe.recipes import soxs_order_centres
            this = soxs_order_centres(
                log=log,
                settings=settings,
                inputFrames=sofPath,
                overwrite=True
            )
            assert False
        except Exception as e:
            assert True
            print(str(e))

        # x-print-testpage-for-pessto-marshall-web-object

    # x-class-to-test-named-worker-function
