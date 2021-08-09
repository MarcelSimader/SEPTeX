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
from typing import Union, AnyStr, Optional, Tuple, Final, TypeVar, Callable, Generic, Sequence, ClassVar, Literal

from SEPModules.SEPPrinting import repr_string

from SEPTeX.TikZBase import TikZWriteable, TikZNamed, TikZDefinesWriteable, TikZStyle, TikZArrow, TikZValue, \
	EMPTY_STYLE, _LEFT, _RIGHT, _BOTH, _NONE, _TikZArrow

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ GLOBALS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_N0: Final = TypeVar("_N0", bound=Number)
""" First constrained type variable for the :py:mod:`TikZ` module. The type of this variable must be a number. """

_N1: Final = TypeVar("_N1", bound=Number)
""" Second constrained type variable for the :py:mod:`TikZ` module. The type of this variable must be a number. """

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ TIKZ OBJECTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class Point(TikZWriteable, Generic[_N0, _N1]):
	r"""
	:py:class:`Point` represented a 2 dimensional coordinate of form :math:`(x, y)`. The class additionally holds information
	on the unit used for both of the values. Various arithmetic operations upon two points are supported, but only if they
	**share the same unit**.

	To perform the vector dot product on two points, use the "matrix-mul" operator ``@``.

	:param x: the x-coordinate
	:param y: the y-coordinate
	:param unit: keyword-only argument, denotes the unit to suffix at the end of the :py:class:`Point` instance, is
	 	**automatically converted to all lower case**, for instance ``Point(3, 4, unit="CM")`` will produce the output
	 	``( 3.000cm,  4.000cm)``
	:param relative: whether or not this coordinate should be considered relative in the used path or not
	"""

	POINT_TEMPLATE: ClassVar[str] = r"{}({: .7f}{unit}, {: .7f}{unit})"
	""" The format string to use when formatting a coordinate to a string. """

	def __init__(self, x: _N0, y: _N1, *, unit: AnyStr = "", relative: bool = False):
		super(Point, self).__init__((), ())
		self._x = x
		self._y = y
		self._unit = unit.lower()
		self._relative = relative

	@property
	def x(self) -> _N0:
		r""" :return: the x coordinate """
		return self._x

	@property
	def y(self) -> _N1:
		r""" :return: the y coordinate """
		return self._y

	@property
	def angle(self) -> float:
		""" :return: the angle of this coordinate in polar coordinates in degrees """
		if self._x == 0:
			return 0
		return math.atan(self._y / self._x) * 180.0 / math.pi

	@property
	def radius(self) -> float:
		""" :return: the radius of this coordinate in polar coordinates """
		return self.geometric_length()

	@property
	def coordinate(self) -> Tuple[_N0, _N1]:
		r""" :return: the tuple :math:`(x, y)` """
		return self.x, self.y

	@property
	def polar_coordinate(self) -> Tuple[float, float]:
		r""" :return: the tuple :math:`(\theta, r)` """
		return self.angle, self.radius

	@property
	def point(self) -> Point[_N0, _N1]:
		r""" :return: self """
		return self

	@property
	def unit(self) -> AnyStr:
		r""" :return: the all lower-case unit suffix """
		return self._unit

	@property
	def relative(self) -> bool:
		""" :return: whether or not this coordinate is relative """
		return self._relative

	# arithmetic
	def __other_as_tuple__(self, other: Union[Real, Point, Tuple[Real, Real]],
						   check_unit: bool = False) -> Tuple[Real, Real]:
		if isinstance(other, Point):
			if check_unit:
				self.__require_same_unit__(other)
			other = other.coordinate
		if not isinstance(other, Tuple):
			other = (other,) * 2
		return other

	def __require_same_unit__(self, other: Point) -> None:
		if self._unit != other._unit:
			raise ValueError(f"Cannot perform arithmetic operation on points of two different units, "
							 f"given {self._unit!r} and {other._unit!r}")

	def __require_non_zero__(self, other: Union[Real, Point, Tuple[Real, Real]], msg: AnyStr) -> None:
		other = self.__other_as_tuple__(other)
		if any([n == 0 for n in other]):
			raise ZeroDivisionError(f"None of the components of {other!r} can be 0 for performing {msg}")

	def __binary_operation__(self, other: Union[Real, Point, Tuple[Real, Real]],
							 operator: Callable[[Real, Real], Real]) -> Point[float, float]:
		o = self.__other_as_tuple__(other, check_unit=True)
		return Point(operator(self._x, o[0]), operator(self._y, o[1]), unit=self._unit,
					 relative=self._relative and (not isinstance(other, Point) or other._relative))

	def __add__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point[float, float]:
		return self.__binary_operation__(other, lambda a, b: a + b)

	def __sub__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point[float, float]:
		return self.__binary_operation__(other, lambda a, b: a - b)

	def __mul__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point[float, float]:
		return self.__binary_operation__(other, lambda a, b: a * b)

	def __truediv__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point[float, float]:
		self.__require_non_zero__(other, "division")
		return self.__binary_operation__(other, lambda a, b: a / b)

	def __floordiv__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point[float, float]:
		self.__require_non_zero__(other, "floor division")
		return self.__binary_operation__(other, lambda a, b: a // b)

	def __mod__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point[float, float]:
		self.__require_non_zero__(other, "modulo")
		return self.__binary_operation__(other, lambda a, b: a % b)

	def __pow__(self, power: Union[Real, Point, Tuple[Real, Real]]) -> Point[float, float]:
		return self.__binary_operation__(power, lambda a, b: a ** b)

	def __matmul__(self, other: Point) -> float:
		self.__require_same_unit__(other)
		return self._x * other._x + self._y * other._y

	# "right" arithmetic operations
	def __radd__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point[float, float]:
		return self.__binary_operation__(other, lambda a, b: b + a)

	def __rsub__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point[float, float]:
		return self.__binary_operation__(other, lambda a, b: b - a)

	def __rmul__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point[float, float]:
		return self.__binary_operation__(other, lambda a, b: b * a)

	def __rtruediv__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point[float, float]:
		self.__require_non_zero__(self, "division")
		return self.__binary_operation__(other, lambda a, b: b / a)

	def __rfloordiv__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point[float, float]:
		self.__require_non_zero__(self, "floor division")
		return self.__binary_operation__(other, lambda a, b: b // a)

	def __rmod__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point[float, float]:
		self.__require_non_zero__(self, "modulo")
		return self.__binary_operation__(other, lambda a, b: b % a)

	def __rpow__(self, other: Union[Real, Point, Tuple[Real, Real]]) -> Point[float, float]:
		return self.__binary_operation__(other, lambda a, b: b ** a)

	def __rmatmul__(self, other: Point) -> float:
		self.__require_same_unit__(other)
		return self._x * other._x + self._y * other._y

	# misc operations
	def as_int(self) -> Point[int, int]:
		r""" :return: a new coordinate :math:`(\text{int}(x), \text{int}(y))` """
		return Point(int(self._x), int(self._y), unit=self._unit, relative=self._relative)

	def as_float(self) -> Point[float, float]:
		r""" :return: a new coordinate :math:`(\text{float}(x), \text{float}(y))` """
		return Point(float(self._x), float(self._y), unit=self._unit, relative=self._relative)

	def __neg__(self) -> Point[_N0, _N1]:
		r""" :return: a new coordinate :math:`((-1) * x, (-1) * y)` """
		return Point(-self._x, -self._y, unit=self._unit, relative=self._relative)

	def __abs__(self) -> Point[_N0, _N1]:
		r""" :return: a new coordinate :math:`(\text{abs}(x), \text{abs}(y))` """
		return Point(abs(self._x), abs(self._y), unit=self._unit, relative=self._relative)

	def geometric_length(self) -> float:
		r""" :return: the geometric length of this coordinate to the origin :math:`\vec 0` """
		return math.sqrt(self._x ** 2.0 + self._y ** 2.0)

	def __hash__(self) -> int:
		return hash((round(self._x, 3), round(self._y, 3), round(self.angle, 3), round(self.radius, 3),
					 self._relative, self._unit))

	def __eq__(self, other) -> bool:
		if not isinstance(other, Point):
			return False
		return (round(self._x == other._x, 3)) and (round(self._y == other._y, 3)) \
			   and (round(self.angle == other.angle, 3)) and (round(self.radius == other.radius, 3)) \
			   and (self._relative == other._relative) and (self._unit == other._unit)

	# str operations
	def to_tikz(self) -> str:
		return self.POINT_TEMPLATE.format("+" if self._relative else "", self._x, self._y, unit=self._unit)

	def __repr__(self) -> str:
		return repr_string(self, Point.x, Point.y, Point.unit, Point.relative)

class PolarPoint(Point[_N0, _N1]):
	"""
	:py:class:`PolarPoint` represents a coordinate in polar coordinates. It slightly modifies the functionality of
	:py:class:`Point` but has largely the same methods.

	:param angle: the angle component **in degrees**
	:param radius: the radial component
	:param unit: keyword-only argument, denotes the unit to suffix at the end of the :py:class:`Point` instance, is
	 	**automatically converted to all lower case**, for instance ``PolarPoint(314, 4, unit="CM")`` will produce the
	 	output ``( 314.000: 4.000cm)``
	:param relative: whether or not this coordinate should be considered relative in the used path or not
	"""

	POINT_TEMPLATE: ClassVar[str] = r"{}({: .7f}:{: .7f}{unit})"
	""" The format string to use when formatting a coordinate to a string. """

	def __init__(self, angle: _N0, radius: _N1, *, unit: AnyStr = "", relative: bool = False):
		self._angle = angle % 360.0
		self._radius = radius
		super(PolarPoint, self).__init__(self.x, self.y, unit=unit, relative=relative)

	@property
	def x(self) -> float:
		return math.cos(self._angle * math.pi / 180.0) * self._radius

	@property
	def y(self) -> float:
		return math.sin(self._angle * math.pi / 180.0) * self._radius

	@property
	def angle(self) -> _N0:
		return self._angle % 360.0

	@property
	def radius(self) -> _N1:
		return self._radius

	# misc operations
	def as_int(self) -> PolarPoint[int, int]:
		r""" :return: a new coordinate :math:`(\text{int}(\text{angle}), \text{int}(\text{radius}))` """
		return PolarPoint(int(self._angle), int(self._radius), unit=self._unit, relative=self._relative)

	def as_float(self) -> PolarPoint[float, float]:
		r""" :return: a new coordinate :math:`(\text{float}(\text{angle}), \text{float}(\text{radius}))` """
		return PolarPoint(float(self._angle), float(self._radius), unit=self._unit, relative=self._relative)

	def __neg__(self) -> PolarPoint[_N0, _N1]:
		r""" :return: a new coordinate :math:`(\text{angle} \text{ mod } 360, (-1) * \text{radius})` """
		return PolarPoint(self._angle % 360, -self._radius, unit=self._unit, relative=self._relative)

	def __abs__(self) -> PolarPoint[_N0, _N1]:
		r""" :return: a new coordinate :math:`(\text{abs}(\text{angle}), \text{abs}(\text{radius}))` """
		return PolarPoint(abs(self._angle), abs(self._radius), unit=self._unit, relative=self._relative)

	# str operations
	def to_tikz(self) -> str:
		return self.POINT_TEMPLATE.format("+" if self._relative else "", self._angle, self._radius, unit=self._unit)

	def __repr__(self) -> str:
		return repr_string(self, PolarPoint.angle, PolarPoint.radius, PolarPoint.unit, PolarPoint.relative)

class RelPoint(Point[_N0, _N1]):
	"""
	:py:class:`RelPoint` is an alias of :py:class:`Point` with the ``relative`` option set to ``True`` by default.

	:param x: the x-coordinate
	:param y: the y-coordinate
	:param unit: keyword-only argument, denotes the unit to suffix at the end of the :py:class:`Point` instance, is
	 	**automatically converted to all lower case**, for instance ``Point(3, 4, unit="CM")`` will produce the output
	 	``( 3.000cm,  4.000cm)``

	..	seealso:: :py:class:`Point` for more details.
	"""

	def __init__(self, x: _N0, y: _N1, *, unit: AnyStr = ""):
		super(RelPoint, self).__init__(x, y, unit=unit, relative=True)

class TikZNode(TikZDefinesWriteable[TikZStyle], TikZNamed):
	"""
	:py:class:`TikZNode` represents a standard TikZ node. It holds information about its coordinate, name, label and style.
	A node must first be registered with a :py:class:`TikZPicture` instance by writing it, which happens implicitly if not
	stated explicitly.

	:param coordinate: the coordinate at which this node should be placed
	:param name: the name which will be used to reference this node
	:param label: the label which will be displayed on the document for this node
	:param relative_to: the node to consider ``coordinate`` to be relative to, or ``None``
	:param style: the style to apply to this node
	"""

	def __init__(self,
				 coordinate: Point[_N0, _N1] = Point(0, 0),
				 name: AnyStr = "",
				 label: AnyStr = "",
				 relative_to: Optional[TikZNode] = None,
				 style: TikZStyle = EMPTY_STYLE):
		super(TikZNode, self).__init__((), (), (style,))

		if coordinate.relative:
			raise ValueError(f"Passed in coordinate {repr(coordinate)} cannot be set to relative")

		self._coordinate = coordinate
		if relative_to is not None:
			if not coordinate.unit == relative_to.coordinate.unit:
				raise ValueError(f"Coordinate units of 'relative_to' node must match the supplied units "
								 f"({coordinate.unit!r}), but received {relative_to.coordinate.unit!r}")
			self._coordinate += relative_to._coordinate

		self._raw_coordinate = coordinate
		self._name = str(name)
		self._label = str(label)
		self._relative_to = relative_to
		self._style = style

	@property
	def raw_coordinate(self) -> Point[_N0, _N1]:
		""" :return: the raw coordinate of this node, this does not include the offset caused by a relative node """
		return self._raw_coordinate

	@property
	def coordinate(self) -> Point:
		""" :return: the true coordinate of this node, with the offset caused by the relative node """
		return self._coordinate

	@property
	def label(self) -> str:
		""" :return: the label of this node """
		return self._label

	@property
	def relative_to(self) -> Optional[TikZNode]:
		""" :return: the node which this node's position is considered relative to, or ``None`` """
		return self._relative_to

	@property
	def style(self) -> TikZStyle:
		""" :return: the style used by this node """
		return self._style

	@property
	def raw_name(self) -> str:
		""" :return: the name of this node without the parentheses """
		return self._name

	@property
	def name(self) -> str:
		""" :return: the name of this node, including parentheses """
		return "" if self._name == "" else f"({self._name})"

	@property
	def definition(self) -> str:
		return f"\\node[{self._style.to_tikz()}] {self.name}" \
			   f" at {self._coordinate.to_tikz()} {{{self._label}}};"

	def __repr__(self) -> str:
		return repr_string(self, TikZNode.coordinate, TikZNode.name, TikZNode.label)

class TikZLabel(TikZDefinesWriteable[TikZStyle]):
	"""
	:py:class:`TikZLabel` represents a TikZ label. These labels can be put on :py:class:`TikZNode` objects, or be used as
	labels for edges in :py:class:`TikZPath` objects.

	:param label: the label text of this label
	:param style: the style of this label, ``draw`` is set to ``False`` by default
	"""

	def __init__(self,
				 label: AnyStr = "",
				 style: TikZStyle = TikZStyle(draw=False)):
		super(TikZLabel, self).__init__((), (), (style,))

		self._label = label
		self._style = style

	@property
	def label(self) -> AnyStr:
		""" :return: the label text of this label """
		return self._label

	@property
	def style(self) -> TikZStyle:
		""" :return: the style of this label """
		return self._style

	def __hash__(self) -> int:
		return hash((self._label, self._style))

	def __eq__(self, other) -> bool:
		return isinstance(other, TikZLabel) and self._label == other._label and self._style == other._style

	def to_tikz(self) -> str:
		return f"node [{self._style.to_tikz()}] {{{self._label}}}"

class TikZPath(TikZDefinesWriteable[Union[TikZStyle, TikZNode]]):
	r"""
	:py:class:`TikZPath` represents a collection of :py:class:`Point`, :py:class:`TikZNode`, and :py:class:`TikZLabel`
	objects drawn using the ``\draw`` command of TikZ.

	:param coordinates: a collection of :py:class:`Point`, :py:class:`TikZNode`, or :py:class:`TikZLabel` objects for
		the path
	:param cycle: whether or not to end the final path string with ``cycle``, which will join the ending to the beginning
	:param style: the style to apply to this path
	"""

	_COORDINATE_JOINER: ClassVar[str] = r" -- "
	r""" The symbol to use between the coordinates in the ``\draw`` command. """

	def __init__(self,
				 coordinates: Sequence[Union[Point, TikZNode, TikZLabel]],
				 cycle: bool = False,
				 style: TikZStyle = EMPTY_STYLE):
		super(TikZPath, self).__init__((), (), (style, *coordinates))

		self._coordinates = tuple(coordinates)
		self._coordinates_string = None
		self._cycle = cycle
		self._style = style

		# find node relations
		self._node_relations = self.find_node_relations(self._coordinates, self.arrow_type)

	@staticmethod
	def find_node_relations(coordinates: Sequence[Union[Point, TikZNode, TikZLabel]],
							arrow_type: _TikZArrow) -> Tuple[Tuple[TikZNode, TikZNode], ...]:
		"""
		Finds the relations between objects passed in through the ``coordinates`` argument. It essentially returns a tuple
		of tuples indicating which :py:class:`TikZNode` objects "point" to which other nodes. For instance, if in a path
		node ``n0`` points visually to ``n1``, then the output of this function will be ``((n0, n1),)``.

		:param coordinates: a collection of :py:class:`Point`, :py:class:`TikZNode`, or :py:class:`TikZLabel` objects for
			the path
		:param arrow_type: the arrow type to consider when evaluating the node relations
		:return: a tuple of tuples containing the relations between the nodes passed in through the ``coordinates`` argument
		"""
		coord_nodes = tuple(c for c in coordinates if isinstance(c, TikZNode))
		return_list = list()

		if len(coord_nodes) >= 1:
			# add for last two nodes
			if arrow_type.direction == _LEFT:
				return_list.append((coord_nodes[-1], coord_nodes[-2]))
			elif arrow_type.direction == _RIGHT:
				return_list.append((coord_nodes[-2], coord_nodes[-1]))
			elif arrow_type.direction in (_NONE, _BOTH):
				return_list.extend(((coord_nodes[-1], coord_nodes[-2]), (coord_nodes[-2], coord_nodes[-1])))

			# add for other nodes except last
			for a, b in zip(coord_nodes[:-2], coord_nodes[1:-1]):
				return_list.extend(((a, b), (b, a)))

		# empty tuple if none found
		return tuple(return_list)

	@property
	def arrow_type(self) -> Literal[TikZArrow.LINE]:
		""" :return: the arrow type of a regular path is always :py:attr:`TikZArrow.LINE` """
		return TikZArrow.LINE

	@property
	def coordinates_string(self) -> str:
		"""
		Converts all of the coordinates of this instance to a string. If there are no coordinates then the empty string
		is returned.
		"""
		if self._coordinates_string is None:
			self._coordinates_string = str()
			for i, c in enumerate(self._coordinates):
				if i == len(self._coordinates) - 1:
					self._coordinates_string += c.to_tikz()
				elif isinstance(c, TikZLabel):
					self._coordinates_string += f"{c.to_tikz()} "
				else:
					self._coordinates_string += f"{c.to_tikz()}{self._COORDINATE_JOINER}"

		return self._coordinates_string

	@property
	def coordinates(self) -> Tuple[Union[Point, TikZNode, TikZLabel]]:
		""" :return: the points, nodes, and labels along this path """
		return self._coordinates

	@property
	def cycle(self) -> bool:
		""" :return: whether or not to join the end of this path to its beginning """
		return self._cycle

	@property
	def style(self) -> TikZStyle:
		""" :return: the style used by this path for its edge """
		return self._style

	@property
	def node_relations(self) -> Tuple[Tuple[TikZNode, TikZNode], ...]:
		""" :return: the node relations of this path, as described by :py:meth:`find_node_relations` """
		return self._node_relations

	def __hash__(self) -> int:
		return hash((self._style, self._coordinates, self._cycle))

	def __eq__(self, other) -> bool:
		return isinstance(other, TikZPath) and self._style == other._style \
			   and self._coordinates == other._coordinates and self._cycle == other._cycle

	def to_tikz(self) -> str:
		return f"\\draw[{self._style.to_tikz()}] {self.coordinates_string}" \
			   f"{f'{self._COORDINATE_JOINER}cycle' if self.cycle else ''};"

	def __repr__(self) -> str:
		return repr_string(self, TikZPath.coordinates, TikZPath.cycle)

class TikZDirectedPath(TikZPath):
	"""
	:py:class:`TikZDirectedPath` represents a path similarly to :py:class:`TikZPath` but with additional information
	on the arrow type used to join up the coordinates.

	This class implicitly uses the ``arrows`` TikZ library.

	:param coordinates: a collection of :py:class:`Point` or :py:class:`TikZNode` objects for the path
	:param cycle: whether or not to end the final path string with ``cycle``, which will join the ending to the beginning
	:param style: the style to apply to this path
	:param arrow_type: the :py:class:`_TikZArrow` to use for the arrow tip of the edge
	"""

	_COORDINATE_JOINER: ClassVar[str] = r" to "
	r""" The symbol to use between the coordinates in the ``\draw`` command. """

	def __init__(self,
				 coordinates: Sequence[Union[Point, TikZNode, TikZLabel]],
				 cycle: bool = False,
				 style: TikZStyle = EMPTY_STYLE,
				 arrow_type: _TikZArrow = TikZArrow.LINE):
		self._arrow_type = arrow_type
		super(TikZDirectedPath, self).__init__(coordinates, cycle, style)
		self.__register_required_tikz_library__("arrows")

	@property
	def arrow_type(self) -> _TikZArrow:
		""" :return: which arrow head type is used by this path """
		return self._arrow_type

	def to_tikz(self) -> str:
		style_list = [x for x in (self._arrow_type.key, self._style.to_tikz()) if len(x) > 0]
		return f"\\draw[{', '.join(style_list)}] {self.coordinates_string}" \
			   f"{f'{self._COORDINATE_JOINER}cycle' if self.cycle else ''};"

	def __repr__(self) -> str:
		return repr_string(self, TikZDirectedPath.coordinates, TikZDirectedPath.cycle, TikZDirectedPath.arrow_type)

class TikZCircle(TikZDefinesWriteable[TikZStyle]):
	"""
	:py:class:`TikZCircle` represents a standard TikZ circle, with a center coordinate, radius and style.

	:param coordinate: the center coordinate of the circle
	:param radius: the radius of the circle
	:param style: the style of the circle
	"""

	def __init__(self,
				 coordinate: Point[_N0, _N1],
				 radius: TikZValue,
				 style: TikZStyle = EMPTY_STYLE):
		super(TikZCircle, self).__init__((), (), (style,))

		self._coordinate = coordinate
		self._radius = radius
		self._style = style

	@property
	def coordinate(self) -> Point[_N0, _N1]:
		""" :return: the center coordinate of this circle """
		return self._coordinate

	@property
	def radius(self) -> TikZValue:
		""" :return: the radius of this circle """
		return self._radius

	@property
	def style(self) -> TikZStyle:
		""" :return: the style used by this circle """
		return self._style

	def __hash__(self) -> int:
		return hash((self._coordinate, self._radius, self._style))

	def __eq__(self, other) -> bool:
		return isinstance(other, TikZCircle) and self._coordinate == other._coordinate \
			   and self._radius == other._radius and self._style == other._style

	def to_tikz(self) -> str:
		return f"\\draw[{self._style.to_tikz()}] {self._coordinate.to_tikz()} circle ({self._radius});"

	def __repr__(self) -> str:
		return repr_string(self, TikZCircle.coordinate, TikZCircle.radius)
