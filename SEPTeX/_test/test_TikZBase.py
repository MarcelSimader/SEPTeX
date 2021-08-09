"""
:Author: Marcel Simader
:Date: 29.06.2021

.. versionadded:: v0.1.0
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ IMPORTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import random
import unittest

from SEPTeX.TikZBase import *

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ UNIT TESTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TikZUnitTest(unittest.TestCase):

	def assertCollectionEquals(self, first, second, msg=None):
		self.assertTupleEqual(tuple(first), tuple(second), msg=msg)

class TestTikZWriteable(TikZUnitTest):
	class TestImplementationWriteable(TikZWriteable):
		def to_tikz(self) -> str:
			return "abc"

	def setUp(self) -> None:
		self.test = TestTikZWriteable.TestImplementationWriteable(("xcolor",), ("arrows",))

	def tearDown(self) -> None:
		del self.test

	def test_init(self):
		self.assertCollectionEquals(("xcolor",), self.test.required_packages)
		self.assertCollectionEquals(("arrows",), self.test.required_tikz_libraries)

	def test_str(self):
		self.assertEqual("abc", str(self.test))
		self.assertEqual("abc", self.test.to_tikz())

	def test_register_required_package_library(self):
		self.assertCollectionEquals(("xcolor",), self.test.required_packages)
		self.test.__register_required_package__("tikz")
		self.assertCollectionEquals(("xcolor", "tikz"), self.test.required_packages)

		self.assertCollectionEquals(("arrows",), self.test.required_tikz_libraries)
		self.test.__register_required_tikz_library__("positioning")
		self.assertCollectionEquals(("arrows", "positioning"), self.test.required_tikz_libraries)

class TestTikZNamed(TikZUnitTest):
	class TestImplementationNamed(TikZNamed):

		@property
		def name(self) -> str:
			return "name"

		@property
		def definition(self) -> str:
			return r"\define;"

		def __hash__(self) -> int:
			return 1

		def __eq__(self, other) -> bool:
			return False

	def setUp(self) -> None:
		self.test = TestTikZNamed.TestImplementationNamed((), ("arrows",))

	def tearDown(self) -> None:
		del self.test

	def test_init(self):
		self.assertEqual("name", self.test.name)
		self.assertEqual("name", str(self.test))
		self.assertEqual(r"\define;", self.test.definition)
		self.assertEqual(1, hash(self.test))
		self.assertFalse(self.test == 3)

class TestTikZDefinesNamed(TikZUnitTest):
	class TestImplementationNamed(TikZNamed):

		def __init__(self, name: str):
			super(TestTikZDefinesNamed.TestImplementationNamed, self).__init__((), ())
			self._name = name

		@property
		def name(self) -> str:
			return self._name

		@property
		def definition(self) -> str:
			return r"\define;"

		def __hash__(self) -> int:
			return hash(self._name)

		def __eq__(self, other) -> bool:
			return isinstance(other, TestTikZDefinesNamed.TestImplementationNamed) and self._name == other._name

	class TestImplementationDefinesWriteable(TikZDefinesWriteable[TestImplementationNamed]):

		def to_tikz(self) -> str:
			return " ".join([x.name for x in self.required_named_objects])

	def setUp(self) -> None:
		self.named = TestTikZDefinesNamed.TestImplementationNamed("ham.spam")
		self.other_named = TestTikZDefinesNamed.TestImplementationNamed("hello")
		self.test = TestTikZDefinesNamed. \
			TestImplementationDefinesWriteable((),
											   (),
											   (TikZStyle(), TikZStyle(fill=TikZColor.RED)),
											   (self.named,))

	def tearDown(self) -> None:
		del self.test, self.named

	def test_init(self):
		self.assertCollectionEquals((), self.test.required_packages)
		self.assertCollectionEquals((), self.test.required_tikz_libraries)
		self.assertCollectionEquals((self.named, TikZColor.RED), self.test.required_named_objects)

	def test_register_named(self):
		self.assertCollectionEquals((self.named, TikZColor.RED), self.test.required_named_objects)
		self.assertDictEqual({self.named: None, TikZColor.RED: None}, self.test._writeable_objs)

		self.test.__register_named_object__(self.named)
		self.assertCollectionEquals((self.named, TikZColor.RED), self.test.required_named_objects)
		self.assertDictEqual({self.named: None, TikZColor.RED: None}, self.test._writeable_objs)

		self.test.__register_named_object__(self.named, self.other_named, TikZColor.RED)
		self.assertCollectionEquals((self.named, TikZColor.RED, self.other_named), self.test.required_named_objects)
		self.assertDictEqual({self.named: None, TikZColor.RED: None, self.other_named: None}, self.test._writeable_objs)

		self.test.__register_named_object__(TestTikZDefinesNamed.TestImplementationNamed("ham.spam"))
		self.assertCollectionEquals((self.named, TikZColor.RED, self.other_named), self.test.required_named_objects)
		self.assertDictEqual({self.named: None, TikZColor.RED: None, self.other_named: None}, self.test._writeable_objs)

	def test_str(self):
		self.assertEqual("ham.spam RED!100", str(self.test))
		self.assertEqual("ham.spam RED!100", self.test.to_tikz())

		self.test.__register_named_object__(TestTikZDefinesNamed.TestImplementationNamed("ham.spam"))
		self.assertEqual("ham.spam RED!100", str(self.test))
		self.assertEqual("ham.spam RED!100", self.test.to_tikz())

		self.test.__register_named_object__(self.named, self.other_named, TikZColor.RED)
		self.assertEqual("ham.spam RED!100 hello", str(self.test))
		self.assertEqual("ham.spam RED!100 hello", self.test.to_tikz())

# noinspection PyTypeChecker
class TestTikZColor(TikZUnitTest):

	def setUp(self) -> None:
		random.seed(62123)
		self.colors, self.colors_alpha = list(), list()
		self.vals = (("RGB", 10, 20, 30), ("RGB", 0, 0, 0), ("RGB", 255, 120, 0),
					 ("rgb", 0, 0, 0), ("rgb", 0.5, 0.8, 0.125), ("rgb", 1.0, 0.23, 0.831))
		self.vals_alpha = (("RGB", 10, 20, 30, 255), ("RGB", 0, 0, 0, 0), ("RGB", 255, 120, 0, 150),
						   ("rgb", 0, 0, 0, 0), ("rgb", 0.5, 0.8, 0.125, 0.3), ("rgb", 1.0, 0.23, 0.831, 0.9))

		for i, val in enumerate(self.vals):
			self.colors.append(TikZColor(str(i), val[1:], val[0], generate_unique_name=False))

		for i, val in enumerate(self.vals_alpha):
			self.colors_alpha.append(TikZColor(str(i), val[1:], val[0], generate_unique_name=False))

		self.iter = lambda: zip(range(0, len(self.colors)), self.colors, self.colors_alpha, self.vals, self.vals_alpha)

	def tearDown(self) -> None:
		del self.colors, self.colors_alpha, self.vals, self.vals_alpha, self.iter

	def test_mode_error(self):
		with self.assertRaises(NotImplementedError):
			TikZColor("abc1", (0, 2, 3), "abc")
		with self.assertRaises(NotImplementedError):
			TikZColor("abc2", (0, 2, 3), "RGb")
		with self.assertRaises(NotImplementedError):
			TikZColor("abc3", (0, 2, 3), "")

	def test_validate_color_value(self):
		for i, c, c_a, v, v_a in self.iter():
			self.assertIsNone(c.__validate_color_value__(v[1:]))
			self.assertIsNone(c_a.__validate_color_value__(v_a[1:]))

		for err_RGB in ((-1, 0, 0), (0, 0), ("abc", 0, 1, 0), (118, 220, 256), (20, 20, 20, 20, 20)):
			with self.assertRaises(ValueError):
				TikZColor("test", (0, 0, 0), "RGB").__validate_color_value__(err_RGB)

		for err_rgb in ((-0.01, 0, 0), (0, 0), ("abc", 0, 1, 0), (0.2, 1, 1.1), (0.5, 0.5, 0.5, 0.2, 0.2)):
			with self.assertRaises(ValueError):
				TikZColor("test", (0, 0, 0), "rgb").__validate_color_value__(err_rgb)

	def test_init(self):
		for i, c, c_a, v, v_a in self.iter():
			self.assertTupleEqual(v[1:], c.value)
			self.assertTupleEqual(v_a[1:], c_a.value)
			self.assertEqual(v[1], c.red)
			self.assertEqual(v[2], c.green)
			self.assertEqual(v[3], c.blue)
			self.assertIsNone(c.alpha)
			self.assertEqual(v_a[1], c_a.red)
			self.assertEqual(v_a[2], c_a.green)
			self.assertEqual(v_a[3], c_a.blue)
			self.assertEqual(v_a[4], c_a.alpha)

			self.assertEqual(v[0], c.mode)
			self.assertEqual(v_a[0], c_a.mode)

			self.assertEqual(str(i), c.raw_name)
			self.assertEqual(str(i), c_a.raw_name)

			self.assertCollectionEquals(("xcolor",), c.required_packages)
			self.assertCollectionEquals((), c.required_tikz_libraries)

	def test_definition(self):
		for i, c, c_a, v, v_a in self.iter():
			self.assertEqual(f"\\definecolor{{{str(i)}}}{{{v[0]}}}"
							 f"{{{', '.join([str(x) for x in v[1:]])}}}", c.definition)
			self.assertEqual(f"\\definecolor{{{str(i)}}}{{{v_a[0]}}}"
							 f"{{{', '.join([str(x) for x in v_a[1:4]])}}}", c_a.definition)

	def test_xcolor_name(self):
		for i, c, c_a, v, v_a in self.iter():
			self.assertEqual(str(i), c.name)
			self.assertRegexpMatches(c_a.name, f"{str(i)}!\d{{1,3}}")

	def test_add_alpha(self):
		for i, c, c_a, v, v_a in self.iter():
			self.assertTupleEqual(c_a.value, c.add_alpha(v_a[4]).value)
			self.assertTupleEqual(c_a.value, c_a.add_alpha(v_a[4]).value)

	def test_remove_alpha(self):
		for i, c, c_a, v, v_a in self.iter():
			self.assertTupleEqual(c.value, c.remove_alpha().value)
			self.assertTupleEqual(c.value, c_a.remove_alpha().value)

	def test_len(self):
		for i, c, c_a, v, v_a in self.iter():
			self.assertEqual(3, len(c))
			self.assertEqual(4, len(c_a))

	def test_eq(self):
		self.assertTrue(TikZColor("abc", (0, 0, 0), "RGB") == TikZColor("abc", (200, 100, 25), "RGB"))
		self.assertTrue(TikZColor("abc_123", (0.2, 0.2, 0.2), "rgb") == TikZColor("abc_123", (200, 100, 25), "RGB"))
		self.assertFalse(TikZColor("abc", (0, 0, 0), "RGB") == TikZColor("abc4", (0, 0, 0), "RGB"))
		self.assertFalse(TikZColor("abc_123", (0.2, 0.2, 0.2), "rgb") == TikZColor("bbc_123", (0.2, 0.2, 0.2), "rgb"))

	def test_arithmetic(self):
		for op_r, op_c in ((lambda a, b: a + b, TikZColor.__add__), (lambda a, b: a - b, TikZColor.__sub__),
						   (lambda a, b: a * b, TikZColor.__mul__)):
			with self.subTest(operator=op_r.__name__):
				for i, c, c_a, v, v_a in self.iter():
					op_r_c, op_r_c_a = None, None
					if c.mode == "rgb":
						op_r_c = lambda a, b: min(1, max(0, op_r(a, b)))
					elif c.mode == "RGB":
						op_r_c = lambda a, b: int(min(255, max(0, op_r(a, b))))
					if c_a.mode == "rgb":
						op_r_c_a = lambda a, b: min(1, max(0, op_r(a, b)))
					elif c_a.mode == "RGB":
						op_r_c_a = lambda a, b: int(min(255, max(0, op_r(a, b))))
					for x in ((1, 1, -1, 1), (0.2, 1, 0.1, 0.5), (20, 40, -150, 53), (-0.5, -0.1, 0.05, 1),
							  (0, 0, 0, 0), (0.0, 0.0, 0.0, 0.0), (-1000, -10000.2, -1000, -1000)):
						new_v = (op_r_c(v[1], x[0]), op_r_c(v[2], x[1]), op_r_c(v[3], x[2]))
						self.assertTupleEqual(new_v, op_c(c, x[:3]).value)
						new_v_a = (op_r_c_a(v_a[1], x[0]), op_r_c_a(v_a[2], x[1]),
								   op_r_c_a(v_a[3], x[2]), op_r_c_a(v_a[4], x[3]))
						self.assertTupleEqual(new_v_a, op_c(c_a, x).value)
