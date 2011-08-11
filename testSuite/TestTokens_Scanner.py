
import sys

class Token( object ):
   def __init__( self ):
      self.kind   = 0     # token kind
      self.pos    = 0     # token position in the source text (starting at 0)
      self.col    = 0     # token column (starting at 0)
      self.line   = 0     # token line (starting at 1)
      self.val    = u''   # token value
      self.next   = None  # AW 2003-03-07 Tokens are kept in linked list


class Position( object ):    # position of source code stretch (e.g. semantic action, resolver expressions)
   def __init__( self, buf, beg, len, col ):
      assert isinstance( buf, Buffer )
      assert isinstance( beg, int )
      assert isinstance( len, int )
      assert isinstance( col, int )

      self.buf = buf
      self.beg = beg   # start relative to the beginning of the file
      self.len = len   # length of stretch
      self.col = col   # column number of start position

   def getSubstring( self ):
      return self.buf.readPosition( self )

class Buffer( object ):
   EOF      = u'\u0100'     # 256

   def __init__( self, s ):
      self.buf    = s
      self.bufLen = len(s)
      self.pos    = 0
      self.lines  = s.splitlines( True )

   def Read( self ):
      if self.pos < self.bufLen:
         result = self.buf[self.pos]
         self.pos += 1
         return result
      else:
         return Buffer.EOF

   def ReadChars( self, numBytes=1 ):
      result = self.buf[ self.pos : self.pos + numBytes ]
      self.pos += numBytes
      return result

   def Peek( self ):
      if self.pos < self.bufLen:
         return self.buf[self.pos]
      else:
         return Scanner.buffer.EOF

   def getString( self, beg, end ):
      s = ''
      oldPos = self.getPos( )
      self.setPos( beg )
      while beg < end:
         s += self.Read( )
         beg += 1
      self.setPos( oldPos )
      return s

   def getPos( self ):
      return self.pos

   def setPos( self, value ):
      if value < 0:
         self.pos = 0
      elif value >= self.bufLen:
         self.pos = self.bufLen
      else:
         self.pos = value

   def readPosition( self, pos ):
      assert isinstance( pos, Position )
      self.setPos( pos.beg )
      return self.ReadChars( pos.len )

   def __iter__( self ):
      return iter(self.lines)

class Scanner(object):
   EOL     = u'\n'
   eofSym  = 0

   charSetSize = 256
   maxT = 12
   noSym = 12
   start = [
     9,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
    13, 13, 13, 13, 13, 13, 13, 13, 13, 13,  0,  0,  0,  0,  0,  0,
     0, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12,
    12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12,  0,  0,  0,  0,  0,
     0, 18, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12,
    12, 12, 12, 12, 12, 12, 12, 12, 12, 12, 12,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,  0,
     -1]


   def __init__( self, s ):
      self.buffer = Buffer( unicode(s) ) # the buffer instance

      self.ch        = u'\0'       # current input character
      self.pos       = -1          # column number of current character
      self.line      = 1           # line number of current character
      self.lineStart = 0           # start position of current line
      self.oldEols   = 0           # EOLs that appeared in a comment;
      self.NextCh( )
      self.ignore    = set( )      # set of characters to be ignored by the scanner
      self.ignore.add( ord(' ') )  # blanks are always white space

      # fill token list
      self.tokens = Token( )       # the complete input token stream
      node   = self.tokens

      node.next = self.NextToken( )
      node = node.next
      while node.kind != Scanner.eofSym:
         node.next = self.NextToken( )
         node = node.next

      node.next = node
      node.val  = u'EOF'
      self.t  = self.tokens     # current token
      self.pt = self.tokens     # current peek token

   def NextCh( self ):
      if self.oldEols > 0:
         self.ch = Scanner.EOL
         self.oldEols -= 1
      else:
         self.ch = self.buffer.Read( )
         self.pos += 1
         # replace isolated '\r' by '\n' in order to make
         # eol handling uniform across Windows, Unix and Mac
         if (self.ch == u'\r') and (self.buffer.Peek() != u'\n'):
            self.ch = Scanner.EOL
         if self.ch == Scanner.EOL:
            self.line += 1
            self.lineStart = self.pos + 1
      




   def CheckLiteral( self ):
      lit = self.t.val
      if lit == "abc":
         self.t.kind = 7
      elif lit == "a":
         self.t.kind = 9


   def NextToken( self ):
      while ord(self.ch) in self.ignore:
         self.NextCh( )
      
      apx = 0
      self.t = Token( )
      self.t.pos = self.pos
      self.t.col = self.pos - self.lineStart + 1
      self.t.line = self.line
      if ord(self.ch) < len(self.start):
         state = self.start[ord(self.ch)]
      else:
         state = 0
      buf = u''
      buf += unicode(self.ch)
      self.NextCh()

      done = False
      while not done:
         if state == -1:
            self.t.kind = Scanner.eofSym     # NextCh already done
            done = True
         elif state == 0:
            self.t.kind = Scanner.noSym      # NextCh already done
            done = True
         elif state == 1:
            if (self.ch >= '0' and self.ch <= '9'
                 or self.ch >= 'A' and self.ch <= 'Z'
                 or self.ch >= 'a' and self.ch <= 'z'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 1
            else:
               self.t.kind = 1
               self.t.val = buf
               self.CheckLiteral()
               return self.t
         elif state == 2:
            self.t.kind = 2
            done = True
         elif state == 3:

            self.pos = self.pos - apx - 1
            self.line = self.t.line
            self.buffer.setPos(self.pos+1)
            self.NextCh()
            self.t.kind = 3
            done = True
         elif state == 4:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 4
            elif self.ch == 'E':
               buf += unicode(self.ch)
               self.NextCh()
               state = 5
            else:
               self.t.kind = 4
               done = True
         elif state == 5:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 7
            elif (self.ch == '+'
                 or self.ch == '-'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 6
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 6:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 7
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 7:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 7
            else:
               self.t.kind = 4
               done = True
         elif state == 8:

            self.pos = self.pos - apx - 1
            self.line = self.t.line
            self.buffer.setPos(self.pos+1)
            self.NextCh()
            self.t.kind = 4
            done = True
         elif state == 9:
            self.t.kind = 5
            done = True
         elif state == 10:
            if self.ch == 'c':
               buf += unicode(self.ch)
               self.NextCh()
               state = 11
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 11:
            self.t.kind = 6
            done = True
         elif state == 12:
            if (self.ch >= '0' and self.ch <= '9'
                 or self.ch >= 'A' and self.ch <= 'Z'
                 or self.ch >= 'a' and self.ch <= 'z'):
               apx = 0
               buf += unicode(self.ch)
               self.NextCh()
               state = 1
            elif self.ch == '*':
               apx = 0
               buf += unicode(self.ch)
               self.NextCh()
               state = 2
            elif self.ch == '_':
               apx += 1
               buf += unicode(self.ch)
               self.NextCh()
               state = 14
            elif self.ch == '+':
               apx += 1
               buf += unicode(self.ch)
               self.NextCh()
               state = 3
            else:
               self.t.kind = 1
               self.t.val = buf
               self.CheckLiteral()
               return self.t
         elif state == 13:
            if (self.ch >= '0' and self.ch <= '9'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 13
            elif self.ch == '.':
               apx += 1
               buf += unicode(self.ch)
               self.NextCh()
               state = 15
            else:
               self.t.kind = 4
               done = True
         elif state == 14:
            if self.ch == '*':
               apx = 0
               buf += unicode(self.ch)
               self.NextCh()
               state = 2
            elif self.ch == '_':
               apx += 1
               buf += unicode(self.ch)
               self.NextCh()
               state = 14
            elif self.ch == '+':
               apx += 1
               buf += unicode(self.ch)
               self.NextCh()
               state = 3
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 15:
            if (self.ch >= '0' and self.ch <= '9'):
               apx = 0
               buf += unicode(self.ch)
               self.NextCh()
               state = 4
            elif self.ch == 'E':
               apx = 0
               buf += unicode(self.ch)
               self.NextCh()
               state = 5
            elif self.ch == '.':
               apx += 1
               buf += unicode(self.ch)
               self.NextCh()
               state = 8
            else:
               self.t.kind = 4
               done = True
         elif state == 16:
            self.t.kind = 8
            done = True
         elif state == 17:
            self.t.kind = 11
            done = True
         elif state == 18:
            if (self.ch >= '0' and self.ch <= '9'
                 or self.ch >= 'A' and self.ch <= 'Z'
                 or self.ch == 'a'
                 or self.ch >= 'c' and self.ch <= 'z'):
               apx = 0
               buf += unicode(self.ch)
               self.NextCh()
               state = 1
            elif self.ch == '*':
               apx = 0
               buf += unicode(self.ch)
               self.NextCh()
               state = 2
            elif self.ch == '_':
               apx += 1
               buf += unicode(self.ch)
               self.NextCh()
               state = 19
            elif self.ch == '+':
               apx += 1
               buf += unicode(self.ch)
               self.NextCh()
               state = 3
            elif self.ch == 'b':
               apx = 0
               buf += unicode(self.ch)
               self.NextCh()
               state = 20
            else:
               self.t.kind = 1
               self.t.val = buf
               self.CheckLiteral()
               return self.t
         elif state == 19:
            if self.ch == '*':
               apx = 0
               buf += unicode(self.ch)
               self.NextCh()
               state = 2
            elif self.ch == '_':
               apx += 1
               buf += unicode(self.ch)
               self.NextCh()
               state = 21
            elif self.ch == '+':
               apx += 1
               buf += unicode(self.ch)
               self.NextCh()
               state = 3
            else:
               self.t.kind = 10
               done = True
         elif state == 20:
            if (self.ch >= '0' and self.ch <= '9'
                 or self.ch >= 'A' and self.ch <= 'Z'
                 or self.ch >= 'a' and self.ch <= 'b'
                 or self.ch >= 'd' and self.ch <= 'z'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 1
            elif ord(self.ch) == 0:
               buf += unicode(self.ch)
               self.NextCh()
               state = 10
            elif self.ch == 'c':
               buf += unicode(self.ch)
               self.NextCh()
               state = 22
            else:
               self.t.kind = 1
               self.t.val = buf
               self.CheckLiteral()
               return self.t
         elif state == 21:
            if self.ch == '*':
               apx = 0
               buf += unicode(self.ch)
               self.NextCh()
               state = 23
            elif self.ch == '_':
               apx += 1
               buf += unicode(self.ch)
               self.NextCh()
               state = 14
            elif self.ch == '+':
               apx += 1
               buf += unicode(self.ch)
               self.NextCh()
               state = 3
            else:
               self.t.kind = Scanner.noSym
               done = True
         elif state == 22:
            if (self.ch >= '0' and self.ch <= '9'
                 or self.ch >= 'A' and self.ch <= 'Z'
                 or self.ch >= 'a' and self.ch <= 'z'):
               buf += unicode(self.ch)
               self.NextCh()
               state = 1
            elif self.ch == '+':
               buf += unicode(self.ch)
               self.NextCh()
               state = 16
            else:
               self.t.kind = 1
               self.t.val = buf
               self.CheckLiteral()
               return self.t
         elif state == 23:
            if self.ch == '*':
               buf += unicode(self.ch)
               self.NextCh()
               state = 17
            else:
               self.t.kind = 2
               done = True

      self.t.val = buf
      return self.t

   def Scan( self ):
      self.t = self.t.next
      self.pt = self.t.next
      return self.t

   def Peek( self ):
      self.pt = self.pt.next
      while self.pt.kind > self.maxT:
         self.pt = self.pt.next

      return self.pt

   def ResetPeek( self ):
      self.pt = self.t

