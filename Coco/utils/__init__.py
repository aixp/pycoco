__license__ = "Unlicense"
__copyright__ = r"""
This is free and unencumbered software released into the public domain.

Anyone is free to copy, modify, publish, use, compile, sell, or distribute this software, either in source code form or as a compiled binary, for any purpose, commercial or non-commercial, and by any means.

In jurisdictions that recognize copyright laws, the author or authors of this software dedicate any and all copyright interest in the software to the public domain. We make this dedication for the benefit of the public at large and to the detriment of our heirs and successors. We intend this dedication to be an overt act of relinquishment in perpetuity of all present and future rights to this software under copyright law.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

For more information, please refer to <https://unlicense.org/>
"""

import ast
import typing
from collections import defaultdict
from collections.abc import MutableMapping
from warnings import warn

import astor

try:
	import isort

	isort_cfg = isort.api.Config()

	def classifyImportModuleName(moduleName: str) -> str:
		return isort.api.place_module(moduleName, isort_cfg)

except ImportError:

	def classifyImportModuleName(moduleName: str) -> str:
		return "UNCLASSIFIED"


def classifyImportsInNode(importAST: typing.Union[ast.ImportFrom, ast.Import]) -> typing.Iterator[typing.Tuple[str, typing.Union[ast.Import, ast.ImportFrom]]]:
	if isinstance(importAST, ast.ImportFrom):
		if importAST.level > 0 or importAST.module is None:
			yield ("LOCALFOLDER", importAST)
		else:
			yield (classifyImportModuleName(importAST.module), importAST)
	elif isinstance(importAST, ast.Import):
		imports = defaultdict(list)
		for alias in importAST.names:
			imports[classifyImportModuleName(alias.name)].append(alias)
		for k, v in imports.items():
			yield (k, ast.Import(names=v))


class DefaultDictRestIter(MutableMapping):
	__slots__ = ("dict", "visited")

	def __init__(self, dic: defaultdict) -> None:
		self.visited = set()
		self.dict = dic

	def __getitem__(self, k):
		self.visited |= {k}
		return self.dict[k]

	def __setitem__(self, k, v):
		self.visited -= {k}
		self.dict[k] = v

	def __delitem__(self, k):
		self.visited -= {k}
		del self.dict[k]

	def __iter__(self):
		return self.keys()

	def __len__(self):
		return len(self.dict) - len(self.visited)

	def items(self):
		for k, v in self.dict.items():
			if k not in self.visited:
				yield (k, v)

	def keys(self):
		for k, v in self.dict.items():
			if k not in self.visited:
				yield k

	def values(self):
		for k, v in self.items():
			yield v


def _testAstorSupportForTypeComment() -> bool:
	"""test if astor supports type comments"""
	return "c" in astor.to_source(ast.Assign(targets=[ast.Name("a")], value=ast.Name("b"), type_comment="c"))


OptAnnAssignT = typing.Union[ast.Assign, ast.AnnAssign]

if _testAstorSupportForTypeComment():

	def ourAnnAssign(target: ast.AST, value: ast.AST, annotation: ast.AST, useDedicatedSyntax: bool = False) -> OptAnnAssignT:
		if useDedicatedSyntax:
			return ast.AnnAssign(
				target=target,
				annotation=annotation,
				value=value,
				simple=1,
			)
		else:
			typeString = astor.to_source(ast, indent_with="\t", pretty_source="".join)
			return ast.Assign(targets=[target], value=value, type_comment=typeString)

else:

	def ourAnnAssign(target: ast.AST, value: ast.AST, annotation: ast.AST, useDedicatedSyntax: bool = False) -> OptAnnAssignT:
		if useDedicatedSyntax:
			return ast.AnnAssign(
				target=target,
				annotation=annotation,
				value=value,
				simple=1,
			)
		return ast.Assign(targets=[target], value=value, type_comment=None)


def getArrayTypeCode(maxInt: int, unsigned: bool = True) -> str:
	"""Returns unsigned type code for `array.array`"""
	bs = maxInt.bit_length() - unsigned  # 1 bit for sign
	vals = (
		(8, "B"),
		(16, "H"),
		(32, "L"),
		(64, "Q"),
	)
	for s, c in vals:
		if bs < s:
			return c.lower() if not unsigned else c
	raise ValueError("Integers are too large")


def astIntoText(codeAST: ast.AST, blacken: bool = True, indent_with="\t") -> str:
	"""Transforms python AST into source text.
	`blacken` means to apply `black`
	"""
	# pylint:disable=import-outside-toplevel

	if blacken:
		try:
			import black
		except ImportError:
			blacken = False

		if blacken:
			res = astor.to_source(codeAST, indent_with=indent_with, pretty_source="".join)
			try:
				res = black.format_str(res, mode=black.Mode(line_length=100500))
				return res
			except BaseException as ex:
				warn("`black` has failed: " + repr(ex))

	res = astor.to_source(codeAST, indent_with=indent_with)
	return res


PrimitiveT = typing.Union[str, int, float, type(None)]
LiteralT = typing.Union[PrimitiveT, typing.Dict[PrimitiveT, "LiteralT"], typing.Tuple["LiteralT", ...], typing.Set[PrimitiveT], typing.FrozenSet[PrimitiveT]]


def literalToAST(lit: LiteralT) -> ast.AST:
	"""Very simple, very dumb and very inefficient transformer of python objects that can be parsed by `literal_eval" into python AST. For input other than of LiteralT the behavior is undefined"""
	v = ast.parse(repr(lit), mode="eval")
	if isinstance(v, ast.Expression):
		v = v.body
	return v


class InvalidIndentationException(Exception):
	__slots__ = ()


class IndentSizer:
	"""Computes sizes of indent characters in sizes of a single character (usually only a tab)."""

	__slots__ = ("table",)

	def __init__(self, tabSize: int = 4) -> None:
		"""`tabSize` - count of spaces in a tab"""
		self.table = {
			" ": lambda col: 1,
			"\t": lambda col: tabSize - col % tabSize,
		}

	def __call__(self, c: str, col: int, default: typing.Callable[[int], int]) -> int:
		"""
		`c` - current character
		`col` - current column
		`default` - a function returning char size for the chars not in table or doing stuff like raising exception. It highly depends on a task and thus is mandatory.
		returns increment for the column.
		"""
		return self.table.get(c, default)(col)


def invalidIndentationExceptionRaiser(col: int):
	raise InvalidIndentationException("Invalid indentation")


def deindent(s: str, indentSizer: IndentSizer, col: int) -> str:
	"""Deindent stripping first level of indentation.

	To be useful we need the following informaion:
		1. offset to beginning of the string of semantic action
		2. tab width (can take from .editorconfig)
	then we will be able to strip the right count of leading whitespaces correctly
	"""

	ls = s.splitlines()
	out = []

	leadin = None

	for l in ls:
		if l:
			countToStrip = None
			if leadin is None:
				leadin = col
				for countToStrip, c in enumerate(l):
					delta = indentSizer(c, leadin, lambda col: None)
					if delta is not None:
						leadin += delta
					else:
						break

			else:
				column = 0
				for countToStrip, c in enumerate(l):
					if c == "#":
						countToStrip = 0
						break
					if column == leadin:
						break
					if column > leadin:
						raise InvalidIndentationException("Invalid indentation: overflow")
					column += indentSizer(c, column, invalidIndentationExceptionRaiser)

			l = l[countToStrip:]
		out.append(l)
	return "\n".join(out)
