import os
import os.path
import fnmatch
from glob import glob
import difflib
import sys
import traceback
import shutil


LAUNCH_DIR = os.getcwd( )
ROOT_DIR = os.path.dirname( __file__ )
os.chdir( ROOT_DIR )

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

class Rule( object ):
   def __init__( self, target, dependancies, action, description=None ):
      global TARGET, NEEDS

      self._target       = target
      self._description  = description
      self._dependancies = { }           # dependency to rule
      self._action       = None

      TARGET = self._target
      NEEDS  = [ ]
      for dependancy in dependancies:
         NEEDS.append( self.expandMacros(dependancy) )

      for dependancy in NEEDS:
         self._dependancies[ dependancy ] = None

      self._action = self.expandMacros( action )

   def getDependancies( self ):
      return self._dependancies.keys( )

   def getDescription( self ):
      return self._description

   def defineDependencyRule( self, dependencyName, Rule ):
      self._dependancies[ dependencyName ] = Rule

   def build( self ):
      target = os.path.normpath( self._target )

      # Handle subrules
      if len( self._dependancies ) == 0:
         needToRebuildTarget = True
      else:
         needToRebuildTarget = not os.path.exists( target )

      for dependency, subrule in self._dependancies.iteritems( ):
         dependency = os.path.normpath( dependency )
         if not os.path.exists( dependency ):
            if subrule:
               subrule.build( )
               print '-----------------------------------'
            else:
               raise Exception( 'No rule to build target %s' % dependency )

         if os.path.exists( target ):
            targetTime     = os.stat( target )[ 8 ]
            dependencyTime = os.stat( dependency )[ 8 ]

            if dependencyTime > targetTime:
               needToRebuildTarget = True

      if needToRebuildTarget:
         print 'Building: %s' % target
         execActionCode( self._action )

   def expandMacros( self, aString ):
      macroStart = aString.find( '${' )

      while macroStart != -1:
         macroEnd   = aString.find( '}', macroStart+2 )
         macroSeq   = aString[ macroStart+2 : macroEnd ].split( ',' )

         if '.' in macroSeq[0]:
            var,op = macroSeq[0].split('.')
         else:
            var = macroSeq[0]
            op  = None

         value = globals( )[ var ]

         if isinstance( value, (str,unicode) ):
            if op == 'dir':
               value = os.path.dirname( value )
            elif op == 'name':
               value = os.path.basename( value )
            elif op == 'base':
               value = os.path.splitext( os.path.basename( value ) )[0]
            elif op == 'ext':
               value = os.path.splitext( os.path.basename( value ) )[1]

            if len(macroSeq) > 1:
               mark = macroSeq[1].find( '=' )
               if mark == -1:
                  raise Exception( 'Error in macro' )
               old = macroSeq[1][ : mark  ]
               new = macroSeq[1][ mark+1 : ]
               value = value.replace( old, new )

            aString = aString[ :macroStart ] + value + aString[ macroEnd+1: ]
            macroStart = aString.find( '${' )
         elif isinstance( value, (list,tuple) ):
            pass

      return aString


class Builder( object ):
   def __init__( self, projectName='' ):
      self._rules           = { }
      self._topLevelTargets = [ ]
      self._leaves          = [ ]
      self._projectName     = projectName
      self._menuOrder       = [ ]

   @staticmethod
   def set( name, value ):
      set( name, value )

   @staticmethod
   def unset( name ):
      unset( name )

   def addTarget( self, targets, *args ):
      if isinstance( targets, str ):
         targets = [ targets ]

      numArgs = len( args )

      if numArgs == 3:
         # We have a description
         description  = args[0]
         dependencies = args[1]
         actions      = args[2]
      elif numArgs == 2:
         # No description
         description  = None
         dependencies = args[0]
         actions      = args[1]
      else:
         raise TypeError( 'addTarget() takes 3 or 4 arguments (%d given)' % numArgs )

      for target in targets:
         depend = [ ]

         self._rules[ target ] = Rule( target, dependencies, actions, description )
         self._menuOrder.append( target )

   def finalize( self ):
      # Assemble the Rules into a Tree
      for target, rule in self._rules.iteritems( ):
         for dependencyName in rule.getDependancies( ):
            if dependencyName in self._rules:
               rule.defineDependencyRule( dependencyName, self._rules[ dependencyName ] )
            else:
               if dependencyName not in self._leaves:
                  self._leaves.append( dependencyName )

      # Determine the top-level targets
      targets = self._rules.keys( )

      for name in self._rules.keys( ):
         for rule in self._rules.values( ):
            if name in rule.getDependancies( ):
               if name in targets:
                  targets.remove( name )

      targets.sort()
      self._topLevelTargets = [ ]
      for targetName in self._menuOrder:
         if targetName in targets:
            self._topLevelTargets.append( ( targetName, self._rules[ targetName ].getDescription() ) )

   def targets( self ):
      return self._rules.keys( )

   def build( self, target ):
      print '********** Target: %s' % target

      try:
         theRule = self._rules[ target ]
         theRule.build( )
         print '********** Build completed'
      except:
         type,value,trace = sys.exc_info( )
         print 'BUILD FAILED!!!'
         print traceback.print_exc( )

   def topTargets( self ):
      return self._topLevelTargets

   def allTargets( self ):
      return self._rules.keys( )

   def initializationCode( self, code ):
      execActionCode( code )

   def goInteractive( self ):
      print
      print 'Entering Interactive Builder'

      response = ''
      self._buildMenu( )
      while response != 'exit':
         target = raw_input( '\nbuild> ' )

         if target == 'showall':
            targetList = self.allTargets( )
            targetList.sort( )
            print ', '.join( targetList )
            continue
         elif target == 'exit':
            break
         elif target in self.allTargets( ):
            print
            print
            self.build( target )
         else:
            print '   !!! Unknown Target !!!'

         self._buildMenu( )

   def _buildMenu( self ):
      print
      print 'Targets:'
      for targetName, targetDescription in self._topLevelTargets:
         print '   %-15s  %s' % ( targetName, targetDescription )

      print
      print '   %-15s  %s' % ( 'showall', 'Show the full list of targets.' )
      print '   %-15s  %s' % ( 'exit', 'Exit the interactive builder.' )


bld = Builder( )

def execActionCode( code ):
   exec code in globals( )


class Path( object ):
   def __init__( self, path ):
      self._drive     = ''
      self._dir       = [ ]
      self._fileName  = ''
      self._extension = ''

      self._drive, self._dir, self._fileName, self._extension = FilePath.parseSystemDependantPath( path )

   @staticmethod
   def parseSystemDependantPath( name ):
      drive, fullPath     = os.path.splitdrive( os.path.normpath(path) )
      dir, fName          = os.path.split( fullPath )
      fileName, extension = os.path.splitext( fName )
      dir                 = dir.split( os.sep )

      return ( drive, dir, fName, extension )

   def asSystemDependantPath( self ):
      return os.path.join( [ self._drive, self._dir, self._fileName, self._extension ] )

   def move( self, newName, overwrite=False ):
      pass

   def copy( self, newName, overwrite=False ):
      pass

   def remove( self ):
      pass

   def exists( self ):
      pass

   def isDirectory( self ):
      pass

   def isPattern( self ):
      pass

   def realize( self ):
      pass

   def stats( self ):
      pass

   def traverse( self ):
      pass

#class FileSystem( object ):
   #def __init__( self, root=None ):
      #self._root = root

      #if root is None:
         #self._root = ''

   #def iterDirTree( self, patterns='*', recurse=True, yieldFolders=False, root=None ):
      ## Expand patterns from semicolon-separated string to list
      #patterns = patterns.split( ';' )

      #if root is None:
         #theRoot = self._root
      #else:
         #theRoot = root

      #for path, subdirs, files in os.walk( theRoot ):
         #if yieldFolders:
            #files.extend( subdirs )

         #files.sort( )
         #for name in files:
            #for pattern in patterns:
               #if fnmatch.fnmatch( name, pattern ):
                  #yield os.path.join( path, name )
                  #break

            #if not recurse:
               #break

   #def remove( self, root=None ):
      #if root is None:
         #theRoot = self._root
      #else:
         #theRoot = root

      #for root, dirs, files in os.walk( theRoot, topdown=False ):
         #for name in files:
            #os.remove( os.path.join( root, name ) )
         #for name in dirs:
            #os.rmdir( os.path.join( root, name ) )

   #def removeFiles( self, patterns='*', recurse=False, root=None ):
      #fileList = list( self.iterDirTree( patterns, recurse, yieldFolders=False, root=root ) ).reverse( )
      #for name in fileList:
         #os.remove( name )

   #def makeDir( self, path ):
      #listPath = path.split( os.sep )
      #accumPath = ''
      #for name in listPath:
         #accumPath = os.path.join( accumPath, name )
         #if not os.path.exists( accumPath ):
            #os.mkdir( accumPath )

   #def removeDir( self, path ):
      #os.rmdir( path )

   #def currentDir( self ):
      #return os.getcwd( )

   #def changeDir( self, path ):
      #os.chdir( path )

   #def exists( self, path ):
      #return os.path.exists( path )

   #def isDir( self, path ):
      #return not os.path.isfile( path )

   #def rename( self, oldName, newName ):
      #os.rename( oldName, newName )

   #def copy( self, pattern, dest ):
      #pass
