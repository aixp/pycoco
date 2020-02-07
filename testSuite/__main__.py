import io
import os
import platform
import sys
import traceback
from pathlib import Path
import unittest
import difflib

from .util import *

testSuiteBaseDir = Path(__file__).absolute().parent
baseDir = testSuiteBaseDir.parent
sys.path.append(str(baseDir))

from Coco.controller import Controller
from Coco.utils import astIntoText

testsDir = testSuiteBaseDir / "tests"
tmpDir = testSuiteBaseDir / "tmp"


def combineSuites(testSuites):
	s=unittest.TestSuite()
	for testSuite in testSuites:
		s.addTests(testSuite._tests)
	return s


class TestBase(unittest.TestCase):
	maxDiff = None

	def assertMultiLineEqual2(self, expected, actual):
		if expected != actual:
			res = "\n".join(difflib.unified_diff(expected.splitlines(), actual.splitlines(), "expected", "actual"))
			self.fail(self._formatMessage(res, res))


	def _testBase(self, dirName: str, errorExpected: bool):
		controller = Controller()
		controller.table.ddt.traceComputations = True
		controller.table.ddt.tokenNames = True

		src = (dirName / "Test.atg").read_text(encoding="utf-8")
		controller.parse(src)
		res = controller.pipeline()

		with self.subTest("scanner"):
			assert res.scanner is not None
			actual = astIntoText(res.scanner)
			etalon = (dirName / "Scanner.py").read_text()
			self.assertMultiLineEqual2(actual, etalon)

		with self.subTest("parser"):
			assert res.parser is not None
			actual = astIntoText(res.parser)
			etalon = (dirName / "Parser.py").read_text()
			self.assertMultiLineEqual2(actual, etalon)

		"""
		with self.subTest("trace"):
			etalon = (dirName / "Trace.txt").read_text()
			actual = cls.res
			self.assertMultiLineEqual2(f1, etalon)
		"""

		"""
		if not errorExpected:
			with self.subTest("run"):
				etalon = (dirName / "Output.txt").read_text(encoding="utf-8")
				self.assertMultiLineEqual2(output, etalon)
		"""


class CocoTester(unittest.TestProgram):
	def __init__(self, testsSpec, defaultTest=None, argv=None, testRunner=None, testLoader=unittest.loader.defaultTestLoader, exit=True, verbosity=1, failfast=None, catchbreak=None, buffer=None, warnings=None, *args, **kwargs):
		runTestsBackup=self.runTests
		self._testsSpec=testsSpec
		super().__init__(object(), defaultTest, argv, testRunner, testLoader, exit, verbosity, failfast, catchbreak, buffer, warnings, *args, **kwargs)

	def createTests(self):
		self.test = combineSuites(map(self.testLoader.loadTestsFromTestCase, self.generateTests()))
		if self.testNames:
			self.testNames=set(self.testNames)
			self.test._tests=type(self.test._tests)(filter(lambda e: e[1] in self.testNames, self.test._tests.items()))

	def genTestMethod(self, name, isErrorTest):
		dirName = testsDir / name
		isErrorTest

		def func(self):
			return self._testBase(dirName, isErrorTest)

		func.__name__ = "test_" + name
		return func

	def generateTests(self):
		class TestMeta(type):
			def __new__(cls, className, parents, attrs, *args, **kwargs):
				attrs = type(attrs)(attrs)

				for name, isErrorTest in self._testsSpec:
					testFunc = self.genTestMethod(name, isErrorTest)
					attrs[testFunc.__name__] = testFunc

				res = super().__new__(cls, className, parents, attrs, *args, **kwargs)
				return res

		class Test(TestBase, metaclass=TestMeta):
			pass

		yield Test


suite = [
	("TestAlts", False),
	("TestOpts", False),
	("TestOpts1", False),
	("TestIters", False),
	("TestEps", False),
	("TestAny", False),
	("TestAny1", False),
	("TestSync", False),
	("TestSem", False),
	("TestWeak", False),
	("TestChars", False),
	("TestTokens", False),
	("TestTokens1", True),
	("TestComments", False),
	("TestDel", False),
	("TestTerminalizable", True),
	("TestComplete", True),
	("TestReached", True),
	("TestCircular", True),
	("TestLL1", False),
	("TestResOK", False),
	("TestResIllegal", True),
	("TestCasing", False)
]

tester = CocoTester(suite)
