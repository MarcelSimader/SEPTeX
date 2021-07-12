"""
:Author: Marcel Simader
:Date: 30.06.2021

.. versionadded:: v0.1.0
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ IMPORTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from __future__ import annotations

import math
from numbers import Number, Real
from typing import Union, AnyStr, Optional, Collection, Tuple, Final, TypeVar, Callable, Generic

from SEPModules.SEPPrinting import repr_string

from SEPTeX.TikZBase import TikZWriteable, TikZNamed, TikZDefinesNamed, TikZColor, TikZStyle, TikZArrow, TIKZ_VALUE

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ GLOBALS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

R: Final = TypeVar("R", bound=Number)
""" First constrained type variable for the :py:mod:`TikZ` module. The type of this variable must be a number. """

T: Final = TypeVar("T", bound=Number)
""" Second constrained type variable for the :py:mod:`TikZ` module. The type of this variable must be a number. """

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ TIKZ OBJECTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Point(TikZWriteable, Generic[R, T]):
	r"""
	:py:class:`Point` represented a 2 dimensional coordinate of form :math:`(x, y)`. The class additionally holds information
	on the unit used for the values ``R`` and ``T``. Various arithmetic operations upon two points are supported, but only
	if they share the **same unit**.

	To perform the vector dot product on two points, use the "matrix-mul" operator ``@``.

	:param x: the x-coordinate
	:param y: the y-coordinate
	:param unit: keyword-only argument, denotes the unit to suffix at the end of the :py:class:`Point` instance, is
	 	**automatically converted to all lower case**, for instance ``Point(3, 4, unit="CM")`` will produce the output
	 	 ``( 3.000cm,  4.000cm)``
	:param relative: whether or not this point should be considered relative in the used path or not
	"""

	POINT_TEMPLATE: AnyStr = r"{}({: .3f}{unit}, {: .3f}{unit})"
	""" The format string to use when formatting a point to a string. """

	def __init__(self, x: R, y: T, *, unit: AnyStr = "", relative: bool = False):
		super(Point, self).__init__((), ())
		self._x = x
		self._y = y
		self._unit = unit.lower()
		self._relative = relative

	@property
	def x(self) -> R:
		r""" :return: the x coordinate """
		return self._x

	@property
	def y(self) -> T:
		r""" :return: the y coordinate """
		return self._y

	@property
	def angle(self) -> float:
		""" :return: the angle of this point in polar coordinates in degrees """
		if self._y == 0:
			return 0
		return math.atan(self._x / self._y) * 180 / math.pi

	@property
	def radius(self) -> float:
		""" :return: the radius of this point in polar coordinates """
		return self.geometric_length()

	@property
	def point(self) -> Tuple[R, T]:
		r""" :return: the tuple :math:`(x, y)` """
		return self.x, self.y

	@property
	def unit(self) -> AnyStr:
		r""" :return: the all lower-case unit suffix """
		return self._unit

	@property
	def relative(self) -> bool:
		""" :return: whether or not this point is relative """
		return self._relative

	# arithmetic
	def __other_as_tuple__(self, other: Union[Real, Point, Tuple[Real, Real]],
						   check_unit: bool = False) -> Tuple[Real, Real]:
		if isinstance(other, Point):
			if check_unit:
				self.__require_same_unit__(other)
			other = other.point
		if not isinstance(other, Tuple):
			other = (other,) * 2
		return other

	def __require_same_unit__(self, other: Point) -> None:
		if not self._unit == other._unit:
			raise ValueError(f"Cannot perform arithmetic operation on points of two different units, "
							 f"given {repr(self._unit)} and {repr(other._unit)}")

	def __require_non_zero__(self, other: Union[Real, Point, Tuple[Real, Real]], msg: AnyStr) -> None:
		other = self.__other_as_tuple__(other)
		if any([n == 0 for n in other]):
			raise ZeroDivisionError(f"None of the components of {repr(other)} can be 0 for performing {msg}")

	def __binary_operation__(self, other: Union[Real, Point, Tuple[Real, Real]],
							 operator: Callable[[Real, Real], Real]) -> Point:
		o = self.__other_as_tuple__(other, check_unit=True)
		return Point(operator(self._x, o[0]), operator(self._y, o[1]), unit=self._unit,
					 relative=self._relative and (not isinstance(other, Point) or other._relative))

	def __add__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point:
		return self.__binary_operation__(other, lambda a, b: a + b)

	def __sub__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point:
		return self.__binary_operation__(other, lambda a, b: a - b)

	def __mul__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point:
		return self.__binary_operation__(other, lambda a, b: a * b)

	def __truediv__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point:
		self.__require_non_zero__(other, "division")
		return self.__binary_operation__(other, lambda a, b: a / b)

	def __floordiv__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point:
		self.__require_non_zero__(other, "floor division")
		return self.__binary_operation__(other, lambda a, b: a // b)

	def __mod__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point:
		self.__require_non_zero__(other, "modulo")
		return self.__binary_operation__(other, lambda a, b: a % b)

	def __pow__(self, power: Union[Real, Point, Tuple[Real, Real]]) -> Point:
		return self.__binary_operation__(power, lambda a, b: a ** b)

	def __matmul__(self, other: Point) -> float:
		self.__require_same_unit__(other)
		return self._x * other._x + self._y * other._y

	# "right" arithmetic operations
	def __radd__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point:
		return self.__binary_operation__(other, lambda a, b: b + a)

	def __rsub__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point:
		return self.__binary_operation__(other, lambda a, b: b - a)

	def __rmul__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point:
		return self.__binary_operation__(other, lambda a, b: b * a)

	def __rtruediv__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point:
		self.__require_non_zero__(self, "division")
		return self.__binary_operation__(other, lambda a, b: b / a)

	def __rfloordiv__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point:
		self.__require_non_zero__(self, "floor division")
		return self.__binary_operation__(other, lambda a, b: b // a)

	def __rmod__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point:
		self.__require_non_zero__(self, "modulo")
		return self.__binary_operation__(other, lambda a, b: b % a)

	def __rpow__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point:
		return self.__binary_operation__(other, lambda a, b: b ** a)

	def __rmatmul__(self, other: Point) -> float:
		self.__require_same_unit__(other)
		return self._x * other._x + self._y * other._y

	# misc operations
	def as_int(self) -> Point[int, int]:
		r""" :return: a new point :math:`(\text{int}(x), \text{int}(y))` """
		return Point(int(self._x), int(self._y), unit=self._unit, relative=self._relative)

	def as_float(self) -> Point[float, float]:
		r""" :return: a new point :math:`(\text{float}(x), \text{float}(y))` """
		return Point(float(self._x), float(self._y), unit=self._unit, relative=self._relative)

	def __neg__(self) -> Point[R, T]:
		r""" :return: a new point :math:`((-1) * x, (-1) * y)` """
		return Point(-self._x, -self._y, unit=self._unit, relative=self._relative)

	def __abs__(self) -> Point[R, T]:
		r""" :return: a new point :math:`(\text{abs}(x), \text{abs}(y))` """
		return Point(abs(self._x), abs(self._y), unit=self._unit, relative=self._relative)

	def geometric_length(self) -> float:
		r""" :return: the geometric length of this point to the origin :math:`\vec 0` """
		return math.sqrt(self._x ** 2 + self._y ** 2)

	def __hash__(self) -> int:
		return hash((self._x, self._y, self.angle, self.radius, self._relative, self._unit))

	def __eq__(self, other) -> bool:
		if not isinstance(other, Point):
			return False
		return (self._x == other._x) and (self._y == other._y) \
			   and (self.angle == other.angle) and (self.radius == other.radius) \
			   and (self._relative == other._relative) and (self._unit == other._unit)

	# str operations
	def __str__(self) -> str:
		return self.POINT_TEMPLATE.format("+" if self._relative else "", self._x, self._y, unit=self._unit)

	def __repr__(self) -> str:
		return repr_string(self, Point.x, Point.y, Point.unit, Point.relative)

class PolarPoint(Point):
	"""
	:py:class:`PolarPoint` represents a point in polar coordinates. It modifies the functionality of :py:class:`Point`.

	:param angle: the angle component **in degrees**
	:param radius: the radial component
	:param unit: keyword-only argument, denotes the unit to suffix at the end of the :py:class:`Point` instance, is
	 	**automatically converted to all lower case**, for instance ``PolarPoint(314, 4, unit="CM")`` will produce the
	 	output ``( 314.000: 4.000cm)``
	:param relative: whether or not this point should be considered relative in the used path or not
	"""

	POINT_TEMPLATE: AnyStr = r"{}({: .3f}:{: .3f}{unit})"
	""" The format string to use when formatting a point to a string. """

	def __init__(self, angle: R, radius: T, *, unit: AnyStr = "", relative: bool = False):
		self._angle = angle % 360
		self._radius = radius
		super(PolarPoint, self).__init__(self.x, self.y, unit=unit, relative=relative)

	@property
	def x(self) -> float:
		return math.cos((self._angle % 360) * math.pi / 180) * self._radius

	@property
	def y(self) -> float:
		return math.sin((self._angle % 360) * math.pi / 180) * self._radius

	@property
	def angle(self) -> R:
		return self._angle % 360

	@property
	def radius(self) -> T:
		return self._radius % 360

	# misc operations
	def as_int(self) -> PolarPoint[int, int]:
		r""" :return: a new point :math:`(\text{int}(\text{angle}), \text{int}(\text{radius}))` """
		return PolarPoint(int(self._angle), int(self._radius), unit=self._unit, relative=self._relative)

	def as_float(self) -> PolarPoint[float, float]:
		r""" :return: a new point :math:`(\text{float}(\text{angle}), \text{float}(\text{radius}))` """
		return PolarPoint(float(self._angle), float(self._radius), unit=self._unit, relative=self._relative)

	def __neg__(self) -> PolarPoint[R, T]:
		r""" :return: a new point :math:`(\text{angle} \text{ mod } 360, (-1) * \text{radius})` """
		return PolarPoint(self._angle % 360, -self._radius, unit=self._unit, relative=self._relative)

	def __abs__(self) -> PolarPoint[R, T]:
		r""" :return: a new point :math:`(\text{abs}(\text{angle}), \text{abs}(\text{radius}))` """
		return PolarPoint(abs(self._angle), abs(self._radius), unit=self._unit, relative=self._relative)

	# str operations
	def __str__(self) -> str:
		return self.POINT_TEMPLATE.format("+" if self._relative else "", self._angle, self._radius, unit=self._unit)

	def __repr__(self) -> str:
		return repr_string(self, PolarPoint.angle, PolarPoint.radius, PolarPoint.unit, PolarPoint.relative)

class RelPoint(Point):
	"""
	:py:class:`RelPoint` is an alias of :py:class:`Point` with the ``relative`` option set to ``True`` by default.

	:param x: the x-coordinate
	:param y: the y-coordinate
	:param unit: keyword-only argument, denotes the unit to suffix at the end of the :py:class:`Point` instance, is
	 	**automatically converted to all lower case**, for instance ``Point(3, 4, unit="CM")`` will produce the output
	 	 ``( 3.000cm,  4.000cm)``

	..	seealso:: :py:class:`Point` for more details.
	"""

	def __init__(self, x: T, y: T, *, unit: AnyStr = ""):
		super(RelPoint, self).__init__(x, y, unit=unit, relative=True)

class TikZNode(TikZDefinesNamed[TikZColor], TikZNamed):
	"""
	:py:class:`TikZNode` represents a standard TikZ node. It holds information about its coordinate, name, label and style.
	A node must first be registered with a :py:class:`TikZPicture` instance by writing it, which happens implicitly if not
	stated explicitly.

	Comparisons of node objects will compare the names of each node.

	>>> assert TikZNode(Point(5, 2), name="x0") == TikZNode(Point(20, -4), name="x0")
	>>> assert TikZNode(Point(0, 0), name="origin") != TikZNode(Point(0, 0), name="o")

	:param coordinate: the coordinate at which this node should be placed
	:param name: the name which will be used to reference this node
	:param label: the label which will be displayed on the document for this node
	:param relative_to: the node to consider ``coordinate`` to be relative to
	:param style: the style to apply to this node
	"""

	def __init__(self,
				 coordinate: Point = Point(0, 0),
				 name: AnyStr = "",
				 label: AnyStr = "",
				 relative_to: Optional[TikZNode] = None,
				 style: TikZStyle = TikZStyle()):
		super(TikZNode, self).__init__((), (), styles=(style,), named_objs=())

		if coordinate.relative:
			raise ValueError(f"Passed in coordinate {repr(coordinate)} cannot be set to relative")

		if relative_to is not None:
			if not coordinate.unit == relative_to.coordinate.unit:
				raise ValueError(f"Coordinate units of 'relative_to' node must match the supplied units "
								 f"({repr(coordinate.unit)}), but received {repr(relative_to.coordinate.unit)}")
			coordinate = relative_to.coordinate + coordinate

		self._coordinate = coordinate
		self._name = str(name)
		self._label = str(label)
		self._style = style

	@property
	def coordinate(self) -> Point:
		""" :return: the coordinate of this node """
		return self._coordinate

	@property
	def style(self) -> TikZStyle:
		""" :return: the style used by this node """
		return self._style

	@property
	def label(self) -> str:
		""" :return: the label of this node """
		return self._label

	@property
	def name(self) -> str:
		""" :return: the name of this node """
		return self._name

	@property
	def definition(self) -> str:
		"""
		The command to draw the node in the document on its own. This is the standard when the node is written directly
		to a :py:class:`TikZPicture` instance. This method is equivalent to :py:meth:`__str__`.

		:return: the draw command for this node
		"""
		return f"\\node[{str(self._style)}]{'' if self._name == '' else f' ({self._name})'}" \
			   f" at {str(self._coordinate)} {{{self._label}}};"

	def __hash__(self):
		return hash(self._name)

	def __eq__(self, other):
		return isinstance(other, TikZNode) and self._name == other._name

	def __ne__(self, other):
		return not isinstance(other, TikZNode) or self._name != other._name

	def __str__(self) -> str:
		return self.definition

	def __repr__(self) -> str:
		return repr_string(self, TikZNode.coordinate, TikZNode.name, TikZNode.label)

class TikZLabel(TikZDefinesNamed[TikZColor]):
	"""
	DOCS write docs for TikZLabel
	"""

	def __init__(self,
				 label: AnyStr = "",
				 style: TikZStyle = TikZStyle(draw=False)):
		super(TikZLabel, self).__init__((), (), styles=(style,), named_objs=())

		self._label = label
		self._style = style

	@property
	def label(self) -> AnyStr:
		return self._label

	@property
	def style(self) -> TikZStyle:
		return self._style

	def __str__(self) -> str:
		return f"node [{self._style}] {{{self._label}}}"

class TikZPath(TikZDefinesNamed[TikZNode]):
	r"""
	:py:class:`TikZPath` represents a collection of coordinates and nodes drawn using the ``\draw`` command of TikZ.

	:param coordinates: a collection of :py:class:`Point` or :py:class:`TikZNode` objects for the path
	:param cycle: whether or not to end the final path string with ``cycle``, which will join the ending to the beginning
	:param style: the style to apply to this path
	"""

	_COORDINATE_JOINER = r" -- "
	r""" The symbol to use between the coordinates in the ``\draw`` command. """

	def __init__(self,
				 coordinates: Collection[Union[Point, TikZNode]],
				 cycle: bool = False,
				 label: Optional[TikZLabel] = None,
				 style: TikZStyle = TikZStyle()):
		super(TikZPath, self).__init__((), (),
									   styles=(style,),
									   named_objs=[n for n in coordinates if isinstance(n, TikZNamed)])

		self._coordinates = tuple(coordinates)
		self._coordinates_string = None
		self._cycle = cycle
		self._label = label
		self._style = style

	@property
	def arrow_type(self) -> TikZArrow:
		""" :return: the arrow type of a regular path is always :py:attr:`TikZArrow.LINE` """
		return TikZArrow.LINE

	@property
	def coordinates_string(self) -> str:
		"""
		Converts all of the coordinates of this instance to a string. If there are no coordinates then the empty string
		will be returned.
		"""
		if self._coordinates_string is None:
			if len(self._coordinates) <= 0:
				self._coordinates_string = str()
			else:
				coords = [f"({c.name})" if isinstance(c, TikZNode)
						  else str(c) for c in self._coordinates]
				self._coordinates_string = self._COORDINATE_JOINER.join(coords)
		return self._coordinates_string

	@property
	def coordinates(self) -> Tuple[Union[Point, TikZNode]]:
		""" :return: the coordinates and nodes along this path """
		return self._coordinates

	@property
	def cycle(self) -> bool:
		""" :return: whether or not to join the end of this path to its beginning """
		return self._cycle

	@property
	def label(self) -> Optional[TikZLabel]:
		return self._label

	@property
	def style(self) -> TikZStyle:
		""" :return: the style used by this path for its edge """
		return self._style

	def __str__(self) -> str:
		return f"\\draw[{str(self._style)}] {self.coordinates_string}" \
			   f"{f'{self._COORDINATE_JOINER}cycle' if self.cycle else ''}" \
			   f"{'' if self._label is None else f' node[{self._label.style}] {{{self._label.label}}}'};"

	def __repr__(self) -> str:
		return repr_string(self, TikZPath.coordinates, TikZPath.cycle)

class TikZDirectedPath(TikZPath):
	"""
	:py:class:`TikZDirectedPath` represents a path similarly to :py:class:`TikZPath` but with additional information
	on the arrow type used to join up the coordinates.

	:param coordinates: a collection of :py:class:`Point` or :py:class:`TikZNode` objects for the path
	:param cycle: whether or not to end the final path string with ``cycle``, which will join the ending to the beginning
	:param style: the style to apply to this path
	:param arrow_type: the :py:class:`TikZArrow` to use for the arrow tip of the edge
	"""

	_COORDINATE_JOINER = r" to "
	r""" The symbol to use between the coordinates in the ``\draw`` command. """

	def __init__(self,
				 coordinates: Collection[Union[Point, TikZNode]],
				 cycle: bool = False,
				 label: Optional[TikZLabel] = None,
				 style: TikZStyle = TikZStyle(),
				 arrow_type: TikZArrow = TikZArrow.LINE):
		super(TikZDirectedPath, self).__init__(coordinates, cycle, label, style)
		self.__register_required_tikz_library__("arrows")

		self._arrow_type = arrow_type

	@property
	def arrow_type(self) -> TikZArrow:
		""" :return: which arrow head type to use at the end of this path """
		return self._arrow_type

	def __str__(self) -> str:
		style_list = [x for x in (self._arrow_type.key, str(self._style)) if len(x) > 0]
		return f"\\draw[{', '.join(style_list)}] {self.coordinates_string}" \
			   f"{f'{self._COORDINATE_JOINER}cycle' if self.cycle else ''}" \
			   f"{'' if self._label is None else f' node[{self._label.style}] {{{self._label.label}}}'};"

	def __repr__(self) -> str:
		return repr_string(self, TikZDirectedPath.coordinates, TikZDirectedPath.cycle, TikZDirectedPath.arrow_type)

class TikZCircle(TikZDefinesNamed[TikZColor]):
	"""
	:py:class:`TikZCircle` represents a standard TikZ circle, with a center coordinate, radius and style.

	:param coordinate: the center coordinate of the circle
	:param radius: the radius of the circle
	:param style: the style of the circle
	"""

	def __init__(self,
				 coordinate: Point,
				 radius: TIKZ_VALUE,
				 style: TikZStyle = TikZStyle()):
		super(TikZCircle, self).__init__((), (), styles=(style,), named_objs=())

		self._coordinate = coordinate
		self._radius = radius
		self._style = style

	@property
	def coordinate(self) -> Point:
		""" :return: the center coordinate of this circle """
		return self._coordinate

	@property
	def radius(self) -> TIKZ_VALUE:
		""" :return: the radius of this circle """
		return self._radius

	@property
	def style(self) -> TikZStyle:
		""" :return: the style used by this circle """
		return self._style

	def __str__(self) -> str:
		return f"\\draw[{str(self._style)}] {str(self._coordinate)} circle ({self._radius});"

	def __repr__(self) -> str:
		return repr_string(self, TikZCircle.coordinate, TikZCircle.radius)
