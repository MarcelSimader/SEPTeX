"""
:Author: Marcel Simader
:Date: 12.07.2021

.. versionadded:: v0.2.0
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ IMPORTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
import math
import time
from fractions import Fraction
from itertools import combinations
from numbers import Number
from typing import Union, AnyStr, Any, Set, Tuple, List, Sequence, Literal, Optional

import random
from SEPModules.maths import AlgebraicStructure

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ PRIVATE FUNCTIONS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _generate_pseudo_unique_name(prefix: str, *hashes: Any, char_len: int = 6) -> str:
	# 6 bits for 64 chars
	bit_len = 6 * char_len
	bit_size = 2 ** bit_len - 1

	total_hash = hash((prefix, *hashes))
	random_component = time.monotonic_ns() + random.randint(0, bit_size)
	# clip lengths
	total_hash &= bit_size
	random_component &= bit_size
	# interweave bits
	final_bits = 0
	parity = 0
	for b in range(0, bit_len):
		selected_bit = 2 ** b
		final_bits |= (total_hash & selected_bit) if parity else (random_component & selected_bit)
		parity ^= 1

	# convert to chars
	chars = ("A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O", "P", "Q", "R", "S", "T", "U",
			 "V", "W", "X", "Y", "Z", "a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k", "l", "m", "n", "o", "p",
			 "q", "r", "s", "t", "u", "v", "w", "x", "y", "z", "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "-",
			 "_")
	assert len(chars) == 64
	assert bit_len % 6 == 0

	out_str = str()
	for b in range(0, char_len):
		selected_bits = (final_bits >> (b * 6)) & (2 ** 6 - 1)
		out_str += chars[selected_bits]

	return prefix + out_str

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ FUNCTIONS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def vspace(length: Union[AnyStr, Number]) -> str:
	""" Inserts a vertical space of length ``length`` in the document. """
	return r"\vspace*{{{}}}".format(length)

def parentheses(text: Any) -> str:
	r""" Puts ``text`` in parentheses like so: ``\left( text \right)``. """
	return r"\left( {} \right)".format(text)

def brackets(text: Any) -> str:
	r""" Puts ``text`` in brackets like so: ``\left[ text \right]``. """
	return r"\left[ {} \right]".format(text)

def braces(text: Any) -> str:
	r""" Puts ``text`` in braces like so: ``\left\{ text \right\}``. """
	return r"\left\{{ {} \right\}}".format(text)

def matrix(matr: Sequence[Sequence[Any]],
		   matrix_type: Literal["", "p", "b", "B"] = "",
		   labels: Optional[Sequence[Any]] = None,
		   tab_width: int = 4) -> str:
	"""
	Converts a nested sequence of any object to a math-mode compatible matrix. The sequence may not be empty and all nested
	sequences must be of equal length.

	The available options are ``""``, ``"p"``, ``"b"``, and ``"B"`` for ``matrix``, ``pmatrix`` (parentheses),
	``bmatrix`` (brackets), and ``Bmatrix`` (braces, requires ``amsmath``) respectively.

	:param matr: the nested sequence to convert to a matrix string
	:param matrix_type: which kind of matrix to create, either ``""``, ``"p"``, ``"b"``, or ``"B"``
	:param labels: an optional sequence of strings to label both the top row and first column, **can only be used for
		square matrices** and must be of equal length to the first and second dimensions
	:param tab_width: how wide a tab character should be considered to be in characters for formatting the string output

	:raise ValueError: if ``matr`` contains no elements, if nested sequences of ``matr`` are not all the same size, if
		the ``labels`` option is set for non-square matrices, if the ``labels`` sequence is not the same size as the first
		and second dimensions of ``matr``

	:return: the nested sequence as math-mode compatible matrix in string form
	"""
	dim_0 = len(matr)
	if dim_0 <= 0:
		raise ValueError("Matrix contains no elements")
	dim_1 = len(matr[0])
	if not all(dim_1 == len(x) for x in matr):
		raise ValueError(f"Expected nested collection of size ({dim_0}, {dim_1}), but received size "
						 f"({dim_0}, {[len(x) for x in matr]})")

	# with labels
	if labels is not None:
		if dim_0 != dim_1:
			raise ValueError(f"labels argument can only be used with square matrices, but "
							 f"received size ({dim_0, dim_1})")
		if len(labels) != dim_0:
			raise ValueError(f"Expected labels to be of length {dim_0}, but received {len(labels)}")

		# add labels
		edited_matr = [[tex_maths_string(s) for s in (labels[i], *matr[i])] for i in range(dim_0)]
		edited_matr.insert(0, [" ", *(tex_maths_string(s) for s in labels)])
		dim_0 += 1
		dim_1 += 1
	# without labels
	else:
		edited_matr = [[tex_maths_string(s) for s in m] for m in matr]

	# add spacing
	num_tabs_per_col = [int(math.ceil(
			max(abs(len(a) - len(b)) for a, b in combinations(edited_matr[:][i], r=2))
			/ tab_width))
			for i in range(dim_1)]

	# iterate over 2d array
	latex_str = list()
	for y in range(dim_0):
		row = (s + ("\t" * (num - (len(s) // tab_width))) for s, num in zip(edited_matr[y], num_tabs_per_col))
		latex_str.append(f"\t{' & '.join(row)}")

	# final string
	latex_str = " \\\\\n".join(latex_str)
	return f"\\begin{{{matrix_type}matrix}}\n{latex_str}\n\\end{{{matrix_type}matrix}}"

def p_matrix(matr: Sequence[Sequence[Any]], labels: Optional[Sequence[AnyStr]] = None, tab_width: int = 4) -> str:
	"""
	Parentheses alias for specifying a matrix type.

	..	seealso:: Function :py:func:`matrix` for details
	"""
	return matrix(matr, matrix_type="p", labels=labels, tab_width=tab_width)

def b_matrix(matr: Sequence[Sequence[Any]], labels: Optional[Sequence[AnyStr]] = None, tab_width: int = 4) -> str:
	"""
	Brackets alias for specifying a matrix type.

	..	seealso:: Function :py:func:`matrix` for details
	"""
	return matrix(matr, matrix_type="b", labels=labels, tab_width=tab_width)

def B_matrix(matr: Sequence[Sequence[Any]], labels: Optional[Sequence[AnyStr]] = None, tab_width: int = 4) -> str:
	"""
	Braces alias for specifying a matrix type.

	..	seealso:: Function :py:func:`matrix` for details
	"""
	return matrix(matr, matrix_type="B", labels=labels, tab_width=tab_width)

def tex_maths_string(s: Any) -> str:
	r"""
	Formats the given object in a LaTeX-friendly way for *math mode*.

    +----------------------+-------------------------------------------------------------------------------------+
    | ``cls``              | Behaviour if ``isinstance(s, cls)``                                                 |
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
