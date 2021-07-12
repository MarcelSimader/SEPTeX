"""
:Author: Marcel Simader
:Date: 12.07.2021

.. versionadded:: v0.2.0
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ IMPORTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from fractions import Fraction
from numbers import Number
from typing import Union, AnyStr, Any, Set, Tuple, List

from SEPModules.maths import AlgebraicStructure

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ FUNCTIONS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def vspace(length: Union[AnyStr, Number]) -> str:
	""" Inserts a vertical space of length ``length`` in the document. """
	return r"\vspace*{{{}}}".format(length)

def parentheses(text: Any) -> str:
	return r"\left( {} \right)".format(text)

def brackets(text: Any) -> str:
	return r"\left[ {} \right]".format(text)

def braces(text: Any) -> str:
	return r"\left\{{ {} \right\}}".format(text)

def tex_maths_string(s: Any) -> str:
	r"""
	Formats the given object in a LaTeX-friendly way for *math mode*.

    +----------------------+-------------------------------------------------------------------------------------+
    | Supertype            | Behaviour                                                                           |
    +======================+=====================================================================================+
    | Fraction             | print as LaTeX fraction                                                             |
    +----------------------+-------------------------------------------------------------------------------------+
    | Set                  | print set in curly braces, call :py:func:`tex_maths_string` on                      |
    |                      | each object of the set                                                              |
    +----------------------+-------------------------------------------------------------------------------------+
    | Tuple or List        | print list or tuple in square brackets, call :py:func:`tex_maths_string`            |
    |                      | on each object of the set except if the object is a string                          |
    +----------------------+-------------------------------------------------------------------------------------+
    | Algebraic Structure  | print the set using :py:func:`tex_maths_string`, and format the operator            |
    |                      | names as text, both set and operators are in parentheses                            |
    +----------------------+-------------------------------------------------------------------------------------+

    Default behaviour is to call the ``__str__`` method of an object.

	:param s: the object to format
	:return: a string which can be written to a LaTeX document in a math mode environment
	"""
	text_f = r"\text{{{}}}"

	formats = {
			Fraction          : lambda o: f"{'-' if o < 0 else ''}\\frac{{{abs(o.numerator)}}}{{{o.denominator}}}",
			Set               : lambda o: braces(", ".join([tex_maths_string(el) for el in s])),
			(Tuple, List,)    : lambda o: brackets(
					", ".join([text_f.format(el) if isinstance(el, str) else tex_maths_string(el) for el in s])),
			AlgebraicStructure: lambda o: parentheses(
					f"{tex_maths_string(o.elements)}, {', '.join([text_f.format(op.__name__) for op in o.binary_operators])}")
			}

	# if sub-type of dict key
	for super_type, format_function in formats.items():
		if isinstance(s, super_type):
			return format_function(s)

	# default case
	return str(s)
