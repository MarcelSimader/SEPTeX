..  Author Marcel Simader
	Date 12.07.2021

TikZBase
==========================

..  automodule:: SEPTeX.TikZBase

..	autodata:: SEPTeX.TikZBase.TikZValue

TikZWriteable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..	autoclass:: SEPTeX.TikZBase.TikZWriteable
	:special-members: __register_required_package__, __register_required_tikz_library__, __hash__, __eq__
	:members:

TikZNamed
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..	autoclass:: SEPTeX.TikZBase.TikZNamed
	:members:

TikZDefinesWriteable
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..	autoclass:: SEPTeX.TikZBase.TikZDefinesWriteable
	:special-members: __register_writeable_object__
	:members:

TikZColor
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..	sidebar:: Color Constants

	..	data:: 	WHITE
				ALMOST_WHITE
				LIGHT_GRAY
				DARK_GRAY
				ALMOST_BLACK
				BLACK
				RED
				ORANGE
				YELLOW
				GREEN
				LIGHT_BLUE
				DARK_BLUE
				PURPLE
				MAGENTA
				PINK
				ROSE

			These constants are provided as default colors.

..	autoclass:: SEPTeX.TikZBase.TikZColor
	:members:

TikZArrowDirection
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..	autoclass:: SEPTeX.TikZBase.TikZArrowDirection

TikZArrow
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..	autoclass:: SEPTeX.TikZBase.TikZArrow
	:members:

		..	data:: 	LINE
					LEFT
					RIGHT
					LEFT_RIGHT
					IN_LEFT
					IN_RIGHT
					IN_LEFT_RIGHT
					LEFT_STUMP
					RIGHT_STUMP
					LEFT_RIGHT_STUMP
					LEFT_LATEX
					RIGHT_LATEX
					LEFT_RIGHT_LATEX
					LEFT_LATEX_PRIME
					RIGHT_LATEX_PRIME
					LEFT_RIGHT_LATEX_PRIME
					LEFT_CIRC
					RIGHT_CIRC
					LEFT_RIGHT_CIRC

				The different arrow head types. These can be extended arbitrarily.

TikZStyle
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..	autoclass:: SEPTeX.TikZBase.TikZStyle
	:members:

TikZPicture
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..	autoclass:: SEPTeX.TikZBase.TikZPicture
	:members:

TikZScope
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

..	autoclass:: SEPTeX.TikZBase.TikZScope
	:members:
