#!/usr/bin/env python3
import os
from setuptools import setup
from setuptools.config import read_configuration

curDir = os.path.dirname(__file__)
setupCfgPath=os.path.join(curDir, "setup.cfg")
cfg = read_configuration(setupCfgPath)

#print(cfg)
cfg["options"].update(cfg["metadata"])
cfg=cfg["options"]
setup(use_scm_version = True, **cfg)





