"""
:Author: Marcel Simader
:Date: 29.06.2021

.. versionadded:: v0.1.0
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ IMPORTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import os.path
import unittest

from SEPTeX.LaTeX import *
from SEPTeX.TeXBase import *
from SEPTeX.TikZBase import *

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ UNIT TESTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class LaTeXDocumentTestCase(unittest.TestCase):

	def setUp(self) -> None:
		self.doc1 = LaTeXDocument("tmp/_test.tex",
								  document_class="article", document_options="a4paper, 12pt",
								  default_packages=(),
								  title="This is a title", subtitle=None, author="python unittest",
								  show_date=False, show_page_numbers=False, line_wrap_length=None)
		self.doc2 = LaTeXDocument("tmp/_testabc",
								  document_class="article", document_options="a3paper, 10pt",
								  default_packages=("amsmath",),
								  title="title", subtitle="subtitle", author=None,
								  show_date=False, show_page_numbers=True, line_wrap_length=None)
		self.docs = (self.doc1, self.doc2)

	def tearDown(self) -> None:
		try:
			for doc in self.docs:
				if os.path.isfile(doc.path):
					os.remove(doc.path)
		except OSError as e:
			print(f"did not delete file: {e}")
		del self.doc1, self.doc2

	def enter(self):
		for doc in self.docs:
			doc.__enter__()

	def exit(self):
		for doc in self.docs:
			doc.__exit__(None, None, None)

	def assertDocumentContentsEqual(self, document: LaTeXDocument):
		self.assertMultiLineEqual(LaTeXDocument.LaTeXTemplate.format(
				document.document_options,
				document.document_class,
				str(document._definitions),
				str(document._preamble),
				str(document._body)
				), str(document))

	def assertLaTeXContains(self, doc: Union[LaTeXDocument, LaTeXEnvironment], *strings: str):
		any_char = r"(.*\s)*"
		strings = [s.replace("\\", "\\\\")
					   .replace("{", "\\{").replace("}", "\\}")
					   .replace("[", "\\[").replace("]", "\\]") for s in strings]
		self.assertRegex(str(doc), expected_regex=any_char + any_char.join(strings) + any_char)

# noinspection PyTypeChecker
class TestTeXResource(unittest.TestCase):
	class TestImplementationResource(TeXResource):
		def __str__(self) -> str:
			return ""

	@staticmethod
	def name_f(f: Callable) -> Callable:
		def test(*args, **kwargs):
			return f(*args, **kwargs)

		return test

	def setUp(self) -> None:
		self.no_reopen = self.TestImplementationResource()
		self.reopen = self.TestImplementationResource(can_reopen=True)

	def tearDown(self) -> None:
		del self.no_reopen, self.reopen

	def open(self):
		self.no_reopen.__enter__()
		self.reopen.__enter__()

	def close(self):
		self.no_reopen.__exit__(None, None, None)
		self.reopen.__exit__(None, None, None)

	def test_init(self):
		self.assertFalse(self.no_reopen.open)
		self.assertFalse(self.reopen.open)

	def test_open_counter(self):
		self.assertEqual(0, self.no_reopen._open_counter)
		self.assertEqual(0, self.reopen._open_counter)
		self.open()
		self.assertEqual(1, self.no_reopen._open_counter)
		self.assertEqual(1, self.reopen._open_counter)

		self.reopen.__enter__()
		self.assertEqual(2, self.reopen._open_counter)
		self.reopen.__exit__(None, None, None)
		self.assertEqual(2, self.reopen._open_counter)

	def test_open(self):
		self.open()
		self.assertTrue(self.no_reopen.open)
		self.assertTrue(self.reopen.open)

	def test_close(self):
		self.open()
		self.close()
		self.assertFalse(self.no_reopen.open)
		self.assertFalse(self.reopen.open)

	def test_require_closed(self):
		self.assertIsNone(self.no_reopen.__require_closed__())
		self.assertIsNone(self.reopen.__require_closed__())
		self.open()
		self.assertRaisesRegex(TeXError, r".*(closed).*('test').*", self.name_f(self.no_reopen.__require_closed__))
		self.assertRaisesRegex(TeXError, r".*(closed).*('test').*", self.name_f(self.reopen.__require_closed__))
		self.close()
		self.assertIsNone(self.no_reopen.__require_closed__())
		self.assertIsNone(self.reopen.__require_closed__())

	def test_require_open(self):
		self.assertRaisesRegex(TeXError, r".*(open).*('test').*", self.name_f(self.no_reopen.__require_open__))
		self.assertRaisesRegex(TeXError, r".*(open).*('test').*", self.name_f(self.reopen.__require_open__))
		self.open()
		self.assertIsNone(self.no_reopen.__require_open__())
		self.assertIsNone(self.reopen.__require_open__())
		self.close()
		self.assertRaisesRegex(TeXError, r".*(open).*('test').*", self.name_f(self.no_reopen.__require_open__))
		self.assertRaisesRegex(TeXError, r".*(open).*('test').*", self.name_f(self.reopen.__require_open__))

	def test_require_virgin(self):
		self.assertIsNone(self.no_reopen.__require_virgin__())
		self.assertIsNone(self.reopen.__require_virgin__())
		self.open()
		self.assertRaisesRegex(TeXError, r".*(not have been opened).*('test').*",
							   self.name_f(self.no_reopen.__require_virgin__))
		self.assertRaisesRegex(TeXError, r".*(not have been opened).*('test').*",
							   self.name_f(self.reopen.__require_virgin__))
		self.close()
		self.assertRaisesRegex(TeXError, r".*(not have been opened).*('test').*",
							   self.name_f(self.no_reopen.__require_virgin__))
		self.assertRaisesRegex(TeXError, r".*(not have been opened).*('test').*",
							   self.name_f(self.reopen.__require_virgin__))

	def test_require_used(self):
		self.assertRaisesRegex(TeXError, r".*(have been opened and closed).*('test').*",
							   self.name_f(self.no_reopen.__require_used__))
		self.assertRaisesRegex(TeXError, r".*(have been opened and closed).*('test').*",
							   self.name_f(self.reopen.__require_used__))
		self.open()
		self.assertRaisesRegex(TeXError, r".*(have been opened and closed).*('test').*",
							   self.name_f(self.no_reopen.__require_used__))
		self.assertRaisesRegex(TeXError, r".*(have been opened and closed).*('test').*",
							   self.name_f(self.reopen.__require_used__))
		self.close()
		self.assertIsNone(self.no_reopen.__require_used__())
		self.assertIsNone(self.reopen.__require_used__())

	def test_reopen(self):
		self.open()
		self.close()
		self.assertRaises(TeXError, lambda: self.no_reopen.__enter__())
		self.assertIsNone(self.reopen.__enter__())

	def test_str(self):
		self.assertEqual("", str(self.no_reopen))
		self.assertEqual("", str(self.reopen))

# noinspection PyTypeChecker
class TestTeXHandler(unittest.TestCase):

	def setUp(self) -> None:
		self.plain = TeXHandler()
		self.indent = TeXHandler(indent_level=1)
		self.wrap = TeXHandler(line_wrap_length=10)
		self.wrap_indent = TeXHandler(indent_level=1, line_wrap_length=10)

	def tearDown(self) -> None:
		del self.plain, self.indent, self.wrap, self.wrap_indent

	def write(self, s):
		self.plain.write(s)
		self.indent.write(s)
		self.wrap.write(s)
		self.wrap_indent.write(s)

	def newline(self):
		self.plain.newline()
		self.indent.newline()
		self.wrap.newline()
		self.wrap_indent.newline()

	def test_init(self):
		self.assertEqual(list(), self.plain._data)
		self.assertEqual(list(), self.indent._data)
		self.assertEqual(list(), self.wrap._data)
		self.assertEqual(list(), self.wrap_indent._data)

	def test_write_empty(self):
		self.write("")
		self.assertTupleEqual(((0, ""),), self.plain.data)
		self.assertTupleEqual(((1, ""),), self.indent.data)
		self.assertTupleEqual(((0, ""),), self.wrap.data)
		self.assertTupleEqual(((1, ""),), self.wrap_indent.data)

	def test_newline_write_empty(self):
		self.write("\n")
		self.assertTupleEqual(((0, ""), (0, "")), self.plain.data)
		self.assertTupleEqual(((1, ""), (1, "")), self.indent.data)
		self.assertTupleEqual(((0, ""), (0, "")), self.wrap.data)
		self.assertTupleEqual(((1, ""), (1, "")), self.wrap_indent.data)

	def test_newline(self):
		self.newline()
		self.assertTupleEqual(((0, ""),), self.plain.data)
		self.assertEqual(1, len(self.plain))
		self.assertTupleEqual(((1, ""),), self.indent.data)
		self.assertEqual(1, len(self.indent))
		self.assertTupleEqual(((0, ""),), self.wrap.data)
		self.assertEqual(1, len(self.wrap))
		self.assertTupleEqual(((1, ""),), self.wrap_indent.data)
		self.assertEqual(1, len(self.wrap_indent))

	def test_write_short(self):
		self.write("test")
		self.assertTupleEqual(((0, "test"),), self.plain.data)
		self.assertTupleEqual(((1, "test"),), self.indent.data)
		self.assertTupleEqual(((0, "test"),), self.wrap.data)
		self.assertTupleEqual(((1, "test"),), self.wrap_indent.data)
		self.write("abc")
		self.assertTupleEqual(((0, "test"), (0, "abc")), self.plain.data)
		self.assertTupleEqual(((1, "test"), (1, "abc")), self.indent.data)
		self.assertTupleEqual(((0, "test"), (0, "abc")), self.wrap.data)
		self.assertTupleEqual(((1, "test"), (1, "abc")), self.wrap_indent.data)

	def test_newline_write_short(self):
		self.write("test\n  abc")
		self.assertTupleEqual(((0, "test"), (0, "  abc")), self.plain.data)
		self.assertEqual(2, len(self.plain))
		self.assertTupleEqual(((1, "test"), (1, "  abc")), self.indent.data)
		self.assertEqual(2, len(self.indent))
		self.assertTupleEqual(((0, "test"), (0, "  abc")), self.wrap.data)
		self.assertEqual(2, len(self.wrap))
		self.assertTupleEqual(((1, "test"), (1, "  abc")), self.wrap_indent.data)
		self.assertEqual(2, len(self.wrap_indent))
		self.write("123")
		self.assertTupleEqual(((0, "test"), (0, "  abc"), (0, "123")), self.plain.data)
		self.assertEqual(3, len(self.plain))
		self.assertTupleEqual(((1, "test"), (1, "  abc"), (1, "123")), self.indent.data)
		self.assertEqual(3, len(self.indent))
		self.assertTupleEqual(((0, "test"), (0, "  abc"), (0, "123")), self.wrap.data)
		self.assertEqual(3, len(self.wrap))
		self.assertTupleEqual(((1, "test"), (1, "  abc"), (1, "123")), self.wrap_indent.data)
		self.assertEqual(3, len(self.wrap_indent))

	def test_write_long(self):
		self.write("This is a long   line.")
		self.assertTupleEqual(((0, "This is a long   line."),), self.plain.data)
		self.assertTupleEqual(((1, "This is a long   line."),), self.indent.data)
		self.assertTupleEqual(((0, "This is a long   line."),), self.wrap.data)
		self.assertTupleEqual(((1, "This is a long   line."),), self.wrap_indent.data)

	def test_wrap_no_hanging_indent(self):
		self.write("This is a long   line.")
		self.plain.wrap_lines(tab_width=4, hanging_indent=False)
		self.indent.wrap_lines(tab_width=4, hanging_indent=False)
		self.wrap.wrap_lines(tab_width=4, hanging_indent=False)
		self.wrap_indent.wrap_lines(tab_width=4, hanging_indent=False)
		self.assertTupleEqual(((0, "This is a long   line."),), self.plain.data)
		self.assertTupleEqual(((1, "This is a long   line."),), self.indent.data)
		self.assertTupleEqual(((0, "This is a long "), (0, "line."),), self.wrap.data)
		self.assertTupleEqual(((1, "This is "), (1, "a long "), (1, "line."),), self.wrap_indent.data)

	def test_wrap_hanging_indent(self):
		self.write("This is a long   line.")
		self.plain.wrap_lines(tab_width=4, hanging_indent=True)
		self.indent.wrap_lines(tab_width=4, hanging_indent=True)
		self.wrap.wrap_lines(tab_width=4, hanging_indent=True)
		self.wrap_indent.wrap_lines(tab_width=4, hanging_indent=True)
		self.assertTupleEqual(((0, "This is a long   line."),), self.plain.data)
		self.assertTupleEqual(((1, "This is a long   line."),), self.indent.data)
		self.assertTupleEqual(((0, "This is a long "), (1, "line."),), self.wrap.data)
		self.assertTupleEqual(((1, "This is "), (2, "a long "), (2, "line."),), self.wrap_indent.data)

	def test_wrap_comment_hanging_indent(self):
		self.write("This is a very very % long line.")
		self.plain.wrap_lines(tab_width=4, hanging_indent=True)
		self.indent.wrap_lines(tab_width=4, hanging_indent=True)
		self.wrap.wrap_lines(tab_width=4, hanging_indent=True)
		self.wrap_indent.wrap_lines(tab_width=4, hanging_indent=True)
		self.assertTupleEqual(((0, "This is a very very % long line."),), self.plain.data)
		self.assertTupleEqual(((1, "This is a very very % long line."),), self.indent.data)
		self.assertTupleEqual(((0, "This is a very "), (1, "very % "), (1, "% long "), (1, "% line."),), self.wrap.data)
		self.assertTupleEqual(((1, "This is "), (2, "a very "), (2, "very "), (2, "% long "), (2, "% line."),),
							  self.wrap_indent.data)

	def test_write_handler_to_handler(self):
		self.write("abc 123")
		self.assertTupleEqual(((0, "abc 123"),), self.plain.data)
		self.assertTupleEqual(((1, "abc 123"),), self.indent.data)
		self.assertTupleEqual(((0, "abc 123"),), self.wrap.data)
		self.assertTupleEqual(((1, "abc 123"),), self.wrap_indent.data)

		self.plain.write(self.indent)
		self.assertTupleEqual(((0, "abc 123"), (1, "abc 123")), self.plain.data)
		self.assertTupleEqual(((1, "abc 123"),), self.indent.data)

		self.wrap_indent.write(self.wrap)
		self.assertTupleEqual(((0, "abc 123"),), self.wrap.data)
		self.assertTupleEqual(((1, "abc 123"), (1, "abc 123")), self.wrap_indent.data)
