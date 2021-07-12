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
from fractions import Fraction
from inspect import getframeinfo, stack
from numbers import Number
from typing import Union, AnyStr, Tuple, List, final, Optional, NoReturn, Any, Set

from SEPModules.SEPPrinting import repr_string
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
	Formats the given object in a LaTeX-friendly way for **math mode**.

    +----------------------+-------------------------------------------------------------------------------------+
    | Supertype            | Behaviour                                                                           |
    +----------------------+-------------------------------------------------------------------------------------+
    | Fraction             | print as LaTeX fraction                                                             |
    +----------------------+-------------------------------------------------------------------------------------+
    | Set                  | print set in curly braces, call :py:func:`tex_maths_string` on                       |
    |                      | each object of the set                                                              |
    +----------------------+-------------------------------------------------------------------------------------+
    | Tuple or List        | print list or tuple in square brackets, call :py:func:`tex_maths_string`             |
    |                      | on each object of the set except if the object is a string                          |
    +----------------------+-------------------------------------------------------------------------------------+
    | Algebraic Structure  | print the set using :py:func:`tex_maths_string`, and format the operator             |
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

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ CLASSES ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@final
class TeXError(Exception):
	"""
	Exception class for the :py:mod:`SEPTeX` module.
	"""

	def __init__(self, msg: AnyStr, obj: Union[TeXHandler, TeXResource]):
		self.msg = msg
		self.obj = obj

	def __str__(self) -> str:
		return f"{self.msg} (raised from {repr(self.obj)})"

@final
class TeXHandler:
	r"""
	:py:class:`TeXHandler` aids as container for lines of text to be written to a document. This class can automatically
	apply a specific level of indentation and hard-wrap lines that are too long.

	..	note::

		The algorithm for the hard-wrap will only be applied when the :py:meth:`wrap_lines` method is called manually.
		The results of these calls will be stored in the instance. Furthermore, the algorithm will split up lines that
		are too long at available spaces. If no space is found, the line simply must exceed the given bounds.

	:param indent_level: the number of tab character to place at the beginning of each line
	:param line_wrap_length: keyword-only argument, when set to an int this value dictates how long a line can be before
		a pseudo soft-wrap is applied during the :py:meth:`write` operations of this instance
	"""

	def __init__(self, indent_level: int = 0, *, line_wrap_length: Optional[int] = None):
		self._data: List[Tuple[int, str]] = list()
		self._indent_level = indent_level
		self._line_wrap_length = line_wrap_length
		self._already_wrapped_lines = 0

	@property
	def data(self) -> Tuple[Tuple[int, str]]:
		""" :return: a tuple of strings where each string is exactly one line in the document """
		return tuple(self._data)

	@property
	def indent_level(self) -> int:
		""" :return: what the default amount of indentation for this handler should be """
		return self._indent_level

	@property
	def line_wrap_length(self) -> Optional[int]:
		"""
		:return: the number of characters before a line is split into two using a soft-wrap, **this means that in the handler,
			the line will still only have one entry but contain the newline character**
		"""
		return self._line_wrap_length

	def wrap_lines(self, *, tab_width: int = 4, hanging_indent: bool = True) -> None:
		"""
		Wraps the lines of this instance according to :py:attr:`line_wrap_length`.

		:param tab_width: how wide (in characters) to consider a tab character (``\t``)
		:param hanging_indent: whether or not to indent wrapped lines by one extra tab
		"""
		if self._line_wrap_length is None:
			return

		last_line_wrapped = False
		data_index = self._already_wrapped_lines
		while data_index < len(self._data):
			tabs, tmp_s = self._data[data_index]
			curr_line_wrap_length = self._line_wrap_length - tabs * tab_width

			# search if we are past the limit
			if len(tmp_s) >= curr_line_wrap_length:
				break_pos = tmp_s.find(" ", curr_line_wrap_length)

				if break_pos != -1:
					# determine comment newline
					comment = "% " if "%" in tmp_s[:break_pos] else ""

					# +1 to break *after* space
					# split entry and remove leading whitespace from right
					left = self._data[data_index][1][:break_pos + 1]
					right = comment + self._data[data_index][1][break_pos + 1:].lstrip()

					# insert left and right
					hanging_tab = 0 if not hanging_indent or last_line_wrapped else 1
					self._data[data_index] = (tabs, left)
					self._data.insert(data_index + 1, (tabs + hanging_tab, right))

					last_line_wrapped = True
				else:
					last_line_wrapped = False
			else:
				last_line_wrapped = False
			data_index += 1

		# mark these lines as wrapped
		self._already_wrapped_lines = data_index

	def write(self, s: Union[AnyStr, TeXHandler]) -> None:
		"""
		Write string ``s`` to the handler.

		If ``s`` is a string or bytes object, this function will perform some processing. If ``s`` is a :py:class:`LaTeXHandler`
		this function will extend the data of this instance with the given handler, and *add the required number of tabs
		of this instance to the tabs already accumulated in the data tuple of the given handler!*

		:param s: the string to write, can be any string of any length including line breaks
		"""
		# ++++ if handler, write and RETURN ++++
		if isinstance(s, TeXHandler):
			self._data.extend([(tabs + self._indent_level, data) for tabs, data in s._data])
			return

		# ++++ if any other type, write normal way ++++
		# preprocess
		s_split = [(self._indent_level, sub.replace("\n", "")) for sub in s.split("\n")]
		# add to data
		self._data.extend(s_split)

	def newline(self) -> None:
		""" Write an empty line. """
		self.write("")

	def readline(self, offset: int = 0, size: int = 1) -> Tuple[str, ...]:
		"""
		Read ``size`` lines from this document, starting at ``offset``.

		:param offset: which line, starting at 0, should be the first to be read
		:param size: how many lines to read, if the number of lines to read past the offset is larger than the number of
			available lines this function will return the remaining lines
		:return: the lines to be read as tuple of tuples, where each tuple entry contains the number of tabs to be added
			to the line and the line contents themselves
		:raise ValueError: if size is negative
		"""
		if size < 0 or offset < 0:
			raise ValueError(f"size and offset parameters must be bigger than or equal to 0, received {size}")
		if offset > len(self):
			raise ValueError(f"offset cannot be bigger than number of lines in handler instance")
		offset_from = offset
		offset_to = min(offset + size, len(self))
		return tuple(map(lambda e: e[1], self._data[offset_from:offset_to]))

	def __len__(self) -> int:
		""" :return: the number of lines stored in the :py:attr:`data` attribute """
		return len(self._data)

	def __str__(self) -> str:
		self.wrap_lines()
		return "\n".join([("\t" * tabs) + data for tabs, data in self._data])

	def __repr__(self) -> str:
		return repr_string(self, TeXHandler.data, TeXHandler.indent_level, TeXHandler.line_wrap_length)

class TeXResource(abc.ABC):
	"""
	Abstract base class for marking a class as having an open and closed state, along with text data of some sort. This
	class requires :py:meth:`__str__` to be implemented to provide the contents of the handlers to any other caller.

	In addition to the open and closed states, one can configure the resource to allow multiple openings. The default
	behaviour is to throw an exception if the resource is opened a second time. The opening and closing is implemented as
	context manager, with :py:meth:`__enter__` triggering an opening and :py:meth:`__exit__` triggering a closing. The
	private helper methods :py:meth:`__require_closed__`, :py:meth:`__require_open__`, :py:meth:`__require_virgin__`, and
	:py:meth:`__require_used__` are provided to check these states.
	"""

	@staticmethod
	@final
	def __get_context__(n: int = 1) -> str:
		"""
		:return: the name of the function which called this function, ``n`` frames above the scope of the caller of this function.
		"""
		try:
			frame = getframeinfo(stack()[n + 1][0])
			return frame.function
		finally:
			del frame

	def __init__(self, *, can_reopen=False):
		self._open = False
		self._open_counter = 0
		self._can_reopen = can_reopen

	@property
	def open(self) -> bool:
		return self._open

	def __enter__(self) -> None:
		if not self._can_reopen and self._open_counter > 0:
			raise TeXError(f"Cannot open the {self.__class__.__name__} object more than once", self)
		self._open = True
		self._open_counter += 1

	def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
		self._open = False
		return exc_val is None

	@final
	def __require_state__(self, state_name: str, frame_depth: int = 1) -> NoReturn:
		raise TeXError(
				f"The {self.__class__.__name__} object must {state_name} before accessing "
				f"'{self.__get_context__(n=frame_depth + 1)}'",
				self)

	@final
	def __require_closed__(self, frame_depth: int = 1) -> None:
		"""
		Requires a resource to be closed.

		:param frame_depth: how many stack frames to go backwards in order to retrieve the name of the function which
			represents the public API call which caused the error

		:raise LaTeXError: if the resource is open when this function is called
		"""
		if self._open:
			self.__require_state__("be closed", frame_depth)

	@final
	def __require_open__(self, frame_depth: int = 1) -> None:
		"""
		Requires a resource to be opened.

		:param frame_depth: how many stack frames to go backwards in order to retrieve the name of the function which
			represents the public API call which caused the error

		:raise LaTeXError: if the resource is closed when this function is called
		"""
		if not self._open:
			self.__require_state__("be open", frame_depth)

	@final
	def __require_virgin__(self, frame_depth: int = 1) -> None:
		"""
		Requires a resource to have never been opened.

		:param frame_depth: how many stack frames to go backwards in order to retrieve the name of the function which
			represents the public API call which caused the error

		:raise LaTeXError: if the resource has been opened once before when this function is called
		"""
		if self._open_counter > 0:
			self.__require_state__("not have been opened at any point", frame_depth)

	@final
	def __require_used__(self, frame_depth: int = 1) -> None:
		"""
		Requires a resource to have been opened *and* closed at least once in the past.

		:param frame_depth: how many stack frames to go backwards in order to retrieve the name of the function which
			represents the public API call which caused the error

		:raise LaTeXError: if the resource has not been opened and closed at least once in the past when this function is
			called
		"""
		if self._open_counter <= 0 or self._open:
			self.__require_state__("have been opened and closed at least once", frame_depth)

	@abc.abstractmethod
	def __str__(self) -> str:
		raise NotImplementedError("Subclasses of TeXResource must implement this method")
