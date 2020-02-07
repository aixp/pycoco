from pathlib import Path

from setuptools.config import read_configuration

curDir = Path(__file__).absolute().parent
setupCfgPath = curDir / ".." / "setup.cfg"
if setupCfgPath.is_file():
	MetaData = read_configuration(setupCfgPath)["metadata"]
else:
	try:
		from importlib import metadata

		MetaData = metadata.metadata("CocoPy")
	except ImportError:
		from pkg_resources import DistributionNotFound, get_distribution

		try:
			d = get_distribution("CocoPy")
		except DistributionNotFound:
			d = get_distribution("Coco")
		MetaData = d.__dict__


def getVersionInfo():
	# pylint:disable=import-outside-toplevel
	try:
		import ujson as json
	except ImportError:
		import json

	return json.loads((curDir / "changelog.json").read_text(encoding="utf-8"))
