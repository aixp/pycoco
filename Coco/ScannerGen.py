import ast
import typing

from CoCoRuntime.errors import Errors

from .actions import CharAct, State, TransitionCode
from .charUtils import charSetSize
from .CodeGenerator import ChCond, apxAST, bufAST, bufferEOFAST, decLevelAST, enumClassFieldTypeAnotationAST, falseAST, genArrayArrayCall, genClassStub, genScannerEnum, incLevelAST, inRangeTestGenAST, intAST, intCollectionAnnotationAST, levelAST, levelEq0Test, line0AST, lineStart0AST, noneAST, printTermName, scannerEnumNoSymAST, scannerEOLAST, selfArgAST, selfBufferAST, selfChAST, selfCheckLiteralCallAST, selfLineAST, selfLineStartAST, selfNameAST, selfNextChCallAST, selfOldEolsAST, selfPosAST, selfTAST, selfTKindAST, selfTValAssignBufAST, selfTValAST, stateAST, trueAST, valChAST
from .Core import Comment
from .defaults import literalsTablePreparerFuncName, runtimeBasePackage, runtimeScannerModule
from .DFA import DFA
from .Preamble import Preamble
from .symbols import Symbol, SymbolTokensKinds
from .Tab import Tab
from .utils import literalToAST, ourAnnAssign


class ScannerGen(DFA):
	"""Scanner gen"""

	__slots__ = ("dfa",)

	def __init__(self, dfa: DFA):
		self.dfa = dfa

	def PutRange(self, s: typing.Set[typing.Union[int, str]]) -> ast.BoolOp:
		assert isinstance(s, set)
		lo = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
		hi = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
		# fill lo and hi
		mx = charSetSize
		top = -1
		i = 0
		while i < mx:
			if i in s:
				top += 1
				lo[top] = i
				i += 1
				while i < mx and (i in s):
					i += 1
				hi[top] = i - 1
			else:
				i += 1

		# print ranges
		if top == 1 and lo[0] == 0 and hi[1] == mx - 1 and hi[0] + 2 == lo[1]:
			s1 = set()
			s1.add(hi[0] + 1)
			return ast.BoolOp(op=ast.And, values=[ast.UnaryOp(op=ast.Not(), operand=self.PutRange(s1)), ast.Compare(left=ast.Attribute(value=ast.Name("Scanner"), attr="ch"), ops=[ast.NotEq()], comparators=[ast.Attribute(value=ast.Attribute(value=ast.Name("Scanner"), attr="buffer"), attr="EOF")],),],)

		res = []

		for i in range(0, top + 1):
			if hi[i] == lo[i]:
				res.append(ChCond(lo[i]))
			elif lo[i] == 0:
				res.append(ChCond(hi[i], ast.LtE))
			else:
				res.append(inRangeTestGenAST(lo[i], hi[i]))
		if "ANYCHAR" in s:
			res.append(ast.Compare(
				left=ast.Call(
					func=ast.Name("ord"),
					args=[selfChAST],
					keywords=(),
				),
				ops=[ast.Gt()],
				comparators=[ast.Num(charSetSize)],
			))

		return ast.BoolOp(op=ast.Or(), values=res)

	@staticmethod
	def GenComBody2(com: Comment) -> None:
		assert isinstance(com, Comment)
		lastElIf = ifNode = ast.If(
			test=ChCond(com.stop[0]),
			body=[],
			orelse=[],
		)
		if len(com.stop) == 1:
			ifNode.body.extend([
				ast.AugAssign(target=levelAST, op=ast.Sub(), value=ast.Num(1)),
				ast.If(
					test=ast.Compare(
						left=levelAST, ops=[ast.Eq()], comparators=[ast.Num(0)]
					),
					body=[
						ast.Assign(
							targets=[selfOldEolsAST],
							value=ast.BinOp(
								left=selfLineAST,
								op=ast.Sub(),
								right=line0AST,
							),
							type_comment=None,
						),
						ast.Expr(
							value=selfNextChCallAST
						),
						ast.Return(value=trueAST),
					],
					orelse=[],
				),
				ast.Expr(
					value=selfNextChCallAST
				),
			])
		else:
			ifNode.body.extend([
				selfNextChCallAST,
				ast.If(
					test=ChCond(com.stop[1]),
					body=[
						decLevelAST,
						ast.If(
							test=ast.Compare(
								left=levelAST, ops=[ast.Eq()], comparators=[ast.Num(0)]
							),
							body=[
								ast.Assign(
									targets=[selfOldEolsAST],
									value=ast.BinOp(
										left=selfLineAST,
										op=ast.Sub(),
										right=line0AST,
									),
									type_comment=None,
								),
								ast.Expr(
									value=selfNextChCallAST
								),
								ast.Return(value=trueAST),
							],
							orelse=[],
						),
						ast.Expr(
							value=selfNextChCallAST
						),
					],
					orelse=[],
				),
			])

		if com.nested:
			trueBranch = [incLevelAST, selfNextChCallAST]

			nestedIf = ast.If(
				test=ChCond(com.start[0]),
				body=[],
				orelse=[],
			)

			if len(com.start) == 1:
				nestedIf.body.extend(trueBranch)
			else:
				nestedIf.body.extend([
					selfNextChCallAST,
					ast.If(
						test=ChCond(com.start[1]),
						body=trueBranch,
						orelse=[],
					)
				])

		lastElIf.orelse.append(ast.If( # el
			test=ast.Compare(
				left=selfChAST,
				ops=[ast.Eq()],
				comparators=[bufferEOFAST],
			),  # 3
			body=[ast.Return(value=falseAST)],
			orelse=[
				selfNextChCallAST
			],
		))

		return ast.While(test=trueAST, body=[ifNode], orelse=[])

	@staticmethod
	def GenComBody3(com: Comment) -> ast.While:
		assert isinstance(com, Comment)

		lastMainElifNode = ifNode = ast.If(
			test=ChCond(com.stop[0]),  # 4
			body=[],
			orelse=[],
		)
		if len(com.stop) == 1:
			ifNode.body.extend((
				decLevelAST,
				ast.If(
					test=levelEq0Test,
					body=[
						ast.Assign(
							targets=[ast.Attribute(value=selfNameAST, attr="oldEols")],
							value=ast.BinOp(
								left=selfLineAST,
								op=ast.Sub(),
								right=line0AST,
							),
							type_comment=None,
						),
						selfNextChCallAST,
						ast.Return(value=trueAST)
					],
					orelse=[],
				),
				selfNextChCallAST
			))

		else:
			ifNode.body.extend((
				selfNextChCallAST,
				ast.If(
					test=ChCond(com.stop[1]), # 5
					body=[
						decLevelAST,
						ast.If(
							test=levelEq0Test,  # 6
							body=[
								ast.Assign(
									targets=[selfOldEolsAST],
									value=ast.BinOp(
										left=selfLineAST,
										op=ast.Sub(),
										right=line0AST,
									),
									type_comment=None,
								),
								selfNextChCallAST,
								ast.Return(value=trueAST)
							],
							orelse=[],
						),
						selfNextChCallAST
					],
					orelse=[],
				),
			))

		if com.nested:
			elifNode1 = ast.If(
				test=ChCond(com.start[0]),  # 4
				body=[],
				orelse=[],
			)

			if len(com.start) == 1:
				elifNode1.body.extend((incLevelAST, selfNextChCallAST))  # 5
			else:
				elifNode1.body.extend((
					selfNextChCallAST,
					ast.If(
						test=ChCond(com.start[1]),  # 5
						body=[
							incLevelAST,
							selfNextChCallAST
						],
						orelse=[],
					)
				))  # 5
			lastMainElifNode.orelse.append(elifNode1)
			lastMainElifNode = elifNode1

		lastMainElifNode.orelse.append(ast.If(
			test=ast.Compare(
				left=selfChAST,
				ops=[ast.Eq()],
				comparators=[bufferEOFAST],
			),  # 4
			body=[
				ast.Return(value=falseAST)
			],
			orelse=[
				selfNextChCallAST
			],
		))

		return ast.While(test=trueAST, body=[ifNode], orelse=[])

	def GenComment(self, com: Comment, i: int) -> ast.FunctionDef:
		assert isinstance(com, Comment)
		assert isinstance(i, int)
		funcBody = [
			ast.Assign(
				targets=[levelAST],
				value=ast.Num(1),
				type_comment=None,
			),
			ast.Assign(
				targets=[line0AST],
				value=selfLineAST,
				type_comment=None,
			),
			ast.Assign(targets=[lineStart0AST], value=selfLineStartAST, type_comment=None),
			selfNextChCallAST
		]

		if len(com.start) == 1:
			funcBody.extend(self.GenComBody2(com))
		else:
			funcBody.extend((
				ast.If(
					test=ChCond(com.start[1]),  # 2
					body=[
						selfNextChCallAST,
						self.GenComBody3(com)
					],
					orelse=[
						ast.If(
							test=ast.Compare(
								left=selfChAST,
								ops=[ast.Eq()],
								comparators=[scannerEOLAST],
							),
							body=[
								ast.AugAssign(target=selfLineAST, op=ast.Sub(), value=ast.Num(1)),
								ast.Assign(targets=[selfLineStartAST], value=lineStart0AST, type_comment=None,),

							],
							orelse=[],
						),
						ast.Assign(
							targets=[selfPosAST],
								value=ast.BinOp(
									left=selfPosAST,
									op=ast.Sub(),
									right=ast.Num(2),
								),
								type_comment=None,
						),
						ast.Expr(ast.Call(
							func=ast.Attribute(
								value=selfBufferAST, attr="setPos"
							),
							args=[
								ast.BinOp(
									left=selfPosAST,
									op=ast.Add(),
									right=ast.Num(1),
								)
							],
							keywords=(),
						)),
						selfNextChCallAST,

					],
				),
				ast.Return(value=falseAST)
			))
		return ast.FunctionDef(
			name="Comment" + str(i),
			args=ast.arguments(
				posonlyargs=(),
				args=[selfArgAST],
				vararg=None,
				kwonlyargs=(),
				kw_defaults=[],
				kwarg=None,
				defaults=[],
			),
			body=funcBody,
			decorator_list=(),
			returns=ast.Name("bool"),
			type_comment=None,
		)

	@staticmethod
	def SymName(table: Tab, sym: Symbol) -> str:
		assert isinstance(sym, Symbol)
		if sym.name[0].isalpha():
			# real name value is stored in table.literals
			for me_key, me_value in table.literals.items():
				if me_value == sym:
					return me_key
		return sym.name

	def GenLiterals(self, table: Tab, enumNameAST: ast.Name, useAnnotatedAssignments: bool = False) -> typing.Iterator[typing.Union[ast.AnnAssign, ast.FunctionDef]]:
		literalsTableNameAST = ast.Name("literalsTable")
		innerLiteralsTableAST = ast.Attribute(value=ast.Attribute(value=selfNameAST, attr="__class__"), attr="literalsTable")

		keys = []
		values = []
		for sym in table.terminals:
			if sym.tokenKind == SymbolTokensKinds.litToken:
				name = self.SymName(table, sym)  # String
				if self.dfa.ignoreCase:
					name = name.lower()

				keys.append(name)
				values.append(printTermName(sym, enumNameAST))

		yield ourAnnAssign(
			target=literalsTableNameAST,
			annotation=ast.Subscript(
				value=ast.Attribute(value=ast.Name("typing"), attr="Mapping"),
				slice=ast.Index(value=ast.Tuple(elts=[ast.Name("str"), enumNameAST])),
			),
			value=ast.Call(func=ast.Name(literalsTablePreparerFuncName), args=[ast.Dict(keys=keys, values=values)], keywords=()),
			useDedicatedSyntax=useAnnotatedAssignments,
		)

		v = selfTValAST
		if self.dfa.ignoreCase:
			v = ast.Call(func=ast.Attribute(value=v, attr="lower"), args=(), keywords=())

		res = ast.FunctionDef(
			name="CheckLiteral",
			args=ast.arguments(
				posonlyargs=(),
				args=[selfArgAST],
				vararg=None,
				kwonlyargs=(),
				kw_defaults=[],
				kwarg=None,
				defaults=[],
			),
			body=[
				ast.Return(
					value=ast.Call(
						func=ast.Attribute(value=innerLiteralsTableAST, attr="get"),
						args=[v, selfTKindAST],
						keywords=(),
					)
				)
			],
			decorator_list=(),
			returns=enumNameAST,
			type_comment=None,
		)

		yield res

	@staticmethod
	def _constructStateTransitionReturnTupleAST(stateToReturn: typing.Union[ast.Constant, ast.Name], kindToReturn: typing.Union[ast.Attribute, ast.Call, ast.Constant], apxToReturn: ast.Name) -> ast.Return:
		return ast.Return(ast.Tuple(
			elts=[
				stateToReturn,  # new state or None if `done==True`
				kindToReturn,  # new kind
				apxToReturn,  # new apx
				bufAST,
			]
		))

	@staticmethod
	def _getKindToReturnInScan3(endOf: typing.Optional[Symbol], mainIfBody: typing.Optional[typing.List[ast.If]], enumToTakeFrom: typing.Optional[ast.Name] = None) -> typing.Union[ast.Attribute, ast.Call]:
		if endOf is None:
			kindToReturn = scannerEnumNoSymAST
		else:
			kindToReturn = printTermName(endOf, enumToTakeFrom)

			if endOf.tokenKind == SymbolTokensKinds.classLitToken:
				mainIfBody.extend([
					selfTValAssignBufAST,
					ast.Assign(targets=[selfTKindAST], value=kindToReturn, type_comment=None),
				])
				kindToReturn = selfCheckLiteralCallAST
		return kindToReturn

	def WriteState(self, state: State) -> ast.If:
		assert isinstance(state, State)
		endOf = state.endOf  # Symbol

		mainIf = ast.If(
			test=ast.Compare(
				left=stateAST, ops=[ast.Eq()], comparators=[ast.Num(state.nr)] # 3
			),
			body=[],
			orelse=[],
		)
		stateToReturn = stateAST
		kindToReturn = selfTKindAST
		apxToReturn = apxAST

		ctxEnd = state.ctx  # boolean
		action = state.firstAction
		while action is not None:
			yetAnotherIf = ast.If(
				test=ChCond(action.sym) if isinstance(action, CharAct) else self.PutRange(self.dfa.charClassStorage.Set(action.sym)), # 4
				body=[],
				orelse=[],
			)
			stateToReturn = stateAST
			kindToReturn = selfTKindAST
			apxToReturn = apxAST

			if action.tc == TransitionCode.contextTrans:
				apxToReturn = ast.BinOp(left=apxAST, op=ast.Add(), right=ast.Num(1))
				ctxEnd = False
			elif state.ctx:
				apxToReturn = ast.Num(0)
			yetAnotherIf.body.append(ast.AugAssign(
				target=bufAST,
				op=ast.Add(),
				value=ast.Call(
					func=ast.Name("str"),
					args=[selfChAST],
					keywords=(),
				),
			))  # 5
			yetAnotherIf.body.append(selfNextChCallAST)  # 5
			stateToReturn = ast.Num(action.target.state.nr)
			yetAnotherIf.body.append(self.__class__._constructStateTransitionReturnTupleAST(stateToReturn, kindToReturn, apxToReturn))

			mainIf.body.append(yetAnotherIf)
			action = action.next

		if ctxEnd:  # final context state: cut appendix
			mainIf.body.extend((
				ast.Assign(
					targets=[selfPosAST],
					value=ast.BinOp(
						left=ast.BinOp(
							left=selfPosAST,
							op=ast.Sub(),
							right=apxAST,
						),
						op=ast.Sub(),
						right=ast.Num(1),
					),
					type_comment=None,
				),
				ast.Assign(
					targets=[selfLineAST],
					value=ast.Attribute(
						value=selfTAST, attr="line"
					),
					type_comment=None,
				),
				ast.Expr(ast.Call(
					func=ast.Attribute(
						value=selfBufferAST, attr="setPos"
					),
					args=[
						ast.BinOp(
							left=selfPosAST,
							op=ast.Add(),
							right=ast.Num(1),
						)
					],
					keywords=(),
				)),
				selfNextChCallAST
			))  # 4

		stateToReturn = noneAST
		kindToReturn = self.__class__._getKindToReturnInScan3(endOf, mainIf.body)

		mainIf.body.append(self.__class__._constructStateTransitionReturnTupleAST(stateToReturn, kindToReturn, apxToReturn))
		return mainIf

	def FillStartTab(self, startTab: typing.List[int]) -> int:
		assert isinstance(startTab, list)
		action = self.dfa.firstState.firstAction

		maxTargetState = -1

		while action is not None:
			targetState = action.target.state.nr  # int
			maxTargetState = max(maxTargetState, targetState)
			if isinstance(action, CharAct):
				startTab[action.sym] = targetState
			else:
				s = self.dfa.charClassStorage.Set(action.sym)  # BitSet
				for i in range(0, charSetSize):
					if i in s:
						startTab[i] = targetState
			action = action.next

		return maxTargetState

	def genCasingFunc(self, name: str = "casing") -> ast.FunctionDef:
		body = []

		if self.dfa.ignoreCase:
			body.extend((
				ast.Assign(
					targets=[valChAST],
					value=selfChAST,
					type_comment=None,
				),
				ast.If(
					test=ast.Compare(
						left=selfChAST,
						ops=[ast.NotEq()],
						comparators=[bufferEOFAST],
					),  # 2
					body=[
						ast.Assign(
							targets=[selfChAST],
							value=ast.Call(
								func=ast.Attribute(
									value=selfChAST, attr="lower"
								),
								args=(),
								keywords=(),
							),
							type_comment=None,
						)
					],
					orelse=[],
				)
			))  # 2
		else:
			body.append(ast.Pass())

		return ast.FunctionDef(
			name=name,
			args=ast.arguments(
				posonlyargs=(),
				args=[selfArgAST],
				vararg=None,
				kwonlyargs=(),
				kw_defaults=[],
				kwarg=None,
				defaults=[],
			),
			body=body,
			decorator_list=(),
			returns=noneAST,
			type_comment=None,
		)

	def genScan1(self, name: str = "scan1") -> ast.FunctionDef:
		body = []
		if self.dfa.commentsListHead is not None:
			ors = []
			com = self.dfa.commentsListHead
			i = 0

			while com is not None:
				ors.append(
					ast.BoolOp(
						op=ast.And(),
						values=[
							ChCond(com.start[0]),
							ast.Call(
								func=ast.Attribute(value=selfNameAST, attr="Comment" + str(i)), args=(), keywords=()
							),
						],
					)
				)
				com = com.next
				i += 1

			body.append(ast.Return(value=ast.BoolOp(op=ast.Or(), values=ors)))
		else:
			body.append(ast.Pass())

		return ast.FunctionDef(
			name=name,
			args=ast.arguments(
				posonlyargs=(),
				args=[selfArgAST],
				vararg=None,
				kwonlyargs=(),
				kw_defaults=[],
				kwarg=None,
				defaults=[],
			),
			body=body,
			decorator_list=(),
			returns=ast.Name("bool"),
			type_comment=None,
		)

	@staticmethod
	def genScan2(name: str = "scan2") -> ast.FunctionDef:
		"""Returns a function. May be moved to the runtime, and I do it, so don't generate. IDK why is it generated, probably it was planned to plug here something"""
		return ast.FunctionDef(
			name=name,
			args=ast.arguments(
				posonlyargs=(),
				args=[
					selfArgAST,
					ast.arg(arg="buf", annotation=ast.Name("str"), type_comment=None)
				],
				vararg=None,
				kwonlyargs=(),
				kw_defaults=[],
				kwarg=None,
				defaults=[],
			),
			body=[
				ast.AugAssign(
					target=bufAST,
					op=ast.Add(),
					value=ast.Call(
						func=ast.Name("str"),
						args=[selfChAST],
						keywords=(),
					),
				),
				selfNextChCallAST,
				ast.Return(value=ast.Name("buf")),
			],
			decorator_list=(),
			returns=ast.Name("str"),
			type_comment=None,
		)

	def genScan3(self, enumNameAST: ast.AST, funcName: str = "scan3", optimizeUsingLUTs: bool = True) -> typing.Tuple[ast.FunctionDef, typing.Iterable[ast.AST], int]:
		finalStatesLUTBody = [ast.Attribute(value=enumNameAST, attr="noSym")]  # state 0 is special and is not passed through this, but for proper typing we set it

		#self.CopyFramePart("-->scan3")
		body = []

		maxFinalStateValue = 0

		populatingFinal = optimizeUsingLUTs
		for state in self.dfa.__class__._iterateStates(self.dfa.firstState.next):
			if populatingFinal:
				if state.isTrivialFinal:
					maxFinalStateValue = max(maxFinalStateValue, state.endOf.n)
					finalStatesLUTBody.append(self.__class__._getKindToReturnInScan3(state.endOf, None, enumNameAST))
				else:
					populatingFinal = False
					body.append(self.WriteState(state))
			else:
				body.append(self.WriteState(state))

		body.append(self.__class__._constructStateTransitionReturnTupleAST(stateAST, selfTKindAST, apxAST))  # do nothing
		return finalStatesLUTBody, ast.FunctionDef(
			name=funcName,
			args=ast.arguments(
				posonlyargs=(),
				args=[
					selfArgAST,
					ast.arg(arg="state", annotation=ast.Name("int"), type_comment=None),
					ast.arg(arg="apx", annotation=ast.Name("int"), type_comment=None),
					ast.arg(arg="buf", annotation=ast.Name("str"), type_comment=None),
				],
				vararg=None,
				kwonlyargs=(),
				kw_defaults=[],
				kwarg=None,
				defaults=[],
			),
			body=body,
			decorator_list=(),
			returns=ast.Subscript(
				value=ast.Attribute(value=ast.Name(id="typing"), attr="Tuple"),
				slice=ast.Index(
					value=ast.Tuple(
						elts=[
							ast.Subscript(
								value=ast.Attribute(value=ast.Name(id="typing"), attr="Optional"),
								slice=ast.Index(value=intAST),
							),
							enumNameAST,
							intAST,
							ast.Name(id="str"),
						]
					)
				),
			),
			type_comment=None,
		), maxFinalStateValue

	def genInitFunc(self, table: Tab) -> ast.FunctionDef:
		body = []

		if not body:
			body.append(ast.Pass())

		return ast.FunctionDef(
			name="initialization",
			args=ast.arguments(
				posonlyargs=(),
				args=[selfArgAST],
				vararg=None,
				kwonlyargs=(),
				kw_defaults=[],
				kwarg=None,
				defaults=[],
			),
			body=body,
			decorator_list=(),
			returns=noneAST,
			type_comment=None,
		)

	def genIgnores(self, table: Tab, useAnnotatedAssignments: bool, name: str = "ignores") -> ast.AST:
		elts = None
		if table.ignored is not None:
			elts = [ast.Num(i) for i in sorted(table.ignored)]
		else:
			# default
			elts = [ast.Num(ord(" "))]

		ignoresBody = ast.Call(
			func=ast.Name(id='frozenset'),
			args=[ast.Tuple(elts=elts)],
			keywords=[],
		)
		ignoresAssignment = ourAnnAssign(
			target=ast.Name(name),
			value=ignoresBody,
			annotation=intCollectionAnnotationAST,
			useDedicatedSyntax=useAnnotatedAssignments,
		)
		return ignoresAssignment

	def genCommentProcessingRoutines(self) -> typing.Iterator[ast.FunctionDef]:
		com = self.dfa.commentsListHead  # Comment
		i = 0
		while com is not None:
			yield self.GenComment(com, i)
			com = com.next
			i += 1

	def WriteScanner(self, table: Tab, withNames: bool, errors: Errors, preamble: typing.Optional[Preamble] = None, useAnnotatedAssignments: bool = False) -> ast.AST:
		assert isinstance(withNames, bool)

		if preamble is None:
			preamble = Preamble()

		if not preamble.licenseHeaderText:
			preamble.licenseHeaderText = __gpl_exception_generated__

		startTab = [0 for i in range(charSetSize)]
		if self.dfa.dirtyDFA:
			self.dfa.MakeDeterministic(errors)
		maxTargetState = self.FillStartTab(startTab)

		enumName = "ScannerEnum"
		baseClassName = "Scanner"
		generatedClassName = "MyScanner"

		baseClassNameAST = ast.Name(baseClassName)
		enumNameAST, enumAST = genScannerEnum(enumName, table, withNames=withNames)

		scannerClass = genClassStub(name=generatedClassName, baseClassNameAST=baseClassNameAST)

		scannerClass.body.extend((  # pylint:disable=no-member
			ourAnnAssign(
				target=ast.Name("ENUM"),
				value=ast.Name(enumName),
				annotation=enumClassFieldTypeAnotationAST(enumName),
				useDedicatedSyntax=useAnnotatedAssignments
			),
			ast.Assign(
				targets=[ast.Name("charSetSize")],
				value=ast.Num(charSetSize),
				type_comment=None,
			),
			ast.Assign(
				targets=[ast.Name("maxT")],
				value=ast.Num(len(table.terminals) - 1),
				type_comment=None,
			),
			ourAnnAssign(
				target=ast.Name("start"),
				value=genArrayArrayCall(ast.Tuple(literalToAST(startTab + [-1]).elts), maxTargetState, unsigned=False),
				annotation=intCollectionAnnotationAST,
				useDedicatedSyntax=useAnnotatedAssignments
			)
		))

		if self.dfa.ignoreCase:
			scannerClass.body.append(ast.Assign(  # pylint:disable=no-member
				targets=[valChAST],
				value=ast.Str(value=""),
				type_comment=None,
			))  # 1
			#scannerClass.body.append(INDENT + "# current input character (for token.val)")

		scannerClass.body.extend((  # pylint:disable=no-member
			self.genInitFunc(table),
			self.genIgnores(table, useAnnotatedAssignments),
			self.genCasingFunc(),
		))

		scannerClass.body.extend(self.genCommentProcessingRoutines())  # pylint:disable=no-member
		scannerClass.body.extend(self.GenLiterals(table, enumNameAST, useAnnotatedAssignments))  # pylint:disable=no-member
		scannerClass.body.extend((  # pylint:disable=no-member
			self.genScan1(),
			self.__class__.genScan2(),
		))

		finalStatesLUTName = "finalStates"

		finalStatesLUTBody, scan3AST, maxFinalStateValue = self.genScan3(enumNameAST)

		scannerClass.body.append(scan3AST)

		if len(finalStatesLUTBody) > 1:
			scannerClass.body.append(ourAnnAssign(
				target=ast.Name(finalStatesLUTName),
				value=genArrayArrayCall(ast.Tuple(finalStatesLUTBody), maxFinalStateValue, unsigned=True),
				annotation=intCollectionAnnotationAST,
				useDedicatedSyntax=useAnnotatedAssignments
			))

		scannerDocPostfix = "This is a scanner."

		return ast.Module(body=[
			ast.Expr(ast.Str(preamble.doc + "\n\n" + scannerDocPostfix if preamble.doc is not None else scannerDocPostfix)),
			ast.Assign(
				targets=[ast.Name("__copyright__")],
				value=ast.Str(preamble.licenseHeaderText),
				type_comment=None,
			),
			ast.Import(names=[ast.alias(name="typing", asname=None)]),
			ast.Import(names=[ast.alias(name="array", asname=None)]),
			ast.ImportFrom(module="enum", names=[ast.alias(name="IntEnum", asname=None)], level=0),
			ast.ImportFrom(module="functools", names=[ast.alias(name="wraps", asname=None)], level=0),
			ast.ImportFrom(
				module=runtimeBasePackage + "." + runtimeScannerModule,
				names=[
					ast.alias(name="Buffer", asname=None),
					ast.alias(name=baseClassName, asname=None),
					ast.alias(name=literalsTablePreparerFuncName, asname=None),
				],
				level=0,
			),
			enumAST,
			scannerClass
		])
