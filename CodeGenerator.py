import os
import os.path

class CodeGenerator( object ):
   CR          = '\r'
   LF          = '\n'
   TAB         = '\t'
   EOF         =   -1
   ls          = "\n"
   indent_unit = '   '

   sourceDir   = None
   frameDir    = None

   def __init__( self ):
      self._frameFile      = None
      self._outputFile     = None

   def openFiles( self, frameFileName, sourceFileName, outputFileName, backup=False ):
      if isinstance(frameFileName, str):
         frameFileName = [ frameFileName ]

      self._frameFile = None
      for frameName in frameFileName:
         fr = os.path.join( CodeGenerator.sourceDir, frameName )
         if not os.path.exists( fr ):
            if CodeGenerator.frameDir is not None:
               fr = os.path.join( CodeGenerator.frameDir, frameName )
         try:
            self._frameFile = file( fr, 'r' )
            break
         except IOError:
            pass

      if self._frameFile is None:
         raise RuntimeError( '-- Compiler Error: Cannot open ' + frameFileName[0] )

      try:
         fn = os.path.join( CodeGenerator.sourceDir, outputFileName )
         fn = str(fn)
         if backup and os.path.exists( fn ):
            if os.path.exists( fn + '.old' ):
               os.remove( fn + '.old' )
            os.rename( fn, fn + '.old' )
         self._outputFile = file( fn, 'w' )
      except:
         raise RuntimeError( '-- Compiler Error: Cannot create ' + outputFileName[0] + '.py' )

   def close( self ):
      self._frameFile.close( )
      self._outputFile.close( )

   def CopyFramePart( self, stop ):
      assert isinstance( stop, str )
      last = 0
      startCh = stop[0]
      endOfStopString = len(stop) - 1
      ch = self.frameRead( )

      while ch != CodeGenerator.EOF:
         if ch == startCh:
            i = 0
            if i == endOfStopString:
               return       # stop[0..i] found
            ch = self.frameRead( )
            i += 1
            while ch == stop[i]:
               if i == endOfStopString:
                  return       # stop[0..i] found
               ch = self.frameRead( )
               i += 1
            # stop[0..i-1] found; continue with last read character
            self._outputFile.write( stop[0:i] )
         elif ch == CodeGenerator.LF:
            if last != CodeGenerator.CR:
               self._outputFile.write( '\n' )
            last = ch
            ch = self.frameRead( )
         elif ch == CodeGenerator.CR:
            self._outputFile.write( '\n' )
            last = ch
            ch = self.frameRead()
         else:
            self._outputFile.write( str(ch) )
            last = ch
            ch = self.frameRead( )
      raise RuntimeError( ' -- Compiler Error: incomplete or corrupt parser frame file' )

   def CopySourcePart( self, pos, indent, forceOutput=False ):
      if pos is None:
         if forceOutput:
            self.Indent( indent )
            self._outputFile.write( 'pass' )
         return

      code = pos.getSubstring( )
      col = pos.col - 1

      lines = code.splitlines( True )
      pos = 0
      if (lines is None) or (len(lines) == 0):
         if forceOutput:
            self.Indent( indent )
            self._outputFile.write( 'pass' )
         return

      while lines[0][pos] in ( ' ', '\t' ):
         col += 1
      newLineList = [ lines[0] ]
      lines.pop(0)
      if col < 0:
         col = 0
      for line in lines:
         newLineList.append( line[ col : ] )

      for line in newLineList:
         self.Indent( indent )
         self._outputFile.write( line )

      if indent > 0:
         self._outputFile.write( '\n' )

      return

   def frameRead( self ):
      try:
         return self._frameFile.read( 1 )
      except IOError:
         #raise RuntimeError('-- Compiler Error: error reading Parser.frame')
         return ParserGen.EOF

   def Indent( self, n ):
      assert isinstance( n, int )
      self._outputFile.write( CodeGenerator.indent_unit * n )

   def Ch(ch):
      if isinstance(self, ch, int):
         ch = str( ch )
      if ch < ' ' or ch >= str(127) or ch == '\'' or ch == '\\':
         return ch
      else:
         return "ord('" + ch + "')"

   def ReportCh(self, ch):
      if isinstance(ch, (str,unicode)):
         ch = ord(ch)
      if (ch < ord(' ') or ch >= 127 or ch == ord('\'') or ch == ord('\\')):
         return str(ch)
      else:
         return ''.join( [ "'", chr(ch), "'" ] )

   def ChCond(self, ch, relOpStr='=='):
      if isinstance(ch, (str,unicode)):
         ch = ord(ch)

      if (ch < ord(' ') or ch >= 127 or ch == ord('\'') or ch == ord('\\')):
         return ''.join( [ 'ord(self.ch) ', relOpStr, " ", str(ch) ] )
      else:
         return ''.join( [ 'self.ch ', relOpStr, " '", chr(ch), "'" ] )

   def write( self, aString ):
      self._outputFile.write( aString )
