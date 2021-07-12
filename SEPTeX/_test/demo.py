"""
:Author: Marcel Simader
:Date: 29.06.2021

.. versionadded:: v0.1.0
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ IMPORTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
from SEPModules.maths import Monoid, Field

from SEPTeX.LaTeX import *
from SEPTeX.TeXBase import *
from SEPTeX.TikZ import *
from SEPTeX.TikZBase import *
from SEPTeX.TikZGraph import *

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ DEMO ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def demo1():
	document: LaTeXDocument
	pre: TeXHandler
	body: TeXHandler
	with LaTeXDocument("tmp/demo1.tex",
					   title="Demo Document No. 1",
					   subtitle="for the SEPTeX module",
					   author="Marcel Simader",
					   show_page_numbers=False,
					   line_wrap_length=100) as (document, pre, body):
		# ++++ PAGE 1 ++++

		pre.write(r"% This is indeed a comment in the preamble")
		body.write(
				r'\noindent This is some text, and it contains a potentially % confusing comment for the "soft" line wrap % functionality')
		body.newline()
		body.write(r"And this is some text that goes on" + (" and on" * 20) + r"\ldots")

		body.write(r"This is a \LaTeX\ sentence -- wow!")

		s = MathsEnvironment(document, "gather", star=True)
		with s as eq:
			eq.write([1, Fraction(1, 3), 3, "abc"])
			eq.write({1, Fraction(-3, 5), Fraction(-2, 7), "abc"})

			eq.newline()

			def add(a, b): return a + b

			def multiply(a, b): return a * b

			eq.write(Monoid({1, 2, 3, Fraction(-9, 2)}, add))
			eq.write(Field({1, 2, 3, Fraction(-9, 2)}, add, multiply))

		document.page_break()
		# ++++ PAGE 2 ++++

		colors = TikZColor.DEFAULT_COLORS

		with Figure(document, caption="Captions, Figures, and the Default Colors.") as fig, \
				Center(fig) as center, \
				TikZPicture(center) as tikz:
			tikz.define_named_object(*colors)

			for i, color in enumerate(colors):
				with TikZScope(tikz, style=TikZStyle(scale=0.4 + (0.7 * (i / len(colors))))) as scope:
					path = TikZPath((Point(0, i), Point(4, 4 + i), Point(0, 4 + i), Point(-4, 2 + i)),
									cycle=True,
									style=TikZStyle(fill=color,
													color=TikZColor.ALMOST_BLACK,
													line_width=f"{0.5 + i / len(colors)}mm")
									)
					scope.write(path)

		document.page_break()
		# ++++ PAGE 3 ++++

		with Figure(document, caption="The arrow styles.") as fig, \
				Center(fig) as center, \
				TikZPicture(center) as tikz:
			for i, arrow_style in enumerate(TikZArrow):
				with TikZScope(tikz, style=TikZStyle(shift=(0, -i * 0.45), scale=2)) as scope:
					scope.write(
							TikZDirectedPath((Point(0, 0), Point(1 + (2 * i / len(TikZArrow)), 0.75), Point(4, 0)),
											 style=TikZStyle(line_width="0.85mm"),
											 arrow_type=arrow_style))

		document.page_break()
		# ++++ PAGE 4 ++++

		num, rad = 12, 5
		circ_nodes = list()
		for i in range(num):
			j = 2 * math.pi * i / num
			x, y = rad * math.sin(j), rad * math.cos(j)
			circ_nodes.append(TikZNode(Point(x, y), label=str(i), name=f"x{i}", style=TikZStyle(circle=True)))

		with Figure(document, caption="Nodes, and directed paths -- wow!") as fig, \
				Center(fig) as center, \
				TikZPicture(center) as tikz:
			for i in range(num):
				i = i % num
				tikz.write(TikZDirectedPath((circ_nodes[i - 1], circ_nodes[i]),
											style=TikZStyle(bend_left=15, line_width="0.3mm", dashed=True),
											arrow_type=TikZArrow.RIGHT_LATEX_PRIME))
			tikz.write(TikZDirectedPath((circ_nodes[0], circ_nodes[num // 2 + 1]),
										arrow_type=TikZArrow.RIGHT_CIRC))

		document.page_break()
		# ++++ PAGE 5 ++++

		num, rad = 24, 6
		pol_circ_nodes = list()
		for i in range(num):
			angle = -(i * 360 / num) + 90
			pol_circ_nodes.append(
					TikZNode(PolarPoint(angle, rad), label=f"$n_{{{i}}}$", name=f"y{i}", style=TikZStyle(circle=True))
					)

		with Figure(document, caption="Graphs!") as fig, \
				Center(fig) as center, \
				TikZPicture(center) as tikz:
			graph = TikZGraph(TikZStyle(), TikZStyle(line_width="0.25mm"))

			origin = TikZNode(Point(0, 0), label=r"Math can go here: \\$\sum_{n=0}^{\infty} 3x^n$", name="o",
							  style=TikZStyle({"double": True}, align="center", circle=True,
											  fill=TikZColor.ALMOST_WHITE))

			graph.add_node(pol_circ_nodes, origin)
			graph.add_edge(TikZDirectedPath((pol_circ_nodes[0], origin), arrow_type=TikZArrow.LEFT))

			sec_nodes = list()
			for i in range(1, num, num // 12):
				p = PolarPoint(-(i / num) * 360 - 90, 2)
				n = TikZNode(p, name=f"l{i}", label=f"$\\scriptstyle \\phi = {p.angle}$",
							 style=TikZStyle(circle=True), relative_to=pol_circ_nodes[i])
				sec_nodes.append(n)
				graph.add_node(n)

			ratio = num // len(sec_nodes)
			for i in range(len(sec_nodes)):
				o1 = (i * ratio) % num
				o2 = (o1 + ratio) % num
				graph.add_edge(TikZDirectedPath((sec_nodes[i], pol_circ_nodes[o1]), arrow_type=TikZArrow.LEFT))
				graph.add_edge(TikZDirectedPath((sec_nodes[i], pol_circ_nodes[o2]), arrow_type=TikZArrow.RIGHT))

			loop_dirs = (graph.edge_style & TikZStyle({"loop above": True}),
						 graph.edge_style & TikZStyle({"loop right": True}),
						 graph.edge_style & TikZStyle({"loop below": True}),
						 graph.edge_style & TikZStyle({"loop left": True}))
			for i in range(num):
				o = (i + 1) % num
				graph.add_edge(TikZDirectedPath((pol_circ_nodes[i], pol_circ_nodes[o]), arrow_type=TikZArrow.LEFT))
				if i % 2 == 0:
					graph.add_edge(TikZDirectedPath((pol_circ_nodes[i], pol_circ_nodes[i]),
													arrow_type=TikZArrow.RIGHT,
													style=loop_dirs[int(i * 4 // num)]
													))

			tikz.write(graph)

	document.to_pdf(out_file_path="tmp/demo1.pdf", overwrite=True)

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ MAIN ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

if __name__ == "__main__":
	demo1()
