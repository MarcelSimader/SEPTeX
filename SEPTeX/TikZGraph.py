"""
:Author: Marcel Simader
:Date: 08.07.2021

.. versionadded:: v0.3.0
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ IMPORTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from __future__ import annotations

from typing import Collection, Union, List

from SEPTeX.TikZBase import TikZStyle, TikZDefinesNamed
from SEPTeX.TikZ import TikZNode, TikZPath, TikZDirectedPath

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ CLASSES ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class TikZGraph(TikZDefinesNamed[TikZNode]):

	def __init__(self,
				 default_node_style: TikZStyle = TikZStyle(),
				 default_edge_style: TikZStyle = TikZStyle()):
		super(TikZGraph, self).__init__((), ("positioning",),
										styles=(default_node_style, default_edge_style),
										named_objs=())
		self._default_node_style = default_node_style
		self._default_edge_style = default_edge_style
		self._edges: List[TikZPath] = list()

	@property
	def edge_style(self):
		return self._default_edge_style

	@property
	def node_style(self):
		return self._default_node_style

	def add_node(self, *nodes: Union[TikZNode, Collection[TikZNode]]) -> None:
		for entry in nodes:
			if not isinstance(entry, Collection):
				entry = (entry,)
			for node in entry:
				if node.style.empty:
					node = TikZNode(node.coordinate, node.name, node.label, None, self._default_node_style)
				self.__register_named_object__(node)

	def add_edge(self, *edges: Union[TikZPath, Collection[TikZPath]]) -> None:
		for entry in edges:
			if not isinstance(entry, Collection):
				entry = (entry,)
			for edge in entry:
				if edge.style.empty:
					edge = TikZDirectedPath(edge.coordinates, edge.cycle, edge.label, self._default_edge_style,
											edge.arrow_type)
				self._edges.append(edge)

	def __str__(self) -> str:
		return ";\n".join([str(edge) for edge in self._edges])
