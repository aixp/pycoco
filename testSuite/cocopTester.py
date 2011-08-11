import os
import os.path
import fnmatch
from glob import glob
import difflib
import sys
import traceback
import shutil


TARGET = ''
NEEDS  = [ ]

def expandGlob( aPathPattern ):
   '''Given a pathname pattern, return a list of all the paths on
   the local filesystem that match the pattern.'''
   return glob( os.path.normpath( aPathPattern ) )

def expandGlobList( paths ):
   '''Given a list of pathname patterns, return a list of all the
   paths on the local filesystem that match the patterns.

   paths may be:
      pathname as string
      pathname pattern as string
      pathname list as a string of ; separated patterns - not implemented
      pathname list who elements may be pathname or pathname pattern.
   returns:
      A list of all the paths on the local filesystem that match the
      patterns.
   '''
   if isinstance( paths, str ):
      return expandGlob( paths )
   elif isinstance( paths, (list,tuple) ):
      result = [ ]
      for pattern in paths:
         result += expandGlob( pattern )
      return result
   else:
      raise Exception( 'invalid argument type' )

def splitStringList( aString ):
   '''Given a string representing a list of glob, return a python
   list of glob.
   '''
   def strip( val ):
      return val.strip( )

   lst = aString.split( ';' )
   lst = map( strip, lst )

   return lst

def splitLists( *lists ):
   '''Given a list of things that may be a mix of globs or globlists,
   return a single python list of globs.

   items passsed may be:
      pathname or glob as string
      a list as a string containing pathname or glob all separated by ;
      a python list of pathname, glob or a list as a string of pathname or glob separated by ;
   '''
   result = [ ]

   for lst in lists:
      if isinstance( lst, str ):
         result += splitStringList( lst )
      elif isinstance( lst, (list,tuple) ):
         for elt in lst:
            result += splitStringList( elt )

   return result

def renameFile( filename, filename2 ):
   return os.renames( os.path.normpath(filename), os.path.normpath(filename2) )

def makeDirs( *dirNames ):
   dirNames = splitLists( *dirNames )
   for dirName in dirNames:
      dirName = os.path.normpath(dirName)
      if not os.path.exists( dirName ):
         os.makedirs( dirName )
      elif not os.path.isdir( dirName ):
         Exception( "Can't MakeDir.  Name already exists as a file. (%s)" % dirName )

def moveFilesTo( destDir, *paths ):
   '''Move the files named by paths to dirname.  Overwrite existing files.'''
   paths = splitLists( *paths )

   MakeDir( destDir )

   for name in expandGlobList( paths ):
      base = os.path.basename( name )
      dest = os.path.join( os.path.normpath(destDir), base )
      os.renames( name, dest )

def copyFilesTo( destDir, *paths ):
   '''Copy the files named by paths to dirname.  Overwrite existing files.'''
   if not os.path.exists( destDir ):
      makeDirs( destDir )

   paths = splitLists( *paths )
   for filename in expandGlobList( paths ):
      if os.path.isdir( filename ):
         shutil.copytree( filename, destDir )
      else:
         shutil.copy2( filename, destDir )

def deleteFiles( *paths ):
   paths = splitLists( *paths )
   for name in expandGlobList( paths ):
      if os.path.exists( name ):
         if os.path.isdir( name ):
            shutil.rmtree( name )
         else:
            os.remove( name )

def changeDir( destDir ):
   os.chdir( os.path.normpath(destDir) )

def compareFiles( fn1, fn2 ):
   f1 = file( os.path.normpath(fn1), 'r' ).read( ).splitlines( )
   f2 = file( os.path.normpath(fn2), 'r' ).read( ).splitlines( )

   return list(difflib.context_diff( f1, f2 ))

def dos2unix( filename ):
   if isinstance( filename, str ):
      fName = [ filename ]
   else:
      fName = filename

   import sys

   for fname in fName:
      infile = open( fname, "rb" )
      instr = infile.read()
      infile.close()
      outstr = instr.replace( "\r\n", "\n" ).replace( "\r", "\n" )

      if len(outstr) == len(instr):
         continue

      outfile = open( fname, "wb" )
      outfile.write( outstr )
      outfile.close()

def unix2dos( filename ):
   if isinstance( filename, str ):
      fName = [ filename ]
   else:
      fName = filename

   import sys

   for fname in fName:
      infile = open( fname, "rb" )
      instr = infile.read()
      infile.close()
      outstr = instr.replace( "\n", "\r\n" )

      if len(outstr) == len(instr):
         continue

      outfile = open( fname, "wb" )
      outfile.write( outstr )
      outfile.close()

def touch( filename ):
   pass

def shell( *strings ):
   command = ' '.join( strings )
   os.system( command )


class CocoTester( object ):
   def __init__( self, compiler, targetLanguageExt, testSuite ):
      self._compiler    = compiler
      self._fnTgtExt    = targetLanguageExt
      self._suite       = testSuite

   def compileBases( self, atgFilename,isErrorBase=False ):
      '''Python replacement for compile.bat.'''
      print 'Compiling bases for test: %s' % atgFilename

      if not atgFilename.lower().endswith( '.atg' ):
         baseName = atgFilename
         atgFilename += '.atg'
      else:
         baseName = os.path.splitext( os.path.basename( atgFilename ) )[0]

      if not os.path.exists( atgFilename ):
         raise 'ATG file not found %s' % atgFilename

      shell( '%s %s > %s_Output.txt' % (self._compiler, atgFilename, baseName) )
      deleteFiles( '%s_Trace.txt' % baseName, '%s_Parser.py' % baseName, '%s_Scanner.py' % baseName )
      renameFile( 'trace.txt',  '%s_Trace.txt'  % baseName )

      if not isErrorBase:
         renameFile( 'Parser.py',  '%s_Parser.py'  % baseName )
         renameFile( 'Scanner.py', '%s_Scanner.py' % baseName )

   def compileAllBases( self ):
      '''Python replacement for compileall.bat.'''
      for name,testType in self._suite:
         self.compileBases( name,testType )

      print 'Done.'

   def check( self, name, isErrorTest=False ):
      print 'Running test: %s' % name

      shell( '%s %s.atg >output.txt' % (self._compiler, name) )
      if compareFiles( 'trace.txt', '%s_Trace.txt' % name ):
         print 'trace files differ for %s' % name
         return False
      if compareFiles( 'output.txt', '%s_Output.txt' % name ):
         print 'output files differ for %s' % name
         return False

      if not isErrorTest:
         if compareFiles( 'Parser.py', '%s_Parser.py' % name ):
            print 'output files differ for %s' % name
            return False
         if compareFiles( 'Scanner.py', '%s_Scanner.py' % name ):
            print 'output files differ for %s' % name
            return False

      deleteFiles( '*.py.old', 'Parser.py', 'Scanner.py', 'output.txt', 'trace.txt' )

      return True

   def checkall( self ):
      numFailures = 0

      for name,isErrorTest in self._suite:
         passed = self.check( name, isErrorTest )
         if not passed:
            numFailures += 1

      print '%d tests failed.' % numFailures
      print 'Done.'

suite = [
      ( 'TestAlts',           False ),
      ( 'TestOpts',           False ),
      ( 'TestOpts1',          False ),
      ( 'TestIters',          False ),
      ( 'TestEps',            False ),
      ( 'TestAny',            False ),
      ( 'TestAny1',           False ),
      ( 'TestSync',           False ),
      ( 'TestSem',            False ),
      ( 'TestWeak',           False ),
      ( 'TestChars',          False ),
      ( 'TestTokens',         False ),
      ( 'TestTokens1',        True  ),
      ( 'TestComments',       False ),
      ( 'TestDel',            False ),
      ( 'TestTerminalizable', True  ),
      ( 'TestComplete',       True  ),
      ( 'TestReached',        True  ),
      ( 'TestCircular',       True  ),
      ( 'TestLL1',            False ),
      ( 'TestResOK',          False ),
      ( 'TestResIllegal',     True  ),
      ( 'TestCasing',         False )
      ]

tester = CocoTester( 'python %s' % (os.path.join('..', 'Coco.py')), 'py', suite )
tester.checkall( )
