"""
:Author: Marcel Simader
:Date: 08.07.2021

.. versionadded:: v0.3.0
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ IMPORTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from __future__ import annotations

import abc
import math
from typing import List, Tuple, Optional, Set, Dict, Union, TypeVar, Final, Iterable, AnyStr, Protocol, \
	runtime_checkable

from SEPModules import debug

from SEPTeX.TikZ import TikZNode, TikZPath, TikZDirectedPath, TikZLabel, Point, PolarPoint
from SEPTeX.TikZBase import TikZStyle, TikZDefinesWriteable, TikZArrow, EMPTY_STYLE

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ FUNCTIONS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _not_implemented(name: str) -> NotImplementedError:
	""" Return a ``NotImplementedError`` to raise if a method is missing. """
	return NotImplementedError(f"Required method {name!r} not implemented")

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ CLASSES ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ PROTOCOLS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@runtime_checkable
class SupportsNameLabel(Protocol[AnyStr]):
	""" Protocol for checking whether an object has a :py:attr:`name`, :py:attr:`label`, and :py:attr:`children` property. """

	@property
	@abc.abstractmethod
	def name(self) -> AnyStr:
		raise _not_implemented("name")

	@property
	@abc.abstractmethod
	def label(self) -> AnyStr:
		raise _not_implemented("label")

	@property
	@abc.abstractmethod
	def children(self) -> Iterable[Optional[SupportsNameLabel]]:
		raise _not_implemented("children")

_N: Final = TypeVar("_N", bound=SupportsNameLabel)
""" 
Generic type variable for the :py:mod:`TikZGraph` module for objects which implement 
the :py:class:`SupportsNameLabel` protocol. 
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ GRAPH ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TikZGraph(TikZDefinesWriteable[Union[TikZNode, TikZPath]]):

	def __init__(self,
				 default_node_style: TikZStyle = EMPTY_STYLE,
				 default_edge_style: TikZStyle = EMPTY_STYLE):
		super(TikZGraph, self).__init__((), ("positioning",), (default_node_style, default_edge_style))

		self._default_node_style = default_node_style
		self._default_edge_style = default_edge_style
		self._nodes: Set[TikZNode] = set()
		self._edges: Dict[Tuple[TikZNode, TikZNode], List[TikZPath]] = dict()

	@staticmethod
	def from_ext_graph(root_node: _N,
					   origin: Point = Point(0, 0),
					   radius: float = 2.0,
					   radius_decay_factor: float = 3,
					   default_node_style: TikZStyle = EMPTY_STYLE,
					   default_edge_style: TikZStyle = EMPTY_STYLE) -> TikZGraph:
		graph = TikZGraph(default_node_style, default_edge_style)
		visited_objs: Dict[_N, TikZNode] = dict()

		def __traverse__(current_obj: _N, coord: Point, rad: float, angle: float, angle_reduction: float,
						 parent_node: Optional[TikZNode], number: int) -> TikZNode:
			# return saved
			if current_obj in visited_objs:
				return visited_objs[current_obj]

			# try to access properties
			try:
				# construct tiz node
				node = TikZNode(coord, f"{current_obj.name}-{number}", current_obj.label, relative_to=parent_node)
				visited_objs[current_obj] = node
				# get child objects
				next_objs = tuple(o for o in current_obj.children if o is not None)
			except AttributeError as e:
				raise AttributeError(f"Node object {current_obj!r} does not support one of: 'name', 'label', "
									 f"or 'children'") from e

			# recursively call in circle
			d_angle = 0 if len(next_objs) == 0 else (360 - angle_reduction) / len(next_objs)
			for i, obj in enumerate(next_objs):
				new_angle = (180 + angle + (0.5 * (d_angle + angle_reduction))) + (i * d_angle)
				next_coord = PolarPoint(new_angle, rad)
				graph.add_edge(node, __traverse__(obj, next_coord, rad / radius_decay_factor,
												  new_angle, 180, node, number + 1))

			return node

		# traverse and return final graph
		__traverse__(root_node, origin, radius, 0, 0, None, 0)
		return graph

	@property
	def default_node_style(self) -> TikZStyle:
		return self._default_node_style

	@property
	def default_edge_style(self) -> TikZStyle:
		return self._default_edge_style

	@property
	def paths(self) -> Tuple[TikZPath]:
		return tuple(p for p_list in self._edges.values() for p in p_list)

	@property
	def nodes(self) -> Tuple[TikZNode]:
		return tuple(self._nodes)

	@property
	def edges(self) -> Dict[Tuple[TikZNode, TikZNode], List[TikZPath]]:
		return dict(self._edges)

	def register_node(self, *node: TikZNode, dynamic_style: bool = True) -> None:
		for n in node:
			if dynamic_style and not self._default_node_style.empty:
				n = TikZNode(n.raw_coordinate, n.raw_name, n.label, n.relative_to, self._default_node_style + n.style)

			# register with super
			self.__register_writeable_object__(n)
			# register with self
			self._nodes.add(n)

	def register_path(self, *path: TikZPath, dynamic_style: bool = True) -> None:
		for p in path:
			if dynamic_style and not self._default_edge_style.empty:
				p = TikZDirectedPath(p.coordinates, p.cycle, self._default_edge_style + p.style, p.arrow_type)

			# register with self
			self.register_node(*(n for n in p.coordinates if isinstance(n, TikZNode)), dynamic_style=dynamic_style)
			# register with super
			self.__register_writeable_object__(p)

			# define edges
			for r in p.node_relations:
				if r in self._edges:
					self._edges[r].append(p)
				else:
					self._edges[r] = [p]

	def add_edge(self,
				 node0: TikZNode,
				 node1: TikZNode,
				 arrow_type: TikZArrow = TikZArrow.LINE,
				 label: Optional[TikZLabel] = None,
				 *,
				 style: TikZStyle = EMPTY_STYLE,
				 dynamic_style: bool = True) -> None:
		if dynamic_style:
			# set up vars
			related_edges = [e for r in ((node0, node1), (node1, node0)) for e in self._edges.get(r, [])]
			style_addition = self._default_edge_style

			# handle self looping
			if node0 == node1 and not any(l in style for l in ("loop above", "loop below", "loop left", "loop right")):
				added = False
				for l in ("loop above", "loop below", "loop left", "loop right"):
					if not added and all(l not in e.style for e in related_edges):
						style_addition += TikZStyle({l: True})
						added = True
				if not added:
					style_addition += TikZStyle(loop_above=True)

			# handle multiple edges on same nodes
			elif (node0, node1) in self._edges or (node1, node0) in self._edges:
				num_left = len([True for e in related_edges if "bend left" in e.style])
				num_right = len([True for e in related_edges if "bend right" in e.style])
				if num_left + num_right != len(related_edges):
					if num_left == 0:
						style_addition += TikZStyle(bend_left=True)
					elif num_right == 0:
						style_addition += TikZStyle(bend_right=True)
					else:
						left = num_left <= num_right
						debug(num_left, num_right)

						max_bend = 0
						for s in map(lambda e: e.style, related_edges):
							try:
								max_bend = max(max_bend, float(s.bend_left if left else s.bend_right))
							except (TypeError, ValueError):
								pass
						style_addition += TikZStyle({"bend left" if left else "bend right": max_bend + 15})

			style = style + style_addition

		# register
		path = TikZDirectedPath((node0, node1) if label is None else (node0, label, node1),
								cycle=False, style=style, arrow_type=arrow_type)
		self.register_path(path)

	def __node_grid__(self,
					  width: int, height: int,
					  name_template: AnyStr, label_template: AnyStr,
					  origin: Point = Point(0, 0), spacing: Tuple[float, float] = (2, 2),
					  *,
					  flat_list: bool = False,
					  register_nodes: bool = True) -> Union[Tuple[TikZNode, ...], Tuple[Tuple[TikZNode, ...], ...]]:
		nodes = list()
		num = 0
		for x in range(width):
			col = list()
			for y in range(height):
				col.append(TikZNode(origin + (spacing[0] * x, -spacing[1] * y),
									name_template.format(x, y, x=x, y=y, i=num, n=num, num=num),
									label_template.format(x, y, x=x, y=y, i=num, n=num, num=num)))
				num += 1
			nodes.append(tuple(col))
		# registering and flat list
		if register_nodes or flat_list:
			flat_nodes = tuple(n for col in nodes for n in col)

			if register_nodes:
				self.register_node(*flat_nodes)
			if flat_list:
				return flat_nodes

		# nested list
		return tuple(nodes)

	def node_grid_flat(self,
					   width: int, height: int,
					   name_template: AnyStr, label_template: AnyStr,
					   origin: Point = Point(0, 0), spacing: Tuple[float, float] = (2, 2),
					   *,
					   register_nodes: bool = True) -> Tuple[TikZNode, ...]:
		return self.__node_grid__(width, height, name_template, label_template, origin, spacing,
								  flat_list=True, register_nodes=register_nodes)

	def node_grid_nested(self,
						 width: int, height: int,
						 name_template: AnyStr, label_template: AnyStr,
						 origin: Point = Point(0, 0), spacing: Tuple[float, float] = (2, 2),
						 *,
						 register_nodes: bool = True) -> Tuple[Tuple[TikZNode, ...], ...]:
		return self.__node_grid__(width, height, name_template, label_template, origin, spacing,
								  flat_list=False, register_nodes=register_nodes)

	def node_oval(self,
				  width: float, height: float,
				  num_nodes: int,
				  name_template: AnyStr, label_template: AnyStr,
				  origin: Point = Point(0, 0),
				  *,
				  register_nodes: bool = True) -> Tuple[TikZNode, ...]:
		d_angle = 2.0 * math.pi / num_nodes
		nodes = list()
		for i in range(0, num_nodes):
			angle = i * d_angle
			r_angle = round(angle, 3)
			nodes.append(TikZNode(origin + (width * math.cos(angle), height * math.sin(angle)),
								  name_template.format(i, i=i, n=i, num=i, r=r_angle, theta=r_angle),
								  label_template.format(i, i=i, n=i, num=i, r=r_angle, theta=r_angle)))

		# register and return
		if register_nodes:
			self.register_node(*nodes)
		return tuple(nodes)

	def node_circle(self,
					radius: float,
					num_nodes: int,
					name_template: AnyStr, label_template: AnyStr,
					origin: Point = Point(0, 0),
					*,
					register_nodes: bool = True) -> Tuple[TikZNode, ...]:
		return self.node_oval(radius, radius, num_nodes, name_template, label_template, origin,
							  register_nodes=register_nodes)

	def __hash__(self) -> int:
		return hash((self._edges, self._default_edge_style, self._default_node_style))

	def __eq__(self, other) -> bool:
		return isinstance(other, TikZGraph) and self._edges == other._edges \
			   and self._default_node_style == other._default_edge_style \
			   and self._default_node_style == other._default_node_style

	def to_tikz(self) -> str:
		return "\n".join(p.to_tikz() for p in self.paths)
