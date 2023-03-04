import ast

INDENT = "\t"
scannerEnumName = "ScannerEnum"
baseParserClassName = "Parser"
baseScannerClassName = "Scanner"
generatedScannerClassName = "My" + baseScannerClassName
generatedParserClassName = "My" + baseParserClassName
runtimeBasePackage = "CoCoRuntime"
runtimeScannerModule = "scanner"
runtimeParserModule = "parser"
errorMessagesCollectionMemberName = "errorMessages"
mainProductionNameMemberName = "__main_production_name__"
eofSymbolMemberName = "__EOF_sym__"
eofSymbolEnumMemberName = "eofSym"
invalidSymbolEnumMemberName = "noSym"
enumTypeMemberName = "ENUM"
literalsTablePreparerFuncName = "prepareLiteralsTable"
scannerDocPostfix = "This is a scanner."
parserDocPostfix = "This is a parser."


defaultParserSystemImports = (
	ast.Import(names=[ast.alias(name="typing", asname=None)]),
	ast.ImportFrom(module="functools", names=[ast.alias(name="wraps", asname=None)], level=0),
)
