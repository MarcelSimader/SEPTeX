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
	Any, NoReturn, TypeVar, Callable, Sequence, Literal, Generic, Collection, List, final

from SEPModules.SEPPrinting import repr_string

from SEPTeX.LaTeX import LaTeXDocument, LaTeXEnvironment
from SEPTeX.TeXBase import TeXHandler

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ GLOBALS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_N: Final = TypeVar("_N", bound=Number)
""" Constrained type variable for the :py:mod:`TikZStyle` module. The type of this variable must be a number. """

TikZValue: Final = Union[AnyStr, int, float]
""" Type alias for a TikZ key value. """

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ ABSTRACT CLASSES ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TikZWriteable(abc.ABC):
	"""
	Abstract base class for all TikZ objects which can be written to a :py:class:`.TeXHandler`. This class requires all
	subclasses to implement the :py:meth:`to_tikz`, :py:meth:`__hash__`, and :py:meth:`__eq__` methods. The latter two
	are required in order to store these objects in sets and dictionaries. :py:class:`TikZWriteable` objects should only
	compare equal if they are semantically equal.

	The method :py:meth:`__str__` is final and calls the abstract method :py:meth:`to_tikz`.

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
		""" Registers one or multiple required packages with this instance. """
		self._required_packages.extend(package)

	def __register_required_tikz_library__(self, *library: AnyStr) -> None:
		""" Registers one or multiple required TikZ libraries with this instance. """
		self._required_tikz_libraries.extend(library)

	@property
	def required_packages(self) -> Tuple[AnyStr]:
		""" :return: the packages required to use this class in a document """
		return tuple(self._required_packages)

	@property
	def required_tikz_libraries(self) -> Tuple[AnyStr]:
		""" :return: the TikZ libraries required to use this class in a document """
		return tuple(self._required_tikz_libraries)

	@abc.abstractmethod
	def to_tikz(self) -> str:
		""" Converts this object to a TikZ string. """
		raise NotImplementedError("Subclasses of TikZWriteable must implement this method")

	@abc.abstractmethod
	def __hash__(self) -> int:
		raise NotImplementedError("Subclasses of TikZWriteable must implement this method")

	@abc.abstractmethod
	def __eq__(self, other) -> bool:
		raise NotImplementedError("Subclasses of TikZWriteable must implement this method")

	@final
	def __str__(self) -> str:
		return self.to_tikz()

class TikZNamed(TikZWriteable, abc.ABC):
	"""
	Abstract base class for a :py:class:`TikZWriteable` object which can be defined in a ``tikzpicture`` and then referenced
	by its name. All subclasses of this class must implement the :py:meth:`name`, and :py:meth:`definition` methods. The
	final methods :py:meth:`__str__`, and :py:meth:`to_tikz` are mapped to the abstract method :py:meth:`name`.

	The final methods :py:meth:`__hash__`, and :py:meth:`__eq__` compare two :py:class:`TikZNamed` objects based solely
	on an instance check and the return value of the abstract method :py:meth:`name`. This means that two TikZNamed objects
	with the same name are treated as being equal, regardless of their semantic contents (as is the case in TikZ itself).

	:param required_packages: a collection of the names of the packages which are required to use a subclass of this class
	:param required_tikz_libraries: a collection of the names of the TikZ libraries which are required to use a subclass
		of this class
	"""

	def __init__(self,
				 required_packages: Collection[AnyStr],
				 required_tikz_libraries: Collection[AnyStr]):
		super(TikZNamed, self).__init__(required_packages, required_tikz_libraries)

	@property
	@abc.abstractmethod
	def name(self) -> str:
		""" :return: the TikZ name of this object as string """
		raise NotImplementedError("Subclasses of TikZNamed must implement this method")

	@property
	@abc.abstractmethod
	def definition(self) -> str:
		""" :return: the definition string of this object """
		raise NotImplementedError("Subclasses of TikZNamed must implement this method")

	@final
	def __hash__(self) -> int:
		return hash(self.name)

	@final
	def __eq__(self, other) -> bool:
		return isinstance(other, TikZNamed) and self.name == other.name

	@final
	def to_tikz(self) -> str:
		return self.name

_TW: Final = TypeVar("_TW", bound=TikZWriteable)
""" The type variable used to mark an object as being at least :py:class:`TikZWriteable`. """

class TikZDefinesWriteable(TikZWriteable, Generic[_TW], abc.ABC):
	"""
	Abstract base class for marking a subclass as keeping :py:class:`TikZWriteable` objects in an ordered definition set.
	Each object registered with an instance of this class must inherit from :py:class:`TikZWriteable` and (optionally) be
	of the type specified by the generic type variable.

	This class is useful when one desires to build up more complex TikZ objects. For example, the :py:class:`TikZStyle`
	class inherits from ``TikZDefinesWriteable[TikZColor]``, since each TikZ style also stores a number of :py:class:`TikZColor`
	objects, which implement :py:class:`TikZNamed`.

	The handling of these :py:class:`TikZWriteable` object is solved internally in the :py:class:`TikZPicture` class.

	..	warning::

		This class internally stores each registered named object as a dictionary, so the objects will be compared using
		the ``__eq__`` and ``__hash__`` methods. Only the least recently registered object is kept, if two objects of the
		same type and same name are registered. See the documentation of :py:class:`TikZWriteable`, and :py:class:`TikZNamed`
		for details on these methods.

	:param required_packages: a collection of the names of the packages which are required to use a subclass of this class
	:param required_tikz_libraries: a collection of the names of the TikZ libraries which are required to use a subclass
		of this class
	"""

	def __init__(self,
				 required_packages: Collection[AnyStr],
				 required_tikz_libraries: Collection[AnyStr],
				 required_writeable_objs: Collection[_TW]):
		super(TikZDefinesWriteable, self).__init__(required_packages, required_tikz_libraries)

		# dict to remove duplicates
		self._writeable_objs: Dict[_TW, None] = dict()
		# register passed objs
		self.__register_writeable_object__(*required_writeable_objs)

	def __register_writeable_object__(self, *writeable_obj: _TW) -> None:
		""" Register one or multiple :py:class:`TikZWriteable` instances with this instance. """
		for o in writeable_obj:
			# recurse
			if isinstance(o, TikZDefinesWriteable):
				self.__register_writeable_object__(*o.required_named_objects)

			# register and update
			self.__register_required_package__(*o.required_packages)
			self.__register_required_tikz_library__(*o.required_tikz_libraries)
		self._writeable_objs.update(dict.fromkeys(writeable_obj))

	@property
	def required_writeable_objects(self) -> Iterator[_TW]:
		""" :return: the required :py:class:`TikZWriteable` objects used by this instance """
		return (x for x in self._writeable_objs.keys())

	@property
	def required_named_objects(self) -> Iterator[TikZNamed]:
		""" :return: the uniquely-named required :py:class:`TikZNamed` objects used by this instance """
		return (x for x in self._writeable_objs.keys() if isinstance(x, TikZNamed))

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ STYLES ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TikZColor(TikZNamed, Generic[_N]):
	r"""
	:py:class:`TikZColor` represents an RGB color definition. Each color has a name, either 3 or 4 values and a mode. These
	color instances need to be registered with the TikZPicture instance before they can be used. Multiple colors can share
	the same name but they may be overwritten by each another, with the color registered at the most recent time being the
	used version.

	The mode can be one of two values:
		* ``rgb`` for int or float values in the interval [0;1], or
		* ``RGB`` for int values in the interval [0;255]

	Colors of length 3 represent ``RED``, ``GREEN`` and ``BLUE``, while colors with length 4 add an addition ``ALPHA``
	channel at the end.

	Various arithmetic operations are implemented for this class. The following syntax is used for all binary arithmetic
	operations (the same also applies for the right-handed arithmetic operations, but in reverse):

	..	math:: \circ \in \left\{ +, -, *, /, //, \%, ** \right\}

	..	math::
		\text{color} \circ \lambda &:\Longleftrightarrow
		\left( \text{r} \circ \lambda, \text{g} \circ \lambda, \text{b} \circ \lambda[, \text{a} \circ \lambda] \right)

		\text{color} \circ (x, y, z[, w]) &:\Longleftrightarrow
		\left( \text{r} \circ x, \text{g} \circ y, \text{b} \circ z[, \text{a} \circ w]\right)

		\text{color1} \circ \text{color2} &:\Longleftrightarrow
		\text{color1} \circ \left(\text{r}, \text{g}, \text{b}[, \text{a}]\right)_{\text{color2}}

	:param name: the name to register this color instance under
	:param value: the ``RGB[A]`` value of this color
	:param mode: the mode of representing the color
	:param generate_unique_name: keyword-only argument that indicates whether or not the class should automatically
		try to make colors unique by adding parts of the hash to the end of the name, this exists mainly to make arithmetic
		operations on colors easier to handle TODO make this part of TikZNamed by default

	:raise ValueError: if the ``value`` tuple is neither 3 nor 4 values long, or the types of the tuple do not match the
		constraints given by ``mode``
	:raise NotImplementedError: if ``mode`` is not one of the listed literals
	"""

	ColorTuple: Final = Union[Tuple[_N, _N, _N], Tuple[_N, _N, _N, _N]]
	""" Shorthand for a tuple of either 3 or 4 :py:attr:`T`. """

	def __init__(self,
				 name: AnyStr,
				 value: ColorTuple,
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
	def _not_implemented() -> NotImplementedError:
		return NotImplementedError("This operation is not supported")

	def __validate_color_value__(self, value: ColorTuple) -> None:
		"""
		Asserts that the input value is either of length 3 or 4, and that the types of all values match the constraints
		of the color mode.
		"""
		if not (len(value) == 3 or len(value) == 4):
			raise ValueError(f"Color value tuple must contain either 3 or 4 values, received {len(value)}")
		type_names = [type(e).__name__ for e in value]
		# check mode adherence
		if self._mode == "rgb" and not all([isinstance(v, (int, float)) and 0.0 <= v <= 1.0 for v in value]):
			raise ValueError(f"All color values for mode 'rgb' must be of type int or float and in range [0;1], "
							 f"but received {value} of type {type_names}")
		elif self._mode == "RGB" and not all([isinstance(v, int) and 0 <= v <= 255 for v in value]):
			raise ValueError(f"All color values for mode 'RGB' must be of type int and in range [0;255], "
							 f"but received {value} of type {type_names}")

	@property
	def raw_name(self) -> str:
		""" :return: the raw name, different from :py:meth:`name` since this does not include opacity """
		return self._name

	@property
	def name(self) -> str:
		""" :return: a string containing the full name to be used in a TikZ context """
		if len(self) >= 4:
			if self._mode == "rgb":
				alpha = self.alpha
			elif self._mode == "RGB":
				alpha = self.alpha / 255
			else:
				raise self._not_implemented()
			return f"{self._name}!{round(alpha * 100, ndigits=None)}"
		else:
			return self._name

	@property
	def definition(self) -> str:
		""" :return: a string containing the ``xcolor`` definition of this color for the preamble of a LaTeX document """
		return f"\\definecolor{{{self._name}}}{{{self._mode}}}{{{self.red}, {self.green}, {self.blue}}}"

	@property
	def value(self) -> ColorTuple:
		""" :return: the tuple data of this color """
		return self._value

	@property
	def mode(self) -> str:
		""" :return: the mode of this color """
		return self._mode

	@property
	def red(self) -> _N:
		""" :return: the red channel """
		return self._value[0]

	@property
	def green(self) -> _N:
		""" :return: the green channel """
		return self._value[1]

	@property
	def blue(self) -> _N:
		""" :return: the blue channel """
		return self._value[2]

	@property
	def alpha(self) -> Optional[_N]:
		""" :return: the alpha channel if present or ``None`` """
		if len(self) <= 3:
			return None
		return self._value[3]

	def add_alpha(self, value: _N) -> TikZColor[_N]:
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

	def remove_alpha(self) -> TikZColor[_N]:
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

	def __binary_operation__(self, other: Union[_N, TikZColor, ColorTuple],
							 operator: Callable[[_N, _N], _N]) -> TikZColor[_N]:
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
			raise ValueError(f"Other value of binary operator must be a tuple of the same length as {repr(self)}"
							 f" ({len(self)}), but received length {len(other)}")
		if not all([isinstance(v, (int, float)) for v in other]):
			raise ValueError(f"All values of other must be an int or float but received {other} of types "
							 f"{[o.__class__.__name__ for o in other]}")

		# convert to int if needed
		if self._mode == "RGB":
			_operator = lambda a, b: min(max(int(operator(a, b)), 0), 255)
		elif self._mode == "rgb":
			_operator = lambda a, b: min(max(operator(a, b), 0), 1)
		else:
			raise self._not_implemented()

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
			raise self._not_implemented()

	# arithmetic operations
	def __add__(self, other: Union[_N, TikZColor, ColorTuple]) -> TikZColor[_N]:
		return self.__binary_operation__(other, lambda a, b: a + b)

	def __sub__(self, other: Union[_N, TikZColor, ColorTuple]) -> TikZColor[_N]:
		return self.__binary_operation__(other, lambda a, b: a - b)

	def __mul__(self, other: Union[_N, TikZColor, ColorTuple]) -> TikZColor[_N]:
		return self.__binary_operation__(other, lambda a, b: a * b)

	def __truediv__(self, other: Union[_N, TikZColor, ColorTuple]) -> TikZColor[_N]:
		return self.__binary_operation__(other, lambda a, b: a / b)

	def __floordiv__(self, other: Union[_N, TikZColor, ColorTuple]) -> TikZColor[_N]:
		return self.__binary_operation__(other, lambda a, b: a // b)

	def __mod__(self, other: Union[_N, TikZColor, ColorTuple]) -> TikZColor[_N]:
		return self.__binary_operation__(other, lambda a, b: a % b)

	def __pow__(self, power: Union[_N, TikZColor, ColorTuple]) -> TikZColor[_N]:
		return self.__binary_operation__(power, lambda a, b: a ** b)

	# "right" arithmetic operations
	def __radd__(self, other: Union[_N, TikZColor, ColorTuple]) -> TikZColor[_N]:
		return self.__binary_operation__(other, lambda a, b: b + a)

	def __rsub__(self, other: Union[_N, TikZColor, ColorTuple]) -> TikZColor[_N]:
		return self.__binary_operation__(other, lambda a, b: b - a)

	def __rmul__(self, other: Union[_N, TikZColor, ColorTuple]) -> TikZColor[_N]:
		return self.__binary_operation__(other, lambda a, b: b * a)

	def __rtruediv__(self, other: Union[_N, TikZColor, ColorTuple]) -> TikZColor[_N]:
		return self.__binary_operation__(other, lambda a, b: b / a)

	def __rfloordiv__(self, other: Union[_N, TikZColor, ColorTuple]) -> TikZColor[_N]:
		return self.__binary_operation__(other, lambda a, b: b // a)

	def __rmod__(self, other: Union[_N, TikZColor, ColorTuple]) -> TikZColor[_N]:
		return self.__binary_operation__(other, lambda a, b: b % a)

	def __rpow__(self, other: Union[_N, TikZColor, ColorTuple]) -> TikZColor[_N]:
		return self.__binary_operation__(other, lambda a, b: b ** a)

	def __len__(self) -> int:
		return len(self._value)

	def __repr__(self) -> str:
		return repr_string(self, TikZColor.raw_name, TikZColor.value, TikZColor.mode)

	# ~~~~~~~~~~~~~~~ DEFAULT COLORS ~~~~~~~~~~~~~~~

	@classmethod
	def __set_default_colors__(cls) -> None:
		""" This function initializes the default or resets colors. """
		cls.WHITE: TikZColor[int] = TikZColor("WHITE", (255, 255, 255, 255), "RGB")
		cls.ALMOST_WHITE: TikZColor[int] = TikZColor("ALMOST_WHITE", (245, 245, 245, 255), "RGB")
		cls.LIGHT_GRAY: TikZColor[int] = TikZColor("LIGHT_GRAY", (180, 180, 180, 255), "RGB")
		cls.DARK_GRAY: TikZColor[int] = TikZColor("DARK_GRAY", (45, 45, 45, 255), "RGB")
		cls.ALMOST_BLACK: TikZColor[int] = TikZColor("ALMOST_BLACK", (18, 18, 18, 255), "RGB")
		cls.BLACK: TikZColor[int] = TikZColor("BLACK", (0, 0, 0, 255), "RGB")
		cls.RED: TikZColor[int] = TikZColor("RED", (252, 68, 68, 255), "RGB")
		cls.ORANGE: TikZColor[int] = TikZColor("ORANGE", (255, 165, 0, 255), "RGB")
		cls.YELLOW: TikZColor[int] = TikZColor("YELLOW", (251, 219, 4, 255), "RGB")
		cls.GREEN: TikZColor[int] = TikZColor("GREEN", (139, 195, 74, 255), "RGB")
		cls.LIGHT_BLUE: TikZColor[int] = TikZColor("LIGHT_BLUE", (3, 169, 244, 255), "RGB")
		cls.DARK_BLUE: TikZColor[int] = TikZColor("DARK_BLUE", (4, 60, 140, 255), "RGB")
		cls.PURPLE: TikZColor[int] = TikZColor("PURPLE", (103, 58, 183, 255), "RGB")
		cls.MAGENTA: TikZColor[int] = TikZColor("MAGENTA", (156, 39, 176, 255), "RGB")
		cls.PINK: TikZColor[int] = TikZColor("PINK", (236, 76, 140, 255), "RGB")
		cls.ROSE: TikZColor[int] = TikZColor("ROSE", (252, 140, 132, 255), "RGB")
		cls.DEFAULT_COLORS: Tuple[TikZColor[int], ...] = (
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

# init default colors
TikZColor.__set_default_colors__()

class TikZArrowDirection(Enum):
	"""
	:py:class:`TikZArrowDirection` is an enum which helps to track which direction an arrow of :py:class:`TikZArrow` is
	pointing. It contains the values ``NONE``, ``LEFT``, ``RIGHT``, and ``BOTH``.
	"""
	NONE: Final = 0
	LEFT: Final = 1
	RIGHT: Final = 2
	BOTH: Final = 3

# convenience variables to keep names short and snappy
_NONE, _LEFT, _RIGHT, _BOTH = TikZArrowDirection.NONE, TikZArrowDirection.LEFT, \
							  TikZArrowDirection.RIGHT, TikZArrowDirection.BOTH

class _TikZArrow(Enum):
	"""
	:py:class:`_TikZArrow` is the baseclass enumeration for holding TikZ arrow head type data.

	:param key: the TikZ key for this arrow head type (e.g. ``->``)
	:param direction: which way the arrow head is pointing (e.g. ``->`` uses ``TikZArrowDirection.RIGHT``)
	"""

	def _generate_next_value_(name, start, count, last_values) -> int:
		if last_values is None:
			return 0
		else:
			return last_values + 1

	def __init__(self, key: str, direction: TikZArrowDirection):
		super(_TikZArrow, self).__init__()
		# check types
		if not isinstance(key, str):
			raise TypeError(f"TikZArrow enum entries must be of shape 'TikZ value key, direction' with type 'str', "
							f"and type 'TikZArrowDirection', found type {repr(key.__class__.__name__)}")
		if not isinstance(direction, TikZArrowDirection):
			raise TypeError(f"TikZArrow enum entries must be of shape 'TikZ value key, direction' with type 'str', "
							f"and type 'TikZArrowDirection', found type {repr(direction.__class__.__name__)}")
		self._name = str(self._name_)
		self._key = key
		self._direction = direction

	@property
	def name(self) -> str:
		""" :return: the name of this enum object """
		return self._name

	@property
	def key(self) -> str:
		""" :return: the TikZ key for this arrow head type """
		return self._key

	@property
	def direction(self) -> TikZArrowDirection:
		""" :return: the direction the arrow is pointing as :py:class:`_TikZArrowDirection` enum value """
		return self._direction

	def __repr__(self) -> str:
		return repr_string(self, _TikZArrow.key)

class TikZArrow(_TikZArrow):
	"""
	:py:class:`TikZArrow` is an enumeration of TikZ arrow head types. An arrow enum variable has three values associated
	with it:

		- the name of the type, which only holds internal relevance
		- the TikZ key of the type, which is used in the TikZ source
		- the :py:class:`TikZArrowDirection` of the type, which indicates which way the arrow is pointing
	"""
	LINE: Final = "-", _NONE

	LEFT: Final = "<-", _LEFT
	RIGHT: Final = "->", _RIGHT
	LEFT_RIGHT: Final = "<->", _BOTH
	IN_LEFT: Final = ">-", _LEFT
	IN_RIGHT: Final = "-<", _RIGHT
	IN_LEFT_RIGHT: Final = ">-<", _BOTH

	LEFT_STUMP: Final = "|-", _LEFT
	RIGHT_STUMP: Final = "-|", _RIGHT
	LEFT_RIGHT_STUMP: Final = "|-|", _BOTH

	LEFT_LATEX: Final = "latex-", _LEFT
	RIGHT_LATEX: Final = "-latex", _RIGHT
	LEFT_RIGHT_LATEX: Final = "latex-latex", _BOTH
	LEFT_LATEX_PRIME: Final = "latex'-", _LEFT
	RIGHT_LATEX_PRIME: Final = "-latex'", _RIGHT
	LEFT_RIGHT_LATEX_PRIME: Final = "latex'-latex'", _BOTH

	LEFT_CIRC: Final = "o-", _LEFT
	RIGHT_CIRC: Final = "-o", _RIGHT
	LEFT_RIGHT_CIRC: Final = "o-o", _BOTH

class TikZStyle(TikZDefinesWriteable[TikZColor]):
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

	One can either iterate over the non-None values of this instance, or call the :py:meth:`to_tikz` method:

	>>> multiple_style = TikZStyle(width="1cm", draw=True)
	>>> for s in multiple_style:
	...		print(s)
	('width', '1cm')
	('draw', True)
	>>> print(multiple_style.to_tikz())
	draw, width={1cm}

	Style objects can be compared using ``==`` and ``!=``, and test equal if and only if they have matching key value
	pairs in :py:attr:`style` (i.e. the values passed to the constructor).

	>>> assert TikZStyle(dashed=True, line_width="2mm") == TikZStyle(dashed=True, line_width="2mm")
	>>> assert TikZStyle(dashed=True) != EMPTY_STYLE

	Style obejcts may also be combined using either ``+``, ``&``, or ``|``, which all hold the same meaning. When styles
	are combined, the style obejct on the right will overwrite any overlapping attributes of the style on the left side.

	>>> style1 = TikZStyle(dashed=True, align="left")
	>>> style2 = TikZStyle(dotted=True, align="right")
	>>> assert style1 + style2 == TikZStyle(dashed=True, dotted=True, align="right")
	>>> assert style2 & style1 == TikZStyle(dashed=True, dotted=True, align="left")
	>>> assert style1 | style2 == style1 + style2

	:param custom_entries: an optional mapping of any entries not included in the keyword arguments
	"""

	DictVal: Final = Optional[Union[AnyStr, bool, int, float]]
	""" The types of a dictionary entry of the styles dictionary. """

	# This tuple is purely used to define the style properties so that IDEs and other tools can find and suggest them
	__slots__ = ("width", "height", "x_scale", "y_scale", "scale", "shift",
				 "bend_left", "bend_right", "loop", "loop_above", "loop_below", "loop_left", "loop_right",
				 "draw", "circle", "rectangle",
				 "dashed", "dotted", "line_width", "shorten_start", "shorten_end",
				 "color", "fill",
				 "align",
				 "draw_opacity", "fill_opacity")

	def __init__(self,
				 custom_entries: Optional[Mapping[AnyStr, DictVal]] = None,
				 *,
				 width: Optional[TikZValue] = None,
				 height: Optional[TikZValue] = None,
				 x_scale: Optional[TikZValue] = None,
				 y_scale: Optional[TikZValue] = None,
				 scale: Optional[TikZValue] = None,
				 shift: Optional[Tuple[TikZValue, TikZValue]] = None,

				 bend_left: Optional[Union[bool, TikZValue]] = None,
				 bend_right: Optional[Union[bool, TikZValue]] = None,
				 loop: Optional[bool] = None,
				 loop_above: Optional[bool] = None,
				 loop_below: Optional[bool] = None,
				 loop_left: Optional[bool] = None,
				 loop_right: Optional[bool] = None,

				 draw: bool = True,
				 circle: Optional[bool] = None,
				 rectangle: Optional[bool] = None,

				 dashed: Optional[bool] = None,
				 dotted: Optional[bool] = None,
				 line_width: Optional[TikZValue] = None,
				 shorten_start: Optional[TikZValue] = None,
				 shorten_end: Optional[TikZValue] = None,

				 color: Optional[TikZColor] = None,
				 fill: Optional[TikZColor] = None,

				 align: Optional[AnyStr] = None,

				 draw_opacity: Optional[float] = None,
				 fill_opacity: Optional[float] = None):
		super(TikZStyle, self).__init__((), (), ())

		if draw is None:
			raise ValueError("'draw' cannot be set to None")

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
				"loop"        : loop,
				"loop above"  : loop_above,
				"loop below"  : loop_below,
				"loop left"   : loop_left,
				"loop right"  : loop_right,

				"draw"        : draw,
				"circle"      : circle,
				"rectangle"   : rectangle,

				"dashed"      : dashed,
				"dotted"      : dotted,
				"line width"  : line_width,
				"shorten <"   : shorten_start,
				"shorten >"   : shorten_end,

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
		# dict to remove duplicates
		self._colors: Tuple[TikZColor] = tuple(dict.fromkeys(
				v for k, v in self._style.items() if isinstance(v, TikZColor)))
		self.__register_writeable_object__(*self._colors)

	@staticmethod
	def normalize_key(s: str) -> str:
		""" Removes any underscores or hyphens and replaces them with spaces. """
		return s.replace("_", " ").replace("-", " ")

	@property
	def style(self) -> Dict[AnyStr, DictVal]:
		""" :return: a copy of the styles stored in this instance """
		return dict(self._style)

	@property
	def colors(self) -> Tuple[TikZColor]:
		""" :return: a copy of the unique colors used in this instance, removes ``None`` values """
		return self._colors

	@property
	def empty(self) -> bool:
		""" :return: whether or not this style instance has no properties (aside from the ``draw`` flag) set """
		return (self is EMPTY_STYLE) or (len(self) <= 1)

	def __and__(self, other: TikZStyle) -> TikZStyle:
		return TikZStyle(dict(list(self) + list(other)))

	def __or__(self, other: TikZStyle) -> TikZStyle:
		return self.__and__(other)

	def __add__(self, other: TikZStyle) -> TikZStyle:
		return self.__and__(other)

	def __len__(self) -> int:
		_len = 0
		for key, val in self:
			_len += 0 if val is None else 1
		return _len

	def __contains__(self, item) -> bool:
		key = self.normalize_key(str(item))
		return key in self._style and self._style[key] is not None

	def __iter__(self) -> Iterator[Tuple[str, DictVal]]:
		for key, value in self._style.items():
			if value is not None:
				yield key, value

	def __setitem__(self, key, value) -> NoReturn:
		raise SyntaxError(f"Cannot assign to attribute {key} of TikZStyle, this class is immutable")

	def __getitem__(self, item) -> DictVal:
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

	def to_tikz(self) -> str:
		# process normal items and flags (bool) separately
		style_strings = [f"{key}={{{str(value)}}}" for key, value in self if not isinstance(value, bool)]
		style_flags = [f"{key}" for key, value in self if isinstance(value, bool) and value]
		return ", ".join(style_flags + style_strings)

	def __repr__(self) -> str:
		return f"TikZStyle({', '.join([f'{key}={value}' for key, value in self])})"

EMPTY_STYLE: Final[TikZStyle] = TikZStyle()
""" The default empty :py:class:`TikZStyle` object. """

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ ENVIRONMENTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TikZPicture(LaTeXEnvironment):
	r"""
	:py:class:`TikZPicture` represents the standard TikZ ``tikzpicture`` environment. This class aids in writing special
	TikZ objects like :py:class:`TikZColor`, but can also be written to manually.

	..	warning::

		When a :py:class:`TikZNamed` object is written to this class, its :py:attr:`TikZNamed.definition` string will be
		directly written to the document without registering it, or checking if the object has been written to this instance
		before. However, when a :py:class:`TikZDefinesWriteable` object is written to this class, all the registered
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
				 style: TikZStyle = EMPTY_STYLE,
				 defined_colors: Collection[TikZColor] = (),
				 indent_level: int = 1):
		super(TikZPicture, self).__init__(parent_env,
										  environment_name="tikzpicture",
										  options=style.to_tikz(),
										  required_packages=("tikz",),
										  indent_level=indent_level)

		self.__tikz_init__(style, defined_colors, indent_level)

	def __tikz_init__(self, style: TikZStyle, written_named_object_definitions: Collection[TikZNamed],
					  indent_level: int) -> None:
		""" Initialize this environment. This function should be called by subclasses which do not call the super constructor. """
		self._written_named_object_definitions: List[TikZNamed] = list(written_named_object_definitions)
		self._definition_handler = TeXHandler(indent_level)
		self.write_named_object_definition(*style.colors)

	@property
	def written_named_object_definitions(self) -> Tuple[TikZNamed]:
		""" :return: the :py:class:`TikZNamed` objects which have so far been written and defined by this environment """
		return tuple(self._written_named_object_definitions)

	def write_named_object_definition(self, *obj: TikZNamed) -> None:
		"""
		Register one or multiple :py:class:`TikZNamed` objects with this instance. This will define the objects at the
		beginning of the environment using a special handler.

		:param obj: the named object or objects to define
		"""
		for o in (p for p in obj if p not in self._written_named_object_definitions):
			# register packages
			self.document.use_package(*o.required_packages)
			# register tikz libraries
			self.document.use_tikz_library(*o.required_tikz_libraries)
			# define in this instance
			self._definition_handler.write(o.definition)
			self._written_named_object_definitions.append(o)

	def write(self, s: Union[TikZWriteable, AnyStr, TeXHandler]) -> None:
		"""
		Write ``s`` to the handler of this instance.

		The following conditions apply to special object types:

			-	If ``s`` is a string or :py:class:`TeXHandler` this method will simply write it.

			-	If ``s`` is a :py:class:`TikZWriteable` object this method will first register the required packages, then
			 	the required TikZ libraries, then call the ``to_latex`` method of the object, and finally add ``;`` to the
			 	end if it is missing.

				-	If ``s`` is also a :py:class:`TikZNamed` objet this method will additionally write its definition to
				 	the document directly. This is in contrast to how :py:class:`TikZDefinesWriteable` works, since those
				 	objects will be defined with this class and then written to a special definition handler.

				-	If ``s`` is also a :py:class:`TikZDefinesWriteable` object this method will additionally register all
				 	the defined objects recursively, if they do not compare equal to any of the objects which have been
				 	defined by this class previously. These definitions are written to a special definition handler.

		:param s: the object to write to the handler
		"""
		if isinstance(s, TikZWriteable):
			# register packages
			self.document.use_package(*s.required_packages)
			# register tikz libraries
			self.document.use_tikz_library(*s.required_tikz_libraries)

			# register defines writeable objs
			if isinstance(s, TikZDefinesWriteable):
				self.write_named_object_definition(*s.required_named_objects)

			# get string form of tikz writeable
			if isinstance(s, TikZNamed):
				# this is here so you can write a TikZNamed definition
				# manually to the actual document handler!
				s = s.definition
			else:
				s = s.to_tikz()

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
				 style: TikZStyle = EMPTY_STYLE,
				 indent_level: int = 1):
		# make sure we are in a tikz picture env
		if not isinstance(parent_env, TikZPicture):
			raise TypeError(f"TikZScope must be nested within the context manager of a TikZPicture environment or a "
							f"subclass of it, but received {parent_env.__class__.__name__}")

		super(TikZPicture, self).__init__(parent_env,
										  environment_name="scope",
										  options=style.to_tikz(),
										  required_packages=("tikz",),
										  indent_level=indent_level)
		self.__tikz_init__(style, parent_env.written_named_object_definitions, indent_level)
