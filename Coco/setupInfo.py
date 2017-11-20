from setuptools.config import read_configuration
import os

curDir=os.path.dirname(__file__)
setupCfgPath=os.path.join(curDir, "..", "setup.cfg")
if os.path.isfile(setupCfgPath):
   MetaData = read_configuration(setupCfgPath)["metadata"]
else:
   from pkg_resources import get_distribution
   MetaData = get_distribution('Coco').__dict__

VersionInfo = {
   '1.1.0rc': {
      'changes':  [ "Coco/R now passes all tests of the official Coco/R test suite" ],
      'bugfixes': [ ],
      'contirubtions': [ ]
   },

   '1.0.10b2':{
      'changes':  [ "Updated builder and renamed it to pimaker" ],
      'bugfixes': [ "Many code generator bug fixes" ],
      'contributions': [ "Wayne Wiitanen has contributed a version of the EXPR example that works with CocoPy." ]
   },

   '1.0.9b2': {
      'changes':  [ "Simplified the Errors class and error handling.",
                    "Completed a first version of my builder application." ],
      'bugfixes': [ "Repaired a bug in SemErr() didn't work properly." ]
   },

   '1.0.7b1': {
      'changes':  [ ],
      'bugfixes': [ "Repaired LINUX bug found in v1.0.6b1" ]
   },

   '1.0.6b1': {
      'changes':  [ "Completed a beta version of builder.py",
                    "Updated README.txt to describe builder.py",
                    "Removed HowToBootstrap.txt from Documents" ],
      'bugfixes': [ "Coco.atg does not bootstrap on LINUX." ]
   }
}
