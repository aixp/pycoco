import plumbum.cli

class ApplicationWithArgsParsing(plumbum.cli.Application):
   @classmethod
   def parseArgs(cls, args):
      s=cls("")
      validators, restOfArgs=s._validate_args(*s._parse_args(args))
      for validator, args in validators:
         validator(s, *args)
      return s

class CocoArgs(ApplicationWithArgsParsing):
   traceAutomaton=plumbum.cli.Flag(
      ('a', 'A', "traceAutomaton"),
      help='Include automaton tracing in the trace file.',
      default=False
   )
   generateDriver=plumbum.cli.Flag(
      ('c', 'C', "generateDriver"),
      help='Generate a main compiler source file.',
      default=False
   )
   firstAndFollow=plumbum.cli.Flag(
      ('f', 'F', "firstAndFollow"),
      default=False,
      help='Include first & follow sets in the trace file.'
   )
   syntaxGraph=plumbum.cli.Flag(
      ('g', 'G', "syntaxGraph"),
      default=False,
      help='Include syntax graph in the trace file.'
   )
   traceComputations=plumbum.cli.Flag(
      ('i', 'I', "traceComputations"),
      default=False,
      help='Include a trace of the computations for first sets in the trace file.'
   )
   listAnyAndSync=plumbum.cli.Flag(
      ('j', 'J', "listAnyAndSync"),
      default=False,
      help='Inclue a listing of the ANY and SYNC sets in the trace file.'
   )
   mergeErrors=plumbum.cli.Flag(
      ('m', 'M', "mergeErrors"),
      default=False,
      help='Merge error messages in the source listing.'
   )
   tokenNames=plumbum.cli.Flag(
      ('n', 'N', "tokenNames"),
      default=False,
      help='Generate token names in the source listing.'
   ) 
   statistics=plumbum.cli.Flag(
      ('-p', '-P', "statistics"),
      default=False,
      help='Include a listing of statistics in the trace file.'
   )
   frameFileDir=plumbum.cli.SwitchAttr(
      ('-r', '-R', "frameFileDir"),
      plumbum.cli.ExistingDirectory,
      default=False,
      help='Use scanner.frame and parser.frame in this directory.'
   )
   symbolTable=plumbum.cli.Flag(
      ('-s', '-S', "symbolTable"),
      default=False,
      help='Include the symbol table listing in the trace file.'
   )
   testOnly=plumbum.cli.Flag(
      ('-t', '-T', "testOnly"),
      default=False,
      help='Test the grammar only, don\'t generate any files.'
   )
   crossReferences=plumbum.cli.Flag(
      ('-x', '-X', "xref"),
      default=False,
      help='Include a cross reference listing in the trace file.'
   )
   
   def main(self, *args, **kwargs):
      return self

parseArgs=CocoArgs.parseArgs