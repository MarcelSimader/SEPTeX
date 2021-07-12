"""
:Author: Marcel Simader
:Date: 29.06.2021

.. versionadded:: v0.1.0
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ IMPORTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

import os.path

from SEPTeX.LaTeX import *
from SEPTeX.TeXBase import *
from SEPTeX.TikZBase import *
from SEPTeX._test.test_TeXBase import LaTeXDocumentTestCase

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ UNIT TESTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# noinspection PyTypeChecker
class TestLaTeXDocument(LaTeXDocumentTestCase):

	def test_init(self):
		self.assertTrue(self.doc1._has_title)
		self.assertTrue(self.doc2._has_title)
		self.assertEqual(os.path.abspath("tmp/_test.tex"), self.doc1.path)
		self.assertEqual(os.path.abspath("tmp/_testabc.tex"), self.doc2.path)
		self.assertTupleEqual((), self.doc1.definitions)
		self.assertTupleEqual((("usepackage", "amsmath"),), self.doc2.definitions)

		self.assertRaises(TeXError, lambda: self.doc1.body)
		self.assertRaises(TeXError, lambda: self.doc1.preamble)
		self.assertRaises(TeXError, lambda: self.doc2.body)
		self.assertRaises(TeXError, lambda: self.doc2.preamble)

		self.assertRaises(TeXError, lambda: self.doc1.to_pdf("_"))
		self.assertRaises(TeXError, lambda: self.doc2.to_pdf("_"))

		self.assertDocumentContentsEqual(self.doc1)
		self.assertDocumentContentsEqual(self.doc2)

	def test_open(self):
		self.assertFalse(self.doc1.open)
		self.assertFalse(self.doc2.open)
		self.enter()
		self.assertTrue(self.doc1.open)
		self.assertTrue(self.doc2.open)

	def test_close(self):
		self.enter()
		self.exit()
		self.assertFalse(self.doc1.open)
		self.assertFalse(self.doc2.open)

	def test_include_statement(self):
		self.doc1.use_package("mathtools")
		self.doc1.use_tikz_library("arrows")
		self.enter()
		self.doc2.use_package("mathtools")
		self.doc2.use_tikz_library("arrows")
		self.exit()
		self.assertTupleEqual((("usepackage", "mathtools"), ("usepackage", "tikz"), ("usetikzlibrary", "arrows"),
							   ("usepackage", "relsize")), self.doc1.definitions)
		self.assertTupleEqual((("usepackage", "amsmath"), ("usepackage", "relsize"), ("usepackage", "mathtools"),
							   ("usepackage", "tikz"), ("usetikzlibrary", "arrows")), self.doc2.definitions)
		self.assertDocumentContentsEqual(self.doc1)
		self.assertDocumentContentsEqual(self.doc2)

	def test_init_document(self):
		self.enter()
		self.exit()
		self.assertLaTeXContains(self.doc1, r"\title{This is a title}", r"\author{python unittest}", r"\date{}",
								 r"\pagenumbering{gobble}", r"\maketitle")

		self.assertLaTeXContains(self.doc2, r"\title{title\\[0.4em]\smaller{subtitle}}", r"\date{}", r"\maketitle")

	def test_exit(self):
		self.assertFalse(self.doc1.successfully_saved_tex)
		self.assertFalse(self.doc2.successfully_saved_tex)
		self.enter()
		self.assertFalse(self.doc1.successfully_saved_tex)
		self.assertFalse(self.doc2.successfully_saved_tex)
		self.exit()
		self.assertTrue(self.doc1.successfully_saved_tex)
		self.assertTrue(self.doc2.successfully_saved_tex)
		try:
			self.assertTrue(os.path.isfile(self.doc1.path))
			self.assertTrue(os.path.isfile(self.doc2.path))
			# at least 50 bytes
			self.assertGreaterEqual(os.path.getsize(self.doc1.path), 50)
			self.assertGreaterEqual(os.path.getsize(self.doc2.path), 50)
		except OSError:
			self.fail("file does not exist")

	def test_to_pdf(self):
		self.assertRaises(TeXError, lambda: self.doc1.to_pdf("_"))
		self.assertRaises(TeXError, lambda: self.doc2.to_pdf("_"))
		self.enter()
		self.assertRaises(TeXError, lambda: self.doc1.to_pdf("_"))
		self.assertRaises(TeXError, lambda: self.doc2.to_pdf("_"))
		self.exit()

		path = "tmp/_test.pdf"
		aux_path = "tmp/.aux"
		try:
			if os.path.isdir(aux_path):
				shutil.rmtree(aux_path)
			if os.path.isfile(path):
				os.remove(path)
		except OSError as e:
			print(f"did not delete file: {e}")

		# only test on one for now so it's faster
		self.assertRaises(NotImplementedError, lambda: self.doc1.to_pdf(path, engine="abc123"))
		self.doc1.to_pdf(path, overwrite=False, delete_aux_files=False, engine="pdftex", custom_options="")
		self.assertTrue(os.path.isdir(aux_path))
		self.assertTrue(os.path.isfile(path))
		self.assertRaises(FileExistsError, lambda: self.doc1.to_pdf(path))
		self.doc1.to_pdf(path, overwrite=True, delete_aux_files=True, engine="pdftex", custom_options="")
		self.assertFalse(os.path.isdir(aux_path))
		self.assertTrue(os.path.isfile(path))

# noinspection PyTypeChecker
class TestLaTeXEnvironment(LaTeXDocumentTestCase):

	def setUp(self) -> None:
		super(TestLaTeXEnvironment, self).setUp()
		self.env1 = LaTeXEnvironment(self.doc1, "itemize", "align=left", ("enumitem",), 1)
		self.env2 = LaTeXEnvironment(self.doc2, "enumerate", "", (), 1)
		self.env3 = LaTeXEnvironment(self.env2, "center", "", ("random_package",), 0)
		self.envs = (self.env1, self.env2, self.env3)

	def tearDown(self) -> None:
		super(TestLaTeXEnvironment, self).tearDown()
		del self.env1, self.env2, self.env3

	def enter_env(self):
		for env in self.envs:
			env.__enter__()

	def enter(self):
		super(TestLaTeXEnvironment, self).enter()
		self.enter_env()

	def exit_env(self):
		for env in reversed(self.envs):
			env.__exit__(None, None, None)

	def exit(self):
		self.exit_env()
		super(TestLaTeXEnvironment, self).exit()

	def test_init(self):
		self.assertEqual("[align=left]", self.env1.options)
		self.assertEqual("", self.env2.options)

		self.assertIn(("usepackage", "enumitem"), self.doc1.definitions)
		self.assertIn(("usepackage", "random_package"), self.doc2.definitions)

		self.assertEqual(self.doc1, self.env1.document)
		self.assertEqual(self.doc1, self.env1.document)
		self.assertEqual(self.doc1, self.env1.parent_env)
		self.assertEqual(self.doc2, self.env2.document)
		self.assertEqual(self.doc2, self.env2.document)
		self.assertEqual(self.doc2, self.env2.parent_env)
		self.assertEqual(self.doc2, self.env3.document)
		self.assertEqual(self.doc2, self.env3.document)
		self.assertEqual(self.env2, self.env3.parent_env)

		self.assertEqual(r"\begin{itemize}[align=left]", self.env1.begin_text)
		self.assertEqual(r"\end{itemize}", self.env1.end_text)
		self.assertEqual(r"\begin{enumerate}", self.env2.begin_text)
		self.assertEqual(r"\end{enumerate}", self.env2.end_text)
		self.assertEqual(r"\begin{center}", self.env3.begin_text)
		self.assertEqual(r"\end{center}", self.env3.end_text)

	def test_open(self):
		self.assertRaises(TeXError, lambda: self.enter_env())
		self.assertRaises(TeXError, lambda: self.env3.__enter__())

		self.enter()
		self.assertEqual(self.doc1.body, self.env1.parent_handler)
		self.assertEqual(self.doc2.body, self.env2.parent_handler)
		self.assertEqual(self.env2._handler, self.env3.parent_handler)

		self.assertLaTeXContains(self.doc1, r"\begin{itemize}[align=left]")
		self.assertLaTeXContains(self.doc2, r"\begin{enumerate}")
		self.assertLaTeXContains(self.env2, r"\begin{center}")

		self.assertTrue(self.env1.open)
		self.assertTrue(self.env2.open)
		self.assertTrue(self.env3.open)

	def test_close_order(self):
		self.enter()
		# exit docs
		super(TestLaTeXEnvironment, self).exit()
		self.assertRaises(TeXError, lambda: self.exit_env())

	def test_close(self):
		self.enter()
		self.exit()
		self.assertFalse(self.env1.open)
		self.assertFalse(self.env2.open)
		self.assertFalse(self.env3.open)

		self.assertLaTeXContains(self.doc1, r"\begin{itemize}[align=left]", r"\end{itemize}")
		self.assertLaTeXContains(self.env2, r"\begin{center}", r"\end{center}")
		self.assertLaTeXContains(self.doc2, r"\begin{enumerate}", r"\begin{center}", r"\end{center}",
								 r"\end{enumerate}")

	def test_write(self):
		self.assertRaises(TeXError, lambda: self.env1.write("test"))
		self.assertRaises(TeXError, lambda: self.env2.write("test"))
		self.assertRaises(TeXError, lambda: self.env3.write("test"))
		# enter docs
		super(TestLaTeXEnvironment, self).enter()

		self.env1.__enter__()
		self.env2.__enter__()
		self.env1.write("abc123")
		self.env2.write("abc123")
		self.assertLaTeXContains(self.env1, r"\begin{itemize}[align=left]", r"abc123", r"\end{itemize}")
		self.assertLaTeXContains(self.env2, r"\begin{enumerate}", r"abc123", r"\end{enumerate}")

		self.assertRaises(TeXError, lambda: self.env3.write("test"))
		self.env3.__enter__()
		self.env3.write("abc123")
		self.assertLaTeXContains(self.env3, r"\begin{center}", r"abc123", r"\end{center}")

		self.env3.__exit__(None, None, None)
		self.assertLaTeXContains(self.env2, r"\begin{enumerate}", r"abc123", r"\begin{center}", r"abc123",
								 r"\end{center}", r"\end{enumerate}")

		self.env2.__exit__(None, None, None)
		self.env1.__exit__(None, None, None)
		self.assertLaTeXContains(self.doc1, r"\begin{itemize}[align=left]", r"abc123", r"\end{itemize}")
		self.assertLaTeXContains(self.doc2, r"\begin{enumerate}", r"abc123", r"\begin{center}", r"abc123",
								 r"\end{center}", r"\end{enumerate}")
