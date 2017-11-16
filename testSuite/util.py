import os
import os.path
import fnmatch
from glob import glob
import difflib
import sys
import traceback
import shutil
from .util import *
import unittest
import subprocess

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
   lst = list(map( strip, lst ))

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
   with open( os.path.normpath(fn1), 'rt', encoding="utf-8") as f:
      f1 = f.read( ).splitlines( )
   with open( os.path.normpath(fn2), 'rt', encoding="utf-8") as f:
      f2 = f.read( ).splitlines( )

   return list(difflib.context_diff( f1, f2 ))

def assertFilesEqual(test, fn1, fn2 ):
   with open( os.path.normpath(fn1), 'rt', encoding="utf-8") as f:
      f1 = f.read( )
   with open( os.path.normpath(fn2), 'rt', encoding="utf-8") as f:
      f2 = f.read( )

   return test.assertMultiLineEqual( f1, f2 )

def dos2unix( filename ):
   if isinstance( filename, str ):
      fName = [ filename ]
   else:
      fName = filename

   import sys

   for fname in fName:
      with open( fname, "rb" ) as infile:
         instr = infile.read()
      
      outstr = instr.replace( "\r\n", "\n" ).replace( "\r", "\n" )

      if len(outstr) == len(instr):
         continue

      with open( fname, "wb" ) as outfile:
         outfile.write( outstr )

def unix2dos( filename ):
   if isinstance( filename, str ):
      fName = [ filename ]
   else:
      fName = filename

   import sys

   for fname in fName:
      with open( fname, "rb" ) as infile:
         instr = infile.read()
      outstr = instr.replace( "\n", "\r\n" )

      if len(outstr) == len(instr):
         continue

      with open( fname, "wb" ) as outfile:
         outfile.write( outstr )

def touch( filename ):
   pass