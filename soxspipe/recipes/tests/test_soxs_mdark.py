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
settingsFile = packageDirectory + "/test_settings.yaml"
# settingsFile = home + "/.config/soxspipe/soxspipe.yaml"
su = tools(
    arguments={"settingsFile": settingsFile},
    docString=__doc__,
    logLevel="DEBUG",
    options_first=False,
    projectName=None,
    defaultSettingsFile=False
)
arguments, settings, log, dbConn = su.setup()

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


class test_soxs_mdark(unittest.TestCase):

    def test_soxs_mdark_nir_function(self):
        sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-mdark/sofs/nir_6s_darks.sof"
        from soxspipe.recipes import soxs_mdark
        this = soxs_mdark(
            log=log,
            settings=settings,
            inputFrames=sofPath
        )
        productPath = this.produce_product()
        print(f"Here is the final product `{productPath}`")

        sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-mdark/sofs/nir_240s_darks.sof"
        from soxspipe.recipes import soxs_mdark
        this = soxs_mdark(
            log=log,
            settings=settings,
            inputFrames=sofPath
        )
        productPath = this.produce_product()
        print(f"Here is the final product `{productPath}`")

        sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-mdark/sofs/nir_125s_darks.sof"
        from soxspipe.recipes import soxs_mdark
        this = soxs_mdark(
            log=log,
            settings=settings,
            inputFrames=sofPath
        )
        productPath = this.produce_product()
        print(f"Here is the final product `{productPath}`")

    def test_soxs_mdark_uvb_function(self):

        sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-mdark/sofs/uvb_1x1_dark_3600s.sof"
        from soxspipe.recipes import soxs_mdark
        this = soxs_mdark(
            log=log,
            settings=settings,
            inputFrames=sofPath
        )
        productPath = this.produce_product()
        print(f"Here is the final product `{productPath}`")

        sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-mdark/sofs/uvb_2x2_dark_3600s.sof"
        from soxspipe.recipes import soxs_mdark
        this = soxs_mdark(
            log=log,
            settings=settings,
            inputFrames=sofPath
        )
        productPath = this.produce_product()
        print(f"Here is the final product `{productPath}`")

    def test_soxs_mdark_vis_function(self):
        sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-mdark/sofs/vis_1x1_dark_3600s.sof"
        from soxspipe.recipes import soxs_mdark
        this = soxs_mdark(
            log=log,
            settings=settings,
            inputFrames=sofPath
        )
        productPath = this.produce_product()
        print(f"Here is the final product `{productPath}`")

        sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-mdark/sofs/vis_2x2_dark_3600s.sof"
        from soxspipe.recipes import soxs_mdark
        this = soxs_mdark(
            log=log,
            settings=settings,
            inputFrames=sofPath
        )
        productPath = this.produce_product()
        print(f"Here is the final product `{productPath}`")

    # def test_soxs_mdark_function(self):

    #     # utKit.refresh_database() # reset database to database found in
    #     # soxspipe/test/input
    #     from soxspipe.recipes import soxs_mdark
    #     this = soxs_mdark(
    #         log=log,
    #         settings=settings
    #     )
    #     this.get()

    def test_soxs_mdark_function_exception(self):

        from soxspipe.recipes import soxs_mdark
        try:
            sofPath = "~/xshooter-pipeline-data/unittest_data/xsh/xshooter-mdark/sofs/nir_mixed_exptime_darks.sof"
            from soxspipe.recipes import soxs_mdark
            this = soxs_mdark(
                log=log,
                settings=settings,
                inputFrames=sofPath
            )
            assert False
        except Exception as e:
            assert True
            print(str(e))

        # x-print-testpage-for-pessto-marshall-web-object

    # x-class-to-test-named-worker-function
