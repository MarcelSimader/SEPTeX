"""
:Author: Marcel Simader
:Date: 11.07.2021

.. versionadded:: v0.1.0
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ IMPORTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from __future__ import annotations

import abc
from enum import Enum
from numbers import Number
from typing import Union, AnyStr, Optional, Tuple, Final, Dict, Iterator, Mapping, \
	Any, NoReturn, TypeVar, Callable, Sequence, Literal, Generic, Collection, List

from SEPModules.SEPPrinting import repr_string

from SEPTeX.LaTeX import LaTeXDocument, LaTeXEnvironment
from SEPTeX.TeXBase import TeXHandler

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ GLOBALS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

T: Final = TypeVar("T", bound=Number)
""" Constrained type variable for the :py:mod:`TikZStyle` module. The type of this variable must be a number. """

TIKZ_VALUE: Final = Union[AnyStr, int, float]
""" Type alias for a TikZ key value. """

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ ABSTRACT CLASSES ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TikZWriteable(abc.ABC):
	"""
	Abstract base class for all TikZ objects which can be written to a :py:class:`.TeXHandler`. This class requires all
	subclasses to implement the :py:meth:`__str__` method, because this method will be called when writing this instance
	to a handler.

	:param required_packages: a collection of the names of the packages which are required to use a subclass of this class
	:param required_tikz_libraries: a collection of the names of the TikZ libraries which are required to use a subclass
		of this class
	"""

	def __init__(self,
				 required_packages: Collection[AnyStr],
				 required_tikz_libraries: Collection[AnyStr]):
		self._required_packages: List[AnyStr] = list(required_packages)
		self._required_tikz_libraries: List[AnyStr] = list(required_tikz_libraries)

	def __register_required_package__(self, *package: AnyStr) -> None:
		""" Register one or multiple required packages with this instance. """
		self._required_packages.extend(package)

	def __register_required_tikz_library__(self, *library: AnyStr) -> None:
		""" Register one or multiple required TikZ libraries with this instance. """
		self._required_tikz_libraries.extend(library)

	@property
	def required_packages(self) -> Collection[AnyStr]:
		""" :return: the packages required to use this class in a document """
		return tuple(self._required_packages)

	@property
	def required_tikz_libraries(self) -> Collection[AnyStr]:
		""" :return: the TikZ libraries required to use this class in a document """
		return tuple(self._required_tikz_libraries)

	@abc.abstractmethod
	def __str__(self) -> str:
		""" DOCS add abstract docs """
		raise NotImplementedError("Subclasses of TikZWriteable must implement this method")

class TikZNamed(TikZWriteable, abc.ABC):
	"""
	DOCS write docs for TikZNamed
	"""

	def __init__(self,
				 required_packages: Collection[AnyStr],
				 required_tikz_libraries: Collection[AnyStr]):
		super(TikZNamed, self).__init__(required_packages, required_tikz_libraries)

	@property
	@abc.abstractmethod
	def name(self) -> str:
		raise NotImplementedError("Subclasses of TikZNamed must implement this method")

	@property
	@abc.abstractmethod
	def definition(self) -> str:
		raise NotImplementedError("Subclasses of TikZNamed must implement this method")

	@abc.abstractmethod
	def __hash__(self) -> int:
		raise NotImplementedError("Subclasses of TikZNamed must implement this method")

	@abc.abstractmethod
	def __eq__(self, other) -> bool:
		raise NotImplementedError("Subclasses of TikZNamed must implement this method")

	@abc.abstractmethod
	def __str__(self) -> str:
		raise NotImplementedError("Subclasses of TikZWriteable must implement this method")

TN: Final = TypeVar("TN", bound=TikZNamed)
""" The type variable used to mark an object as being at least :py:class:`TikZWriteable`. """

class TikZDefinesNamed(TikZWriteable, Generic[TN], abc.ABC):
	"""
	Abstract base class for marking a subclass as using :py:class:`TikZNamed` objects in an ordered definition list. Each
	object registered with an instance of this class must be associated with a name and subclass the :py:class:`TikZNamed`
	class.

	This class must be inherited from in order for the :py:class:`TikZPicture` class to be able to register and define
	the named objects stored within it and draw the instance.

	..	warning::

		This class internally stores each registered named object as a dictionary, so the objects will be compared using
		the ``__eq__`` and ``__hash__`` methods. Only the least recently registered object is kept, if two objects of the
		same type and same name are registered.

	:param required_packages: a collection of the names of the packages which are required to use a subclass of this class
	:param required_tikz_libraries: a collection of the names of the TikZ libraries which are required to use a subclass
		of this class
	:param named_objs: the (at least) :py:class:`TikZWriteable` objects to be attached to the instance of this class
	"""

	def __init__(self,
				 required_packages: Collection[AnyStr],
				 required_tikz_libraries: Collection[AnyStr],
				 styles: Collection[TikZStyle],
				 named_objs: Collection[TN]):
		super(TikZDefinesNamed, self).__init__(required_packages, required_tikz_libraries)

		# dict to remove duplicates
		self._named_objs: Dict[Union[TikZColor, TN], None] = dict()
		self.__register_named_object__(*named_objs)

		# register styles
		for style in styles:
			self.__register_named_object__(*style.colors)

	def __register_named_object__(self, *named_obj: Union[TikZColor, TN]) -> None:
		""" Register one or multiple required :py:class:`TikZNamed` instances with this instance. """
		self._named_objs.update({n: None for n in named_obj})

	@property
	def required_named_objects(self) -> Tuple[Union[TikZColor, TN]]:
		""" :return: the uniquely-named required :py:class:`TikZNamed` objects used by this instance """
		return tuple(self._named_objs.keys())

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ STYLES ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TikZColor(TikZNamed, Generic[T]):
	r"""
	:py:class:`TikZColor` represents an RGB color definition. Each color has a name, either 3 or 4 values and a mode. These
	color instances need to be registered with the TikZPicture instance before they can be used. Multiple colors can share
	the same name but they will be overridden by one another, with the color registered at the most recent time being the
	used version.

	The mode can be one of two values:
		* ``rgb`` for int or float values in the interval [0;1], or
		* ``RGB`` for int values in the interval [0;255]

	Colors of length 3 represent ``RED``, ``GREEN`` and ``BLUE``, while colors with length 4 add an addition ``ALPHA``
	channel at the end.

	Comparisons of two colors will compare the names of each color.

	Various arithmetic operations are implemented for this class. The following syntax is used for all binary arithmetic
	operations (the same also applies for the right-handed arithmetic operations, but in reverse):

	..	math:: \circ \in \left\{ +, -, *, /, //, \%, ** \right\}

	..	math::
		\text{color} \circ \lambda &:\Longleftrightarrow
		\left( \text{r} \circ \lambda, \text{g} \circ \lambda, \text{b} \circ \lambda[, \text{a} \circ \lambda] \right) \\
		\text{color} \circ (x, y, z[, w]) &:\Longleftrightarrow
		\left( \text{r} \circ x, \text{g} \circ y, \text{b} \circ z[, \text{a} \circ w]\right) \\
		\text{color1} \circ \text{color2} &:\Longleftrightarrow
		\text{color1} \circ \left(\text{r}, \text{g}, \text{b}[, \text{a}]\right)_{\text{color2}}

	:param name: the name to register this color instance under
	:param value: the ``RGB[A]`` value of this color
	:param mode: the mode of representing the color
	:param generate_unique_name: keyword-only argument that indicates whether or not the class should automatically
		try to make colors unique by adding parts of the hash to the end of the name, this exists mainly to make arithmetic
		operations on colors easier to handle

	:raise ValueError: if the ``value`` tuple is neither 3 nor 4 values long, or the types of the tuple do not match the
		constraints given by ``mode``
	:raise NotImplementedError: if ``mode`` is not one of the listed literals
	"""

	COLOR_VALUE = Union[Tuple[T, T, T], Tuple[T, T, T, T]]
	""" Shorthand for a tuple of either 3 or 4 :py:attr:`T`. """

	def __init__(self,
				 name: AnyStr,
				 value: COLOR_VALUE,
				 mode: Literal["rgb", "RGB"] = "rgb",
				 *,
				 generate_unique_name: bool = False):
		super(TikZColor, self).__init__(("xcolor",), ())

		# check constraints
		if mode not in ("rgb", "RGB"):
			raise NotImplementedError(f"Mode {repr(mode)} is not known, choose from: rgb, and RGB")

		self._value = value
		self._mode = mode
		self._generate_unique_name = generate_unique_name
		self.__validate_color_value__(value)

		self._name = str(name)
		if self._generate_unique_name:
			self._name = self._name + f"_{abs(hash(self._value))}"[:11]

	@staticmethod
	def __not_implemented__() -> NotImplementedError:
		return NotImplementedError("This operation is not supported")

	def __validate_color_value__(self, value: COLOR_VALUE) -> None:
		"""
		Asserts that the input value is either of length 3 or 4, and that the types of all values match the constraints
		of the color mode.
		"""
		if not (len(value) == 3 or len(value) == 4):
			raise ValueError(f"Color value tuple must contain either 3 or 4 values, received {len(value)}")
		type_names = [type(e).__name__ for e in value]
		# check mode adherence
		if self._mode == "rgb" and not all([isinstance(v, (int, float)) for v in value]):
			raise ValueError(f"All color values for mode 'rgb' must be of type int or float, but received {type_names}")
		elif self._mode == "RGB" and not all([isinstance(v, int) for v in value]):
			raise ValueError(f"All color values for mode 'RGB' must be of type int, but received {type_names}")

	@property
	def name(self) -> str:
		""" :return: the name, different from :py:meth:`xcolor_name` and :py:meth:`__str__` since this does not include opacity """
		return self._name

	@property
	def definition(self) -> str:
		""" :return: a string containing the ``xcolor`` definition of this color for the preamble of a LaTeX document """
		return f"\\definecolor{{{self._name}}}{{{self._mode}}}{{{self.red}, {self.green}, {self.blue}}}"

	@property
	def xcolor_name(self) -> str:
		""" :return: a string containing the ``xcolor`` name to be used in a LaTeX document, alias for :py:meth:`__str__` """
		return str(self)

	@property
	def value(self) -> COLOR_VALUE:
		return self._value

	@property
	def mode(self) -> str:
		return self._mode

	@property
	def red(self) -> T:
		return self._value[0]

	@property
	def green(self) -> T:
		return self._value[1]

	@property
	def blue(self) -> T:
		return self._value[2]

	@property
	def alpha(self) -> Optional[T]:
		if len(self) <= 3:
			return None
		return self._value[3]

	def add_alpha(self, value: T) -> TikZColor:
		"""
		Adds an alpha channel at opacity ``value`` to this color.

		:param value: the value of the new alpha channel

		:return: the new color with 4 channels, if the color already has 4 channels this function will return the
			original color
		"""
		if not len(self) >= 4:
			new_values = (self.red, self.green, self.blue, value)
			# check if input is legal
			self.__validate_color_value__(new_values)
			# return new color
			return TikZColor(self._name,
							 new_values,
							 self._mode,
							 generate_unique_name=self._generate_unique_name)
		else:
			return self

	def remove_alpha(self) -> TikZColor:
		"""
		Removes the alpha channel of this color.

		:return: the new color with 3 channels, if the color already had 3 channels this function will return the
			original color
		"""
		if not len(self) <= 3:
			return TikZColor(self._name,
							 (self.red, self.green, self.blue),
							 self._mode,
							 generate_unique_name=self._generate_unique_name)
		else:
			return self

	def __binary_operation__(self, other: Union[T, TikZColor, COLOR_VALUE], operator: Callable[[T, T], T]) -> TikZColor:
		"""
		Applies ``operator`` as binary operator to ``self`` and ``other``. If the other input is not a color, then the
		newly generated color will automatically have ``generate_unique_name`` set to ``True``.

		:param other: the value to use on the right hand side of the operator
		:param operator: the operator to apply to the values

		:return: a new :py:class:`TikzColor` instance holding the result of the operation
		:raise ValueError: if the length of ``other`` is not 1 or does not match the length of ``self``, or if the given
			values in ``other`` are not ints or floats greater than or equal to 0
		"""
		# handle other is color
		if isinstance(other, TikZColor):
			generate_unique_name = self._generate_unique_name or other._generate_unique_name
			other = other._value
		else:
			generate_unique_name = True

		# handle other is number
		if not isinstance(other, Sequence):
			other = (other,)
		if len(other) == 1:
			other = other * len(self)
		elif len(other) != len(self):
			raise ValueError(
					f"Other value of binary operator must be a tuple of the same length as {repr(self)} ({len(self)}), "
					f"but received length {len(other)}")
		if not all([isinstance(v, (int, float)) and v >= 0 for v in other]):
			raise ValueError(
					f"All values of other must be a float greater than or equal to 0 but received {other} of types "
					f"{[o.__class__.__name__ for o in other]}")

		# convert to int if needed
		if self._mode == "RGB":
			_operator = lambda a, b: min(max(int(operator(a, b)), 0), 255)
		elif self._mode == "rgb":
			_operator = lambda a, b: min(max(operator(a, b), 0), 1)
		else:
			raise self.__not_implemented__()

		# compute operation and return color
		if len(self) <= 3:
			return TikZColor(self._name,
							 (_operator(self._value[0], other[0]), _operator(self._value[1], other[1]),
							  _operator(self._value[2], other[2])),
							 self._mode,
							 generate_unique_name=generate_unique_name)
		elif len(self) == 4:
			return TikZColor(self._name,
							 (_operator(self._value[0], other[0]), _operator(self._value[1], other[1]),
							  _operator(self._value[2], other[2]), _operator(self._value[3], other[3])),
							 self._mode,
							 generate_unique_name=generate_unique_name)
		else:
			raise self.__not_implemented__()

	# arithmetic operations
	def __add__(self, other: Union[T, TikZColor, COLOR_VALUE]) -> TikZColor:
		return self.__binary_operation__(other, lambda a, b: a + b)

	def __sub__(self, other: Union[T, TikZColor, COLOR_VALUE]) -> TikZColor:
		return self.__binary_operation__(other, lambda a, b: a - b)

	def __mul__(self, other: Union[T, TikZColor, COLOR_VALUE]) -> TikZColor:
		return self.__binary_operation__(other, lambda a, b: a * b)

	def __truediv__(self, other: Union[T, TikZColor, COLOR_VALUE]) -> TikZColor:
		return self.__binary_operation__(other, lambda a, b: a / b)

	def __floordiv__(self, other: Union[T, TikZColor, COLOR_VALUE]) -> TikZColor:
		return self.__binary_operation__(other, lambda a, b: a // b)

	def __mod__(self, other: Union[T, TikZColor, COLOR_VALUE]) -> TikZColor:
		return self.__binary_operation__(other, lambda a, b: a % b)

	def __pow__(self, power: Union[T, TikZColor, COLOR_VALUE]) -> TikZColor:
		return self.__binary_operation__(power, lambda a, b: a ** b)

	# "right" arithmetic operations
	def __radd__(self, other: Union[T, TikZColor, COLOR_VALUE]) -> TikZColor:
		return self.__binary_operation__(other, lambda a, b: b + a)

	def __rsub__(self, other: Union[T, TikZColor, COLOR_VALUE]) -> TikZColor:
		return self.__binary_operation__(other, lambda a, b: b - a)

	def __rmul__(self, other: Union[T, TikZColor, COLOR_VALUE]) -> TikZColor:
		return self.__binary_operation__(other, lambda a, b: b * a)

	def __rtruediv__(self, other: Union[T, TikZColor, COLOR_VALUE]) -> TikZColor:
		return self.__binary_operation__(other, lambda a, b: b / a)

	def __rfloordiv__(self, other: Union[T, TikZColor, COLOR_VALUE]) -> TikZColor:
		return self.__binary_operation__(other, lambda a, b: b // a)

	def __rmod__(self, other: Union[T, TikZColor, COLOR_VALUE]) -> TikZColor:
		return self.__binary_operation__(other, lambda a, b: b % a)

	def __rpow__(self, other: Union[T, TikZColor, COLOR_VALUE]) -> TikZColor:
		return self.__binary_operation__(other, lambda a, b: b ** a)

	def __hash__(self) -> int:
		return hash(self._name)

	def __eq__(self, other: Any) -> bool:
		return isinstance(other, TikZColor) and self._name == other._name

	def __ne__(self, other: Any) -> bool:
		return not isinstance(other, TikZColor) or self._name != other._name

	def __len__(self) -> int:
		return len(self._value)

	def __str__(self) -> str:
		if len(self) >= 4:
			if self._mode == "rgb":
				alpha = self.alpha
			elif self._mode == "RGB":
				alpha = self.alpha / 255
			else:
				raise self.__not_implemented__()
			return f"{self._name}!{round(alpha * 100, ndigits=None)}"
		else:
			return self._name

	def __repr__(self) -> str:
		return repr_string(self, TikZColor.name, TikZColor.value, TikZColor.mode)

	# ~~~~~~~~~~~~~~~ DEFAULT COLORS ~~~~~~~~~~~~~~~

	@classmethod
	def __set_default_colors__(cls) -> None:
		""" This function initializes the default or resets colors. """
		cls.WHITE = TikZColor("WHITE", (255, 255, 255, 255), "RGB")
		cls.ALMOST_WHITE = TikZColor("ALMOST_WHITE", (245, 245, 245, 255), "RGB")
		cls.LIGHT_GRAY = TikZColor("LIGHT_GRAY", (180, 180, 180, 255), "RGB")
		cls.DARK_GRAY = TikZColor("DARK_GRAY", (45, 45, 45, 255), "RGB")
		cls.ALMOST_BLACK = TikZColor("ALMOST_BLACK", (18, 18, 18, 255), "RGB")
		cls.BLACK = TikZColor("BLACK", (0, 0, 0, 255), "RGB")
		cls.RED = TikZColor("RED", (252, 68, 68, 255), "RGB")
		cls.ORANGE = TikZColor("ORANGE", (255, 165, 0, 255), "RGB")
		cls.YELLOW = TikZColor("YELLOW", (251, 219, 4, 255), "RGB")
		cls.GREEN = TikZColor("GREEN", (139, 195, 74, 255), "RGB")
		cls.LIGHT_BLUE = TikZColor("LIGHT_BLUE", (3, 169, 244, 255), "RGB")
		cls.DARK_BLUE = TikZColor("DARK_BLUE", (4, 60, 140, 255), "RGB")
		cls.PURPLE = TikZColor("PURPLE", (103, 58, 183, 255), "RGB")
		cls.MAGENTA = TikZColor("MAGENTA", (156, 39, 176, 255), "RGB")
		cls.PINK = TikZColor("PINK", (236, 76, 140, 255), "RGB")
		cls.ROSE = TikZColor("ROSE", (252, 140, 132, 255), "RGB")
		cls.DEFAULT_COLORS = (
				cls.WHITE, cls.ALMOST_WHITE, cls.LIGHT_GRAY, cls.DARK_GRAY, cls.ALMOST_BLACK,
				cls.BLACK, cls.RED, cls.ORANGE, cls.YELLOW, cls.GREEN, cls.LIGHT_BLUE, cls.DARK_BLUE,
				cls.PURPLE, cls.MAGENTA, cls.PINK, cls.ROSE)

	WHITE: TikZColor[int]
	ALMOST_WHITE: TikZColor[int]
	LIGHT_GRAY: TikZColor[int]
	DARK_GRAY: TikZColor[int]
	ALMOST_BLACK: TikZColor[int]
	BLACK: TikZColor[int]
	RED: TikZColor[int]
	ORANGE: TikZColor[int]
	YELLOW: TikZColor[int]
	GREEN: TikZColor[int]
	LIGHT_BLUE: TikZColor[int]
	DARK_BLUE: TikZColor[int]
	PURPLE: TikZColor[int]
	MAGENTA: TikZColor[int]
	PINK: TikZColor[int]
	ROSE: TikZColor[int]
	DEFAULT_COLORS: Tuple[TikZColor[int], ...]

TikZColor.__set_default_colors__()

class _TikZArrow(Enum):
	"""
	:py:class:`_TikZArrow` is the baseclass enumeration for holding TikZ arrow head type data.

	:param key: the TikZ key for this arrow head type (e.g. ``->``)
	"""

	def _generate_next_value_(name, start, count, last_values) -> int:
		if last_values is None:
			return 0
		else:
			return last_values + 1

	def __init__(self, key: str):
		super(_TikZArrow, self).__init__()
		# check types
		if not isinstance(key, str):
			raise TypeError(f"TikZArrow enum entries must be of shape 'TikZ value key' with type 'str', "
							f"found type {key.__class__.__name__}")
		self._name = self._name_
		self._key = key

	@property
	def name(self):
		""" :return: the name of this enum object """
		return self._name

	@property
	def key(self) -> str:
		""" :return: the TikZ key for this arrow head type """
		return self._key

	def __repr__(self) -> str:
		return repr_string(self, _TikZArrow.key)

class TikZArrow(_TikZArrow):
	"""
	:py:class:`TikZArrow` is an enumeration of TikZ arrow head types.
	"""

	LINE: Final = "-"

	LEFT: Final = "<-"
	RIGHT: Final = "->"
	LEFT_RIGHT: Final = "<->"
	IN_LEFT: Final = ">-"
	IN_RIGHT: Final = "-<"
	IN_LEFT_RIGHT: Final = ">-<"

	LEFT_STUMP: Final = "|-"
	RIGHT_STUMP: Final = "-|"
	LEFT_RIGHT_STUMP: Final = "|-|"

	LEFT_LATEX: Final = "latex-"
	RIGHT_LATEX: Final = "-latex"
	LEFT_RIGHT_LATEX: Final = "latex-latex"
	LEFT_LATEX_PRIME: Final = "latex'-"
	RIGHT_LATEX_PRIME: Final = "-latex'"
	LEFT_RIGHT_LATEX_PRIME: Final = "latex'-latex'"

	LEFT_CIRC: Final = "o-"
	RIGHT_CIRC: Final = "-o"
	LEFT_RIGHT_CIRC: Final = "o-o"

class TikZStyle:
	r"""
	:py:class:`TikZStyle` holds information about what styles to apply to a TikZ object. This class implements a container,
	and the :py:meth:`__getitem__` and :py:meth:`__getattr__` methods. A style can be accessed in the following ways:

	>>> scale_style = TikZStyle(x_scale="2cm")
	>>> assert scale_style.x_scale == "2cm"
	>>> assert scale_style["x_scale"] == "2cm"
	>>> assert scale_style["x scale"] == "2cm"
	>>> assert scale_style["x-scale"] == "2cm"
	>>> assert scale_style.style["x scale"] == "2cm" # space is needed here! this use is discouraged

	Additionally, some methods of this instance will ignore ``None`` values:

	>>> draw_style = TikZStyle(draw=True)
	>>> assert len(draw_style) == 1 # all other values are None
	>>> assert "y_scale" not in draw_style
	>>> assert "draw" in draw_style

	One can either iterate over the non-None values of this instance, or call the :py:meth:`__str__` method:

	>>> multiple_style = TikZStyle(width="1cm", draw=True)
	>>> for s in multiple_style:
	...		print(s)
	('width', '1cm')
	('draw', True)
	>>> print(str(multiple_style))
	draw, width={1cm}

	Style objects can be compared using ``==`` and ``!=``, and test equal if and only if they have matching key value
	pairs in :py:attr:`style` (i.e. the values passed to the constructor).

	>>> assert TikZStyle(dashed=True, line_width="2mm") == TikZStyle(dashed=True, line_width="2mm")
	>>> assert TikZStyle(dashed=True) != TikZStyle()

	:param custom_entries: an optional mapping of any entries not included in the keyword arguments
	"""

	DICT_VAL: Final = Optional[Union[AnyStr, bool, int, float]]
	""" The types of a dictionary entry of the styles dictionary. """

	# This tuple is purely used to define the style properties so that IDEs and other tools can find and suggest them
	__slots__ = ("width", "height", "x_scale", "y_scale", "scale", "shift", "draw", "dashed", "dotted", "line_width",
				 "color", "fill", "draw_opacity", "fill_opacity", "bend_left", "bend_right", "circle", "align",
				 "rectangle",
				 "__dict__")

	def __init__(self,
				 custom_entries: Optional[Mapping[AnyStr, DICT_VAL]] = None,
				 *,
				 width: Optional[TIKZ_VALUE] = None,
				 height: Optional[TIKZ_VALUE] = None,
				 x_scale: Optional[TIKZ_VALUE] = None,
				 y_scale: Optional[TIKZ_VALUE] = None,
				 scale: Optional[TIKZ_VALUE] = None,
				 shift: Optional[Tuple[TIKZ_VALUE, TIKZ_VALUE]] = None,

				 bend_left: Optional[Union[bool, TIKZ_VALUE]] = None,
				 bend_right: Optional[Union[bool, TIKZ_VALUE]] = None,

				 draw: bool = True,
				 circle: Optional[bool] = None,
				 rectangle: Optional[bool] = None,

				 dashed: Optional[bool] = None,
				 dotted: Optional[bool] = None,
				 line_width: Optional[TIKZ_VALUE] = None,
				 color: Optional[TikZColor] = None,
				 fill: Optional[TikZColor] = None,

				 align: Optional[AnyStr] = None,

				 draw_opacity: Optional[float] = None,
				 fill_opacity: Optional[float] = None):
		if draw is None:
			raise ValueError("'draw style cannot be set to None")

		# register styles
		self._style = {
				"width"       : width,
				"height"      : height,
				"x scale"     : x_scale,
				"y scale"     : y_scale,
				"scale"       : scale,
				"shift"       : None if shift is None else f"({shift[0]}, {shift[1]})",

				"bend left"   : bend_left,
				"bend right"  : bend_right,

				"draw"        : draw,
				"circle"      : circle,
				"rectangle"   : rectangle,

				"dashed"      : dashed,
				"dotted"      : dotted,
				"line width"  : line_width,
				"color"       : color,
				"fill"        : fill,

				"align"       : align,

				"draw opacity": draw_opacity,
				"fill opacity": fill_opacity
				}

		# extend registered styles with custom styles
		if custom_entries is not None:
			self._style.update(custom_entries)

		# register all used colors
		self._colors = (color, fill)

	@staticmethod
	def normalize_key(s: str) -> str:
		""" Removes any underscores or hyphens and replaces them with spaces. """
		return s.replace("_", " ").replace("-", " ")

	@property
	def style(self) -> Dict[AnyStr, DICT_VAL]:
		""" :return: a copy of the styles stored in this instance """
		return dict(self._style)

	@property
	def colors(self) -> Tuple[TikZColor]:
		""" :return: a copy of the unique colors used in this instance, removes ``None`` values """
		# dict to remove duplicates
		return tuple(dict.fromkeys([x for x in self._colors if x is not None]).keys())

	@property
	def empty(self) -> bool:
		""" :return: whether or not this style instance has no properties (aside from the ``draw`` flag) set """
		return len(self) <= 1

	def __and__(self, other: TikZStyle) -> TikZStyle:
		sty1 = set(self.__iter__())
		sty2 = set(other.__iter__())
		return TikZStyle(dict(sty2.union(sty1)))

	def __or__(self, other: TikZStyle) -> TikZStyle:
		return self.__and__(other)

	def __add__(self, other: TikZStyle) -> TikZStyle:
		return self.__and__(other)

	def __len__(self) -> int:
		_len = 0
		for s in self._style.values():
			if s is None: continue
			_len += 1
		return _len

	def __contains__(self, item) -> bool:
		key = self.normalize_key(str(item))
		return key in self._style and self._style[key] is not None

	def __iter__(self) -> Iterator[Tuple[str, DICT_VAL]]:
		for key, value in self._style.items():
			if value is not None:
				yield key, value

	def __setitem__(self, key, value) -> NoReturn:
		raise SyntaxError(f"Cannot assign to attribute {key} of TikZStyle, this class is immutable")

	def __getitem__(self, item) -> DICT_VAL:
		return self._style[self.normalize_key(str(item))]

	def __getattr__(self, item) -> Any:
		s_item = self.normalize_key(str(item))
		if s_item in self._style:
			# get style
			return self._style[s_item]

	def __hash__(self) -> int:
		return hash(frozenset(self._style.items()))

	def __eq__(self, other: Any) -> bool:
		return isinstance(other, TikZStyle) and self._style == other._style

	def __ne__(self, other: Any) -> bool:
		return not isinstance(other, TikZStyle) or self._style != other._style

	def __str__(self) -> str:
		out_string = str()

		# empty string without brackets
		if len(self) <= 0:
			return out_string

		# process normal items and flags (bool) separately
		style_strings = [f"{key}={{{value}}}" for key, value in self if not isinstance(value, bool)]
		style_flags = [f"{key}" for key, value in self if isinstance(value, bool) and value]

		return ", ".join(style_flags + style_strings)

	def __repr__(self) -> str:
		return f"TikZStyle({', '.join([f'{key}={value}' for key, value in self])})"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ ENVIRONMENTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TikZPicture(LaTeXEnvironment):
	r"""
	:py:class:`TikZPicture` represents the standard TikZ ``tikzpicture`` environment. This class aids in registering
	:py:class:`TikZNamed` objects and writing special composite objects.

	..	warning::

		When a :py:class:`TikZNamed` object is written to this class, its :py:attr:`TikZNamed.definition` string will be
		directly written to the document without registering it, or checking if the node has been written to this instance
		before. However, when a :py:class:`TikZDefinesNamed` object is written to this class, all the registered
		:py:class:`TikZNamed` objects will be recursively written and registered, so that they can be reused without
		overwriting the old definitions. If one desires to redefine them anyway, one can write them directly to the
		instance manually or simply rename the objects to cause a new definition to be registered.

	..	note::

		Registered :py:class:`TikZNamed` objects are implicitly inherited to :py:class:`TikZScope` environments defined
		with this class as parent.

	:param parent_env: the parent environment or document to this environment
	:param style: the main style to use for this environment
	:param defined_colors: any colors which have already been defined in the document and are accessible from within this
		environment, this option is useful if there are manually defined colors in the document
	:param indent_level: the number of tab characters to indent this environment relative to the parent environment
	"""

	def __init__(self,
				 parent_env: Union[LaTeXDocument, LaTeXEnvironment],
				 style: TikZStyle = TikZStyle(),
				 defined_colors: Collection[TikZColor] = (),
				 indent_level: int = 1):
		super(TikZPicture, self).__init__(parent_env,
										  environment_name="tikzpicture",
										  options=str(style),
										  required_packages=("tikz",),
										  indent_level=indent_level)

		self.__tikz_init__(style, defined_colors, indent_level)

	def __tikz_init__(self, style: TikZStyle, defined_named_objs: Collection[TikZNamed],
					  indent_level: int):
		""" Initialize this environment. This function should be called by subclasses which do not call the super constructor. """
		self._defined_named_objects: List[TikZNamed] = list(defined_named_objs)
		self._definition_handler = TeXHandler(indent_level)
		self.define_named_object(*style.colors)

	@property
	def defined_named_objects(self) -> Tuple[TikZNamed]:
		""" :return: the :py:class:`TikZNamed` objects which have so far been defined by this environment """
		return tuple(self._defined_named_objects)

	def define_named_object(self, *obj: TikZNamed) -> None:
		"""
		Register one or multiple :py:class:`TikZNamed` objects with this instance. This will define the objects at the
		beginning of the environment.

		:param obj: the named object or objects to define
		"""
		for o in obj:
			if o not in self._defined_named_objects:
				# possibly recurse
				if isinstance(o, TikZDefinesNamed):
					self.define_named_object(*o.required_named_objects)

				# register packages
				self.document.use_package(*o.required_packages)
				# register tikz libraries
				self.document.use_tikz_library(*o.required_tikz_libraries)
				# define in this instance
				self._definition_handler.write(o.definition)
				self._defined_named_objects.append(o)

	def write(self, s: Union[TikZWriteable, AnyStr]) -> None:
		"""
		Write ``s`` to the handler of this instance.

		The following conditions apply to special object types:

			-	If ``s`` is a string this method will simply write it.

			-	If ``s`` is a :py:class:`TikZWriteable` object this method will first register the required packages, then
			 	the required TikZ libraries, then call the ``__str__`` method of the object, and finally add ``;`` to the
			 	end if it is missing.

				-	If ``s`` is also a :py:class:`TikZDefinesNamed` object this method will additionally register all the
					named objects recursively, if it has not been defined with the same type and name in this instance before.

		:param s: the object to write to the handler
		"""
		if isinstance(s, TikZWriteable):
			# register packages
			self.document.use_package(*s.required_packages)
			# register tikz libraries
			self.document.use_tikz_library(*s.required_tikz_libraries)

			# register defined named objs
			if isinstance(s, TikZDefinesNamed):
				self.define_named_object(*s.required_named_objects)

			# get definition if s is named obj or just string
			if isinstance(s, TikZNamed):
				s = s.definition
			else:
				s = str(s)

			if not s.endswith(";"):
				s += ";"

		super(TikZPicture, self).write(s)

	def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
		# write color handler to parent
		if len(self._definition_handler) > 0:
			self.parent_handler.write(self._definition_handler)
		# super call
		return super(TikZPicture, self).__exit__(exc_type, exc_val, exc_tb)

class TikZScope(TikZPicture):
	"""
	:py:class:`TikZScope` represents the standard TikZ ``scope`` environment. It can only be instantiated with a parent
	environment inheriting from :py:class:`TikZPicture`. This environment will automatically include all :py:class:`TikZNamed`
	objects registered by the parent environment in its namespace.

	:param parent_env: the parent environment or document to this environment
	:param style: the main style to use for this environment
	:param indent_level: the number of tab characters to indent this environment relative to the parent environment

	:raise TypeError: if the passed ``parent_env`` is not an instance of a :py:class:`TikZPicture` class or subclass thereof
	"""

	def __init__(self,
				 parent_env: TikZPicture,
				 style: TikZStyle = TikZStyle(),
				 indent_level: int = 1):
		# make sure we are in a tikz picture env
		if not isinstance(parent_env, TikZPicture):
			raise TypeError(f"TikZScope must be nested within the context manager of a TikZPicture environment or a "
							f"subclass of it, but received {parent_env.__class__.__name__}")

		super(TikZPicture, self).__init__(parent_env,
										  environment_name="scope",
										  options=str(style),
										  required_packages=("tikz",),
										  indent_level=indent_level)
		self.__tikz_init__(style, parent_env.defined_named_objects, indent_level)
