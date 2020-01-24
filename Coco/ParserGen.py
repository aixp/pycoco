#-------------------------------------------------------------------------
#__class__.py -- The parser generation routines.
#Compiler Generator Coco/R,
#Copyright (c) 1990, 2004 Hanspeter Moessenboeck, University of Linz
#extended by M. Loeberbauer & A. Woess, Univ. of Linz
#ported from Java to Python by Ronald Longo
#
#This program is free software; you can redistribute it and/or modify it
#under the terms of the GNU General Public License as published by the
#Free Software Foundation; either version 2, or (at your option) any
#later version.
#
#This program is distributed in the hope that it will be useful, but
#WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
#or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General Public License
#for more details.
#
#You should have received a copy of the GNU General Public License along
#with this program; if not, write to the Free Software Foundation, Inc.,
#59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#
#As an exception, it is allowed to write an extension of Coco/R that is
#used as a plugin in non-free software.
#
#If not otherwise stated, any source code generated by Coco/R (other than
#Coco/R itself) does not fall under the GNU General Public License.
#-------------------------------------------------------------------------*/
import copy
import os
from pathlib import Path
import io

from .Errors import Errors
from .Trace import Trace
from .Core import Node, DFA, Symbol, Tab
from .CodeGenerator import CodeGenerator

class MyLoopBreak( Exception ):
   pass

class ParserGen( object ):
   maxTerm =    3    # sets of size < maxTerm are enumerated
   ls      = "\n"

   tErr    =    0    # error codes
   altErr  =    1
   syncErr =    2

   usingPos =  None  # usingPos: Position   "using" definitions from the attributed grammar

   errorNr   = 0      # highest parser error number
   curSy     = None   # symbol whose production is currently generated
   err       = None   # generated parser error messages
   srcName   = ''     # name of attributed grammar file
   srcDir    = ''     # directory of attributed grammar file
   symSet    = [ ]

   codeGen   = CodeGenerator( )

   @staticmethod
   def Overlaps( s1, s2 ):
      assert isinstance( s1, set )
      assert isinstance( s2, set )
      ln = len(s1)
      for i in range( 0, ln ):
         if (i in s1) and (i in s2):
            return True
      return False

   @staticmethod
   def GenErrorMsg( errTyp, sym ):
      assert isinstance( errTyp, int )
      assert isinstance( sym, Symbol )
      __class__.errorNr += 1
      __class__.err.write( __class__.ls + '      ' + str(__class__.errorNr) + ' : "' )
      if errTyp == __class__.tErr:
         if sym.name[0] == '"':
            __class__.err.write( str(DFA.Escape( sym.name )) + ' expected' )
         else:
            __class__.err.write( str(sym.name) + ' expected' )
      elif errTyp == __class__.altErr:
         __class__.err.write( 'invalid ' + str(sym.name) )
      elif errTyp == __class__.syncErr:
         __class__.err.write( 'this symbol not expected in ' + str(sym.name) )
      __class__.err.write('",' )

   @staticmethod
   def NewCondSet( s ):
      assert isinstance( s, set )
      for i in range( 1, len(__class__.symSet) ):
        # skip symSet[0] (reserved for union of SYNC sets)
        if s == __class__.symSet[i]: #s.equals( __class__.symSet[i] ):
           return i
      __class__.symSet.append( copy.copy(s) )
      return len(__class__.symSet) - 1

   @staticmethod
   def GenCond( s, p ):
      assert isinstance( s, set  )
      assert isinstance( p, Node )
      if p.typ == Node.rslv:
         __class__.codeGen.CopySourcePart( p.pos, 0 )
      else:
         n = len(s)
         if n == 0:
            __class__.codeGen.write( 'False' ) # should never happen
         elif n <= __class__.maxTerm:
            for i in range( 0, len(Symbol.terminals) ):
               sym = Symbol.terminals[i]
               assert isinstance( sym, Symbol )
               if sym.n in s:
                  __class__.codeGen.write( 'self.la.kind == ')
                  __class__.PrintTermName( sym )
                  n -= 1
                  if n > 0:
                     __class__.codeGen.write( ' or ' )
         else:
            __class__.codeGen.write( 'self.StartOf(' + str(__class__.NewCondSet( s )) + ')' )

   @staticmethod
   def GenCode( p, indent, isChecked ):
      #assert isinstance( p, Node )
      assert isinstance( indent, int )
      assert isinstance( isChecked, set )
      while p is not None:
         if p.typ == Node.nt:       # Non-Terminals
            __class__.codeGen.Indent( indent )
            if p.retVar is not None:
               __class__.codeGen.write( p.retVar + ' = ' )
            __class__.codeGen.write( 'self.' + p.sym.name + '(' )
            __class__.codeGen.CopySourcePart( p.pos, 0 )
            __class__.codeGen.write( ')\n' )
         elif p.typ == Node.t:      # Terminals
            __class__.codeGen.Indent( indent )
            if p.sym.n in isChecked:
               __class__.codeGen.write( 'self.Get( )\n' )
            else:
               __class__.codeGen.write( 'self.Expect(' )
               __class__.PrintTermName( p.sym )
               __class__.codeGen.write( ')\n' )
         elif p.typ == Node.wt:
            __class__.codeGen.Indent( indent )
            s1 = Tab.Expected( p.next, __class__.curSy )
            s1 |= Tab.allSyncSets
            __class__.codeGen.write( 'self.ExpectWeak(' )
            __class__.PrintTermName( p.sym )
            __class__.codeGen.write( ', ' + str(__class__.NewCondSet( s1 )) + ')\n' )
         elif p.typ == Node.any:
            __class__.codeGen.Indent( indent )
            __class__.codeGen.write( 'self.Get()\n' )
         elif p.typ == Node.eps:
            __class__.codeGen.Indent( indent )
            __class__.codeGen.write( 'pass\n' )
         elif p.typ == Node.rslv:
            #__class__.codeGen.Indent( indent )
            #__class__.codeGen.write( 'pass\n' )
            pass   # Nothing to do
         elif p.typ == Node.sem:
            __class__.codeGen.CopySourcePart( p.pos, indent )
         elif p.typ == Node.sync:
            __class__.codeGen.Indent( indent)
            __class__.GenErrorMsg( __class__.syncErr, __class__.curSy )
            s1 = copy.copy(p.set)
            __class__.codeGen.write( 'while not (' )
            __class__.GenCond( s1,p )
            __class__.codeGen.write( '):\n' )
            __class__.codeGen.Indent( indent+1 )
            __class__.codeGen.write( 'self.SynErr(' + str(__class__.errorNr) + ')\n' )
            __class__.codeGen.Indent( indent+1 )
            __class__.codeGen.write( 'self.Get()\n' )
         elif p.typ == Node.alt:
            s1 = Tab.First( p )
            p2 = p
            equal = (s1 == isChecked)
            while p2 is not None:
               s1 = Tab.Expected( p2.sub, __class__.curSy )
               __class__.codeGen.Indent( indent )
               if p2 == p:
                  __class__.codeGen.write( 'if ' )
                  __class__.GenCond( s1, p2.sub )
                  __class__.codeGen.write( ':\n' )
               elif p2.down is None and equal:
                  __class__.codeGen.write( 'else:\n' )
               else:
                  __class__.codeGen.write( 'elif ' )
                  __class__.GenCond( s1, p2.sub )
                  __class__.codeGen.write( ':\n' )
               s1 |= isChecked
               __class__.GenCode( p2.sub, indent+1, s1 )
               p2 = p2.down
            if not equal:
               __class__.codeGen.Indent( indent )
               __class__.GenErrorMsg( __class__.altErr, __class__.curSy )
               __class__.codeGen.write( 'else:\n' )
               __class__.codeGen.Indent( indent+1 )
               __class__.codeGen.write( 'self.SynErr(' + str(__class__.errorNr) + ')\n' )
         elif p.typ == Node.iter:
            __class__.codeGen.Indent( indent )
            p2 = p.sub
            __class__.codeGen.write( 'while ' )
            if p2.typ == Node.wt:
               s1 = Tab.Expected( p2.next, __class__.curSy )
               s2 = Tab.Expected( p.next, __class__.curSy )
               __class__.codeGen.write( 'self.WeakSeparator(' )
               __class__.PrintTermName( p2.sym )
               __class__.codeGen.write( ', ' + str(__class__.NewCondSet(s1)) + ', ' + str(__class__.NewCondSet(s2)) + ')' )
               s1 = set( )
               if p2.up or p2.next is None:
                  p2 = None
               else:
                  p2 = p2.next
            else:
               s1 = Tab.First( p2 )
               __class__.GenCond( s1, p2 )
            __class__.codeGen.write( ':\n' )
            __class__.GenCode( p2,indent+1, s1 )
            __class__.codeGen.write( '\n' )
         elif p.typ == Node.opt:
            s1 = Tab.First( p.sub )
            __class__.codeGen.Indent( indent )
            __class__.codeGen.write( 'if (' )
            __class__.GenCond( s1, p.sub )
            __class__.codeGen.write( '):\n' )
            __class__.GenCode( p.sub, indent+1, s1 )

         if p.typ != Node.eps and p.typ != Node.sem and p.typ != Node.sync:
            for val in range( 0, len(isChecked) ):
               isChecked.discard( val )

         if p.up:
            break

         p = p.next

   @staticmethod
   def GenTokens( withNames ):
      assert isinstance( withNames, bool )
      for sym in Symbol.terminals:
         if sym.name[0].isalpha( ):
            __class__.codeGen.write( '   _' + sym.name + ' = ' + str(sym.n) + '\n' )
      if withNames:
         __class__.codeGen.write( '   # terminals\n')
         for sym in Symbol.terminals:
            __class__.codeGen.write( '   ' + sym.symName + ' = ' + str(sym.n) + '\n' )
         __class__.codeGen.write( '   # pragmas\n' )
         for sym in Symbol.pragmas:
            __class__.codeGen.write( '   ' + sym.symName + ' = ' + str(sym.n) + '\n' )
         __class__.codeGen.write( '\n' )

   @staticmethod
   def GenPragmas( ):
      for sym in Symbol.pragmas:
         __class__.codeGen.write( '   _' + str(sym.name) + ' = ' + str(sym.n) + '\n' )

   @staticmethod
   def GenCodePragmas( ):
      for sym in Symbol.pragmas:
         __class__.codeGen.write( 'if self.la.kind == ' )
         __class__.PrintTermName( sym )
         __class__.codeGen.write( ':\n' )
         __class__.codeGen.CopySourcePart( sym.semPos, 4, True )

   @staticmethod
   def GenProductions( ):
      for sym in Symbol.nonterminals:
         __class__.curSy = sym

         # Generate the function header
         __class__.codeGen.write( '   def ' + sym.name + '( self' )
         if sym.attrPos is not None:
            __class__.codeGen.write( ', ' )
         __class__.codeGen.CopySourcePart( sym.attrPos, 0 )
         __class__.codeGen.write( ' ):\n' )

         # Generate the function body
         __class__.codeGen.CopySourcePart( sym.semPos, 2 )
         __class__.GenCode( sym.graph, 2, set( ) )

         # Generate the function close
         if sym.retVar is not None:
            __class__.codeGen.write( '      return ' + sym.retVar + '\n' )
         __class__.codeGen.write( '\n' )

   @staticmethod
   def InitSets( ):
      for i in range(0,len(__class__.symSet)):
         s = __class__.symSet[i]
         __class__.codeGen.write( '      [' )
         j = 0
         for sym in Symbol.terminals:
            if sym.n in s:
               __class__.codeGen.write( 'T,' )
            else:
               __class__.codeGen.write( 'x,' )
            j += 1
            if j%4 == 0:
               __class__.codeGen.write( ' ' )
         if i == (len(__class__.symSet) - 1):
            __class__.codeGen.write( 'x]\n' )
         else:
            __class__.codeGen.write( 'x],\n' )

   @staticmethod
   def Init( fn, dir: Path ):
      assert isinstance( fn, str )
      assert isinstance( dir, Path )
      __class__.srcName = fn
      __class__.srcDir  = dir
      __class__.errorNr = -1
      __class__.usingPos = None

   @staticmethod
   def WriteParser( withNames ):
      assert isinstance( withNames, bool )
      assert isinstance( Tab.allSyncSets, set )
      __class__.symSet.append( Tab.allSyncSets )

      __class__.codeGen.openFiles( 'Parser.frame', __class__.srcName,
            'Parser.py', True )

      if withNames:
         Tab.AssignNames( )

      __class__.err = io.StringIO( )
      for sym in Symbol.terminals:
         __class__.GenErrorMsg( __class__.tErr, sym )

      __class__.codeGen.CopyFramePart( '-->begin' )
      if __class__.usingPos != None:
         __class__.codeGen.write( '\n' )
         __class__.codeGen.CopySourcePart( __class__.usingPos, 0 )
      __class__.codeGen.CopyFramePart( '-->constants' )
      __class__.GenTokens( withNames )
      __class__.codeGen.write( '   maxT = ' + str(len(Symbol.terminals) - 1) + '\n')
      __class__.GenPragmas( )
      __class__.codeGen.CopyFramePart( '-->declarations' )
      __class__.codeGen.CopySourcePart( Tab.semDeclPos, 0 )
      __class__.codeGen.CopyFramePart( '-->pragmas' )
      __class__.GenCodePragmas( )
      __class__.codeGen.CopyFramePart( '-->productions' )
      __class__.GenProductions( )
      __class__.codeGen.CopyFramePart( '-->parseRoot' )
      __class__.codeGen.write( Tab.gramSy.name + '()\n' )
      __class__.codeGen.write( '      self.Expect(' )
      __class__.PrintTermName( Tab.eofSy )
      __class__.codeGen.write( ')\n' )
      __class__.codeGen.CopyFramePart( '-->initialization' )
      __class__.InitSets( )
      __class__.codeGen.CopyFramePart( '-->errors' )
      __class__.codeGen.write( str(__class__.err.getvalue( )) )
      __class__.codeGen.CopyFramePart( '$$$' )
      __class__.codeGen.close( )

   @staticmethod
   def WriteStatistics( ):
      Trace.WriteLine( )
      Trace.WriteLine( 'Statistics:' )
      Trace.WriteLine( '-----------' )
      Trace.WriteLine( )
      Trace.WriteLine( str(len( Symbol.terminals )) + ' terminals' )
      Trace.WriteLine( str(len( Symbol.terminals ) + len( Symbol.pragmas ) + len( Symbol.nonterminals )) + ' symbols' )
      Trace.WriteLine( str(len(Node.nodes)) + ' nodes' )
      Trace.WriteLine( str(len(__class__.symSet)) + ' sets' )
      Trace.WriteLine( )

   @staticmethod
   def PrintTermName( sym ):
      assert isinstance( sym, Symbol )
      assert isinstance( sym.symName, str ) or (sym.symName is None)
      if sym.symName is None:
         __class__.codeGen.write( str(sym.n) )
      else:
         __class__.codeGen.write( 'Scanner.' )
         __class__.codeGen.write( str(sym.symName) )
