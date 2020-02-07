import difflib
import fnmatch
import os
import os.path
import shutil
import subprocess
import sys
import traceback
import unittest
from glob import glob

from .util import *


def expandGlob(aPathPattern):
	"""Given a pathname pattern, return a list of all the paths on
	the local filesystem that match the pattern."""
	return glob(os.path.normpath(aPathPattern))


def expandGlobList(paths):
	"""Given a list of pathname patterns, return a list of all the
	paths on the local filesystem that match the patterns.

	paths may be:
		pathname as string
		pathname pattern as string
		pathname list as a string of ; separated patterns - not implemented
		pathname list who elements may be pathname or pathname pattern.
	returns:
		A list of all the paths on the local filesystem that match the
		patterns.
	"""
	if isinstance(paths, str):
		return expandGlob(paths)
	elif isinstance(paths, (list, tuple)):
		result = []
		for pattern in paths:
			result += expandGlob(pattern)
		return result
	else:
		raise Exception("invalid argument type")


def splitStringList(aString):
	"""Given a string representing a list of glob, return a python
	list of glob.
	"""

	def strip(val):
		return val.strip()

	lst = aString.split(";")
	lst = list(map(strip, lst))

	return lst


def splitLists(*lists):
	"""Given a list of things that may be a mix of globs or globlists,
	return a single python list of globs.

	items passsed may be:
		pathname or glob as string
		a list as a string containing pathname or glob all separated by ;
		a python list of pathname, glob or a list as a string of pathname or glob separated by ;
	"""
	result = []

	for lst in lists:
		if isinstance(lst, str):
			result += splitStringList(lst)
		elif isinstance(lst, (list, tuple)):
			for elt in lst:
				result += splitStringList(elt)

	return result


def dos2unix(filename):
	if isinstance(filename, str):
		fName = [filename]
	else:
		fName = filename

	import sys

	for fname in fName:
		with open(fname, "rb") as infile:
			instr = infile.read()

		outstr = instr.replace("\r\n", "\n").replace("\r", "\n")

		if len(outstr) == len(instr):
			continue

		with open(fname, "wb") as outfile:
			outfile.write(outstr)


def unix2dos(filename):
	if isinstance(filename, str):
		fName = [filename]
	else:
		fName = filename

	import sys

	for fname in fName:
		with open(fname, "rb") as infile:
			instr = infile.read()
		outstr = instr.replace("\n", "\r\n")

		if len(outstr) == len(instr):
			continue

		with open(fname, "wb") as outfile:
			outfile.write(outstr)
