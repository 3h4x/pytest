import py
import os, sys
from _py.io import terminalwriter 

def test_terminal_width_COLUMNS(monkeypatch):
    """ Dummy test for get_terminal_width
    """
    fcntl = py.test.importorskip("fcntl") 
    monkeypatch.setattr(fcntl, 'ioctl', lambda *args: int('x'))
    monkeypatch.setenv('COLUMNS', '42')
    assert terminalwriter.get_terminal_width() == 41
    monkeypatch.delenv('COLUMNS', raising=False)

def test_terminalwriter_defaultwidth_80(monkeypatch):
    monkeypatch.setattr(terminalwriter, '_getdimensions', lambda: 0/0)
    monkeypatch.delenv('COLUMNS', raising=False)
    tw = py.io.TerminalWriter()  
    assert tw.fullwidth == 80-1

def test_terminalwriter_computes_width(monkeypatch):
    monkeypatch.setattr(terminalwriter, 'get_terminal_width', lambda: 42)
    tw = py.io.TerminalWriter()  
    assert tw.fullwidth == 42
    
def test_terminalwriter_default_instantiation():
    tw = py.io.TerminalWriter(stringio=True)
    assert hasattr(tw, 'stringio')

def test_terminalwriter_dumb_term_no_markup(monkeypatch):
    monkeypatch.setattr(os, 'environ', {'TERM': 'dumb', 'PATH': ''})
    class MyFile:
        def isatty(self):
            return True
    monkeypatch.setattr(sys, 'stdout', MyFile())
    assert sys.stdout.isatty()
    tw = py.io.TerminalWriter()
    assert not tw.hasmarkup

def test_unicode_encoding():
    msg = py.builtin._totext('b\u00f6y', 'utf8')
    for encoding in 'utf8', 'latin1':
        l = []
        tw = py.io.TerminalWriter(l.append, encoding=encoding)
        tw.line(msg)
        assert l[0] == msg.encode(encoding)

class BaseTests:
    def test_line(self):    
        tw = self.getwriter()
        tw.line("hello")
        l = self.getlines()
        assert len(l) == 1
        assert l[0] == "hello\n"

    def test_line_unicode(self):    
        tw = self.getwriter()
        for encoding in 'utf8', 'latin1':
            tw._encoding = encoding 
            msg = py.builtin._totext('b\u00f6y', 'utf8')
            tw.line(msg)
            l = self.getlines()
            assert l[0] == msg + "\n"

    def test_sep_no_title(self):
        tw = self.getwriter()
        tw.sep("-", fullwidth=60) 
        l = self.getlines()
        assert len(l) == 1
        assert l[0] == "-" * 60 + "\n"

    def test_sep_with_title(self):
        tw = self.getwriter()
        tw.sep("-", "hello", fullwidth=60) 
        l = self.getlines()
        assert len(l) == 1
        assert l[0] == "-" * 26 + " hello " + "-" * 27 + "\n"

    @py.test.mark.skipif("sys.platform == 'win32'")
    def test__escaped(self):
        tw = self.getwriter()
        text2 = tw._escaped("hello", (31))
        assert text2.find("hello") != -1

    @py.test.mark.skipif("sys.platform == 'win32'")
    def test_markup(self):
        tw = self.getwriter()
        for bold in (True, False):
            for color in ("red", "green"):
                text2 = tw.markup("hello", **{color: True, 'bold': bold})
                assert text2.find("hello") != -1
        py.test.raises(ValueError, "tw.markup('x', wronkw=3)")
        py.test.raises(ValueError, "tw.markup('x', wronkw=0)")

    def test_line_write_markup(self):
        tw = self.getwriter()
        tw.hasmarkup = True
        tw.line("x", bold=True)
        tw.write("x\n", red=True)
        l = self.getlines()
        if sys.platform != "win32":
            assert len(l[0]) > 2, l
            assert len(l[1]) > 2, l

    def test_attr_fullwidth(self):
        tw = self.getwriter()
        tw.sep("-", "hello", fullwidth=70)
        tw.fullwidth = 70
        tw.sep("-", "hello")
        l = self.getlines()
        assert len(l[0]) == len(l[1])

class TestTmpfile(BaseTests):
    def getwriter(self):
        self.path = py.test.config.ensuretemp("terminalwriter").ensure("tmpfile")
        self.tw = py.io.TerminalWriter(self.path.open('w+'))
        return self.tw
    def getlines(self):
        io = self.tw._file
        io.flush()
        return self.path.open('r').readlines()

class TestWithStringIO(BaseTests):
    def getwriter(self):
        self.tw = py.io.TerminalWriter(stringio=True)
        return self.tw
    def getlines(self):
        io = self.tw.stringio
        io.seek(0)
        return io.readlines()

class TestCallableFile(BaseTests):    
    def getwriter(self):
        self.writes = []
        return py.io.TerminalWriter(self.writes.append)

    def getlines(self):
        io = py.io.TextIO()
        io.write("".join(self.writes))
        io.seek(0)
        return io.readlines()

def test_attr_hasmarkup():
    tw = py.io.TerminalWriter(stringio=True)
    assert not tw.hasmarkup
    tw.hasmarkup = True
    tw.line("hello", bold=True)
    s = tw.stringio.getvalue()
    assert len(s) > len("hello")

    
