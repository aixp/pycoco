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

from .utils import classifyImportsInNode


class Preamble:
	__slots__ = ("doc", "imports", "licenseHeaderText", "restOfPreamble")

	def __init__(self, preambleAST: typing.Optional[typing.List[ast.AST]] = None) -> None:
		self.doc = None
		self.licenseHeaderText = None
		self.imports = defaultdict(list)
		self.restOfPreamble = []

		if preambleAST:
			for el in preambleAST:
				if isinstance(el, (ast.Import, ast.ImportFrom)):
					for section, importAST in classifyImportsInNode(el):
						self.imports[section].append(importAST)
				elif isinstance(el, ast.Assign):
					for n in el.targets:
						if isinstance(n, ast.Name):
							if n.id == "__copyright__":
								self.licenseHeaderText = ast.literal_eval(el.value)
				elif isinstance(el, ast.Expr) and isinstance(el.value, ast.Str) and self.doc is None:
					self.doc = el.value.value
				else:
					self.restOfPreamble.append(el)
