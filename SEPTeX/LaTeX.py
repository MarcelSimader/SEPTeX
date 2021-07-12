"""
:Author: Marcel Simader
:Date: 29.06.2021

.. versionadded:: v0.1.0
"""

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ IMPORTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

from __future__ import annotations

import inspect
import os
import shutil
from os import PathLike
from subprocess import run
from typing import Union, AnyStr, Tuple, List, Final, Collection, final, Literal, Any, Optional

from SEPTeX.TeXBase import TeXResource, TeXHandler, TeXError
from SEPTeX.TeXUtils import tex_maths_string

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ DOCUMENT AND ENVIRONMENTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class LaTeXDocument(TeXResource):
	"""
	:py:class:`LaTeXDocument` represents a LaTeX document that can be written to in a similar fashion as a text file. To
	do so, one must use the context manager of this object or retrieve the file path to write to it directly. The context
	manager will return three objects: the created document itself, the handler for writing to the preamble, and the
	handler for writing to the body of the document.

	Example usage with the context manager: ::

		with LaTeXDocument("abc.tex") as (latex_document, pre, body):
			latex_document.use_package("abc123", "cde456")
			body.write(r"This is some \LaTeX.")

	For extensions to the functionality of this class, see :py:class:`LaTeXEnvironment` as base class.

	..	warning::

		The data stored in and added to this :py:class:`LaTeXDocument` instance is only saved once the context manager
		is closed!

	:param path: the path to the main ``.tex`` file
	:param document_class: the name of the document class to include at the start of the document
	:param document_options: the options to pass to the chosen document class
	:param default_packages: the packages to include right at the beginning of initialization
	:param title: the title of the document
	:param subtitle: the subtitle of the document, is ignored unless ``title`` is not ``None``
	:param author: the author of the document
	:param show_date: keyword-only argument, determines whether or not to include a date in the title
	:param show_page_numbers: keyword-only argument, determines whether or not to show page numbers on all pages
	:param line_wrap_length: keyword-only argument, if set to an int this value will dictate how long a line can be
		before a pseudo soft-wrap is applied (see :py:class:`LaTeXHandler` for details)

	"""

	# cleandoc to remove leading whitespace of multiline string literal
	LaTeXTemplate: Final = inspect.cleandoc(
			r"""
			\documentclass[{}]{{{}}}
			
			% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
			% ~~~~~~~~~~~~~~~ PACKAGES ~~~~~~~~~~~~~~~
			% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
			
			{}
			
			% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
			% ~~~~~~~~~~~~~~~ PREAMBLE ~~~~~~~~~~~~~~~
			% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
			
			{}
			
			% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
			% ~~~~~~~~~~~~~~~ BODY ~~~~~~~~~~~~~~~
			% ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
			
			\begin{{document}}
			{}
			\end{{document}}
			"""
			)

	def __init__(self,
				 path: Union[AnyStr, PathLike],
				 document_class: AnyStr = "article",
				 document_options: AnyStr = "a4paper, 12pt",
				 default_packages: Collection[AnyStr] = ("amsmath",),
				 title: Optional[AnyStr] = None,
				 subtitle: Optional[AnyStr] = None,
				 author: Optional[AnyStr] = None,
				 *,
				 show_date: bool = False,
				 show_page_numbers: bool = False,
				 line_wrap_length: Optional[int] = None):
		super(LaTeXDocument, self).__init__()

		self._path = path
		self._document_class = document_class
		self._document_options = document_options
		self._title = title
		self._subtitle = subtitle
		self._author = author
		self._show_date = show_date
		self._show_page_numbers = show_page_numbers

		# set up handlers
		self._definitions = TeXHandler(indent_level=0)
		self._preamble = TeXHandler(indent_level=0, line_wrap_length=line_wrap_length)
		self._body = TeXHandler(indent_level=1, line_wrap_length=line_wrap_length)

		# misc setup
		self._has_title = self._title is not None or self._author is not None
		self._definition_list: List[Tuple[AnyStr, AnyStr]] = list()
		if not self._path.endswith(".tex"):
			self._path += ".tex"

		# default packages
		self.use_package(*default_packages)

	@property
	def path(self) -> PathLike:
		""" :return: the path of the ``.tex`` file that is to be written """
		return os.path.abspath(self._path)

	@property
	def successfully_saved_tex(self) -> bool:
		""" :return: whether or not this LaTeX document has been successfully saved to its ``.tex`` :py:attr:`path` """
		return self._open_counter > 0 and not self._open and os.path.isfile(self.path)

	@property
	def preamble(self) -> TeXHandler:
		""" :raise TeXError: if the document has not been opened """
		self.__require_open__()
		return self._preamble

	@property
	def body(self) -> TeXHandler:
		""" :raise TeXError: if the document has not been opened """
		self.__require_open__()
		return self._body

	@property
	def document_class(self) -> AnyStr:
		return self._document_class

	@property
	def document_options(self) -> AnyStr:
		return self._document_options

	@property
	def definitions(self) -> Tuple[Tuple[AnyStr, AnyStr]]:
		"""
		:return: a tuple of tuples of the definitions already placed in this instance, one entry consists of a definition
			key (e.g. "usepackage"), and a definition value (e.g. "amsmath")
		"""
		return tuple(self._definition_list)

	@property
	def line_wrap_length(self) -> Optional[int]:
		""" :return: the line wrap length of the body, see :py:attr:`.TeXHandler.line_wrap_length` for details """
		return self._body.line_wrap_length

	@property
	def title(self) -> Optional[AnyStr]:
		return self._title

	@property
	def subtitle(self) -> Optional[AnyStr]:
		return self._subtitle

	@property
	def author(self) -> Optional[AnyStr]:
		return self._author

	@property
	def show_date(self) -> bool:
		return self._show_date

	@property
	def show_page_numbers(self) -> bool:
		return self._show_page_numbers

	def __fspath__(self) -> bytes:
		return str(self.path).encode("utf_8")

	def __inclusion_statement__(self, *s: AnyStr, definition_text: AnyStr) -> None:
		"""
		Include a definition statement in this document. This function checks the list of already included definitions to
		avoid duplicates.

		:param s: the name or names of the definitions to include
		:param definition_text: the text to use for the definition statement
		"""
		if not isinstance(s, Tuple):
			s = (s,)
		for p in s:
			if (definition_text, p) not in self._definition_list:
				self._definition_list.append((definition_text, p))
				self._definitions.write(f"\\{definition_text}{{{p}}}")

	def use_package(self, *package: AnyStr) -> None:
		"""
		Include a ``usepackage`` statement in this document. This function checks the list of already included packages to
		avoid duplicates.

		:param package: the name or names of the package to include
		"""
		self.__inclusion_statement__(*package, definition_text="usepackage")

	def use_tikz_library(self, *library: AnyStr) -> None:
		"""
		Include a ``usetikzlibrary`` statement in this document. This function checks the list of already included libraries
		to avoid duplicates.

		:param library: the name or names of the TikZ library to include
		"""
		self.__inclusion_statement__(*library, definition_text="usetikzlibrary")

	def page_break(self) -> None:
		""" Inserts a page break. """
		self.body.write(r"\newpage")
		self.body.newline()

	def __init_document__(self):
		"""
		This function should be called when the context manager of a document is entered or if the super call of a subclass
		has skipped this class in the inheritance chain. It sets up basic things like the page numbering and titles.
		"""
		# write title
		if self._has_title:
			self._body.write(r"\maketitle")
			self._body.newline()
			if self._title is not None:
				self.use_package("relsize")
				self._preamble.write(f"\\title{{{self._title}"
									 + (r"}"
										if self._subtitle is None else
										f"\\\\[0.4em]\\smaller{{{self._subtitle}}}}}"))
			if self._author is not None:
				self._preamble.write(f"\\author{{{self._author}}}")
			if not self._show_date:
				self._preamble.write(r"\date{}")

		# page numbers
		if not self._show_page_numbers:
			self._preamble.write(r"\pagenumbering{gobble}")

	def __enter__(self) -> Tuple[LaTeXDocument, TeXHandler, TeXHandler]:
		super(LaTeXDocument, self).__enter__()
		self.__init_document__()
		return self, self._preamble, self._body

	def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
		# super call!
		_exit = super(LaTeXDocument, self).__exit__

		# if error, do not write document
		if exc_val is not None:
			return _exit(exc_type, exc_val, exc_tb)

		# no error, try to write file
		file = None
		try:
			# write to actual file
			file = open(self.path, "w")
			file.write(str(self))
		except (TeXError, OSError, IOError) as e:
			raise TeXError(f"Error while writing to '.tex' file", self) from e
		finally:
			if file is not None:
				file.close()
			return _exit(exc_type, exc_val, exc_tb)

	def to_pdf(self,
			   out_file_path: Union[PathLike, AnyStr],
			   overwrite: bool = False,
			   delete_aux_files: bool = True,
			   engine: Literal["pdftex", "pdflatex"] = "pdflatex",
			   custom_options: AnyStr = "") -> None:
		"""
		Compile the LaTeX document at :py:attr:`path` to a PDF file. The document must be closed before attempting to perform
		this operation.

		:param out_file_path: which path to output the file to
		:param overwrite: whether or not to overwrite a file that already exists
		:param delete_aux_files: delete the generated auxiliary files after compilation of the document is complete
		:param engine: which engine to use for conversion between the TeX and PDF files (specifically which string to use to
			call said engine), currently only ``pdftex``/``pdflatex`` is supported
		:param custom_options: options to directly pass to the engine which are not included as argument to this function

		:raise TeXError: if the document was still opened while calling this function or if there was an error while
			executing the engine command in the subshell
		:raise FileExistsError: if the file is already exists and ``overwrite`` is not set to True
		"""
		self.__require_used__()

		if not overwrite and os.path.isfile(out_file_path):
			raise FileExistsError(f"Cannot write PDF of {repr(self)} to {out_file_path}, if you want to overwrite "
								  f"files by default use overwrite=True in the arguments")

		out_file_path = os.path.abspath(out_file_path)
		if out_file_path.lower().endswith(".pdf"):
			out_file_path = out_file_path[:-4]
		out_dir = os.path.dirname(out_file_path)
		out_file = os.path.basename(out_file_path)
		out_aux_dir = os.path.join(out_dir, '.aux')

		os.makedirs(out_aux_dir, exist_ok=True)

		error_msg = f"Error while converting to PDF using {engine}"
		try:
			if engine == "pdflatex" or engine == "pdftex":
				ret = run(
						("pdflatex",
						 os.path.basename(self.path),
						 "-include-directory", os.path.dirname(self.path),
						 "-job-name", out_file,
						 "-output-directory", out_dir,
						 "-aux-directory", out_aux_dir,
						 "-halt-on-error", "-enable-installer", custom_options),
						cwd=os.path.dirname(self.path),
						shell=False,
						)
			# TODO: support more engines
			else:
				raise NotImplementedError(f"Currently only 'pdflatex' and 'pdftex' are supported, "
										  f"but received request for {engine}")

			if ret.returncode != 0:
				raise TeXError(f"{error_msg}, return code: {ret.returncode}", self)
		except OSError as e:
			raise TeXError(error_msg, self) from e
		finally:
			# delete aux files
			if delete_aux_files:
				shutil.rmtree(out_aux_dir)

	def __str__(self) -> str:
		return self.LaTeXTemplate.format(
				self._document_options,
				self._document_class,
				str(self._definitions),
				str(self._preamble),
				str(self._body)
				)

	def __repr__(self) -> str:
		try:
			# windows might throw an error for paths across drives
			path = os.path.relpath(self.path)
		except OSError:
			path = self._path
		return f"LaTeXDocument(" \
			   f"path={path}, " \
			   f"{'' if self._title is None else f'title={self._title}, '}" \
			   f"definitions={self._definition_list}, " \
			   f"open={self._open}, " \
			   f"successfully_saved_tex={self.successfully_saved_tex})"

class LaTeXEnvironment(TeXResource):
	r"""
	Base class for an environment in a LaTeX document (see :py:class:`LaTeXDocument`). This class usually acts as base
	class for extensions that add simpler ways to write to an environment, but it can also be used directly if an environment
	that is not necessarily worth implementing is desired.

	Example usage with two nested context managers: ::

		...
		with LaTeXEnvironment(document, "center") as env_center:
			with LaTeXEnvironment(env_center, "equation", required_packages=("amsmath",)) as env_eq:
				env_eq.write(r"\forall a, b \in \mathbb{R}, \exists c \in \mathbb{R} \colon a^2 + b^2 = c^2")

	..	note::

		When inheriting from this class, one should usually only overwrite the following methods: :py:meth:`__init__`,
		:py:meth:`write`, and :py:meth:`newline`. Overwriting other methods is allowed if needed, unless marked as final.

		It is highly recommended to use either a super call to this class or at least the private methods :py:meth:`_write`
		and :py:meth:`_newline` to handle internal write calls to the :py:class:`.TeXHandler` instance, since these may
		perform additional actions.

	:param parent_env: the parent :py:class:`LaTeXDocument` or :py:class:`LaTeXEnvironment` to this environment
	:param environment_name: the name of the environment, this value is put for the ``\begin`` and ``\end`` commands
	:param options: the options to pass to the environment, this value is put after the ``\begin`` command
	:param required_packages: the packages which are required to use this environment
	:param indent_level: the number of tab characters to indent this environment relative to the parent environment
	"""

	BEGIN_TEMPLATE: Final = r"\begin{{{}}}{}"
	END_TEMPLATE: Final = r"\end{{{}}}"

	def __init__(self,
				 parent_env: Union[LaTeXDocument, LaTeXEnvironment],
				 environment_name: AnyStr,
				 options: AnyStr = "",
				 required_packages: Collection[AnyStr] = (),
				 indent_level: int = 1):
		super(LaTeXEnvironment, self).__init__()

		self._parent_env = parent_env
		self._environment_name = environment_name
		if options == "" or (options.startswith("[") and options.endswith("]")):
			self._options = options
		else:
			self._options = f"[{options}]"
		self._document = None

		# packages
		self.document.use_package(*required_packages)

		# write handler and alias
		self._handler = TeXHandler(indent_level)

	@final
	@property
	def document(self) -> LaTeXDocument:
		"""
		:return: the root document of this environment stack
		:raise TeXError: if one of the parent environments is neither of type LaTeXDocument nor LaTeXEnvironment
		"""
		if self._document is None:
			self._document = self._parent_env
			while not isinstance(self._document, LaTeXDocument):
				if not isinstance(self._document, LaTeXEnvironment):
					error_obj = type(self._document)
					self._document = None
					raise TeXError(f"Found a value which is neither LaTeXDocument nor LaTeXEnvironment but "
								   f"{error_obj} while processing root document", self)
				self._document = self._document._parent_env
		return self._document

	@final
	@property
	def parent_env(self) -> Union[LaTeXDocument, LaTeXEnvironment]:
		""" :return: the parent :py:class:`.TeXResource` of this environment """
		return self._parent_env

	@final
	@property
	def parent_handler(self) -> TeXHandler:
		"""
		:return: the handler of the :py:attr:`parent_env` resource, in the case of :py:class:`LaTeXDocument` this
			function will return the handler of the body
		"""
		# get handler of parent instance (body for document!)
		if isinstance(self._parent_env, LaTeXDocument):
			return self._parent_env.body
		else:
			return self._parent_env._handler

	@final
	@property
	def environment_name(self) -> AnyStr:
		return self._environment_name

	@property
	def options(self) -> AnyStr:
		return self._options

	@property
	def begin_text(self) -> str:
		""" :return: the definition text to open this environment in the TeX source """
		return self.BEGIN_TEMPLATE.format(self._environment_name, self._options)

	@property
	def end_text(self) -> str:
		""" :return: the definition text to close this environment in the TeX source """
		return self.END_TEMPLATE.format(self._environment_name)

	def __enter__(self) -> LaTeXEnvironment:
		self.parent_env.__require_open__()
		super(LaTeXEnvironment, self).__enter__()

		# write begin to parent env
		self.parent_handler.write(self.begin_text)

		return self

	def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
		self.parent_env.__require_open__()
		try:
			# write handler data to parent env
			self.parent_handler.write(self._handler)
			# write end to parent env
			self.parent_handler.write(self.end_text)
			self.parent_handler.newline()
		finally:
			return super(LaTeXEnvironment, self).__exit__(exc_type, exc_val, exc_tb)

	def write(self, s: AnyStr) -> None:
		"""
		Shorthand for writing to the handler of this instance.

		:raise TeXError: if the document has not been opened
		"""
		self._write(s)

	def newline(self) -> None:
		"""
		Shorthand for writing a newline the handler of this instance.

		:raise TeXError: if the document has not been opened
		"""
		self._newline()

	@final
	def _write(self, s: AnyStr) -> None:
		self.__require_open__(frame_depth=2)
		self._handler.write(s)

	@final
	def _newline(self) -> None:
		self.__require_open__(frame_depth=2)
		self._handler.newline()

	def __str__(self) -> str:
		return f"{self.begin_text}\n{str(self._handler)}\n{self.end_text}"

	def __repr__(self) -> str:
		return f"{self.__class__.__name__}(" \
			   f"parent={self._parent_env.__class__.__name__}, " \
			   f"options={self._options}, " \
			   f"opened={self._open})"

# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~ CONCRETE ENVIRONMENTS ~~~~~~~~~~~~~~~
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@final
class Center(LaTeXEnvironment):
	"""
	:py:class:`Center` represents the standard LaTeX ``center`` environment. It has no options and no required packages.

	:param parent_env: the parent :py:class:`LaTeXDocument` or :py:class:`LaTeXEnvironment` to this environment
	:param indent_level: the number of tab characters to indent this environment relative to the parent environment
	"""

	def __init__(self,
				 parent_env: Union[LaTeXDocument, LaTeXEnvironment],
				 indent_level: int = 1):
		super(Center, self).__init__(parent_env,
									 environment_name="center",
									 options="",
									 required_packages=(),
									 indent_level=indent_level)

class Figure(LaTeXEnvironment):
	r"""
	:py:class:`Figure` represents the standard LaTeX ``figure`` environment. It can be initialized with a caption, a label,
	and options. The options default to ``h!`` to force placement at the location of the definition of the figure.

	When referencing this figure, use the :py:attr:`label` property as follows, as it adds the ``fig:`` prefix
	automatically when left out and makes referencing easier and less error-prone: ::

		with LaTeXDocument("ham.tex") as (doc, _, _):
			f1 = Figure(doc, "Caption.", "a-label")
			assert f1.label == "fig:a-label"

			f2 = Figure(doc, "Spam Ham Caption.", "fig:label-label")
			assert f2.label == "fig:label-label"

	:param parent_env: the parent :py:class:`LaTeXDocument` or :py:class:`LaTeXEnvironment` to this environment
	:param caption: the caption of the figure, may be ``None``
	:param label: the label of the figure, can include ``fig:`` as prefix but if this is absent the prefix will be added
		automatically by the :py:attr:`label` property, may be ``None``
	:param options: the options to pass to the environment, this value is put after the ``\begin`` command
	:param indent_level: the number of tab characters to indent this environment relative to the parent environment
	"""

	def __init__(self,
				 parent_env: Union[LaTeXDocument, LaTeXEnvironment],
				 caption: Optional[AnyStr] = None,
				 label: Optional[AnyStr] = None,
				 options: AnyStr = "h!",
				 indent_level: int = 1):
		super(Figure, self).__init__(parent_env,
									 environment_name="figure",
									 options=options,
									 required_packages=(),
									 indent_level=indent_level)
		self._caption = caption
		self._label = label

	@property
	def caption(self) -> Optional[AnyStr]:
		""" :return: the caption of this figure """
		return self._caption

	@property
	def label(self) -> Optional[AnyStr]:
		""" :return: the label referencing this figure, automatically adds ``fig:`` prefix if missing """
		if self._label is not None and not self._label.startswith("fig:"):
			return f"fig:{self._label}"
		else:
			return self._label

	def write_figure_table(self) -> None:
		""" Write a table of the figures in this document at this location. """
		self.document.body.write(r"\listoffigures")

	def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
		# write caption and label
		if self._caption is not None:
			self.write(f"\\caption{{{self._caption}}}")
		if self._label is not None:
			self.write(f"\\label{{{self.label}}}")

		return super(Figure, self).__exit__(exc_type, exc_val, exc_tb)

class MathsEnvironment(LaTeXEnvironment):
	r"""
	:py:class:`MathsEnvironment` represents a base implementation of any ``amsmath`` math environment which uses a star,
	and non-star version. It can be passed the star flag upon creation, which will be inserted at the start of the environment
	name. When writing to this instance, text will automatically be formatted using :py:func:`.tex_maths_string` and the
	:py:meth:`newline` method will write a double backslash ``\\`` instead of the newline character ``\n``.

	:param parent_env: the parent :py:class:`LaTeXDocument` or :py:class:`LaTeXEnvironment` to this environment
	:param env_name: the parent environment or document to this environment
	:param star: whether or not to prefix the environment name with a star like so: ``*env_name`` or ``env_name``
	:param indent_level: the number of tab characters to indent this environment relative to the parent environment
	"""

	def __init__(self,
				 parent_env: Union[LaTeXDocument, LaTeXEnvironment],
				 env_name: str,
				 star: bool = True,
				 indent_level: int = 1):
		super(MathsEnvironment, self).__init__(parent_env,
											   environment_name=f"{env_name}{'*' if star else ''}",
											   options="",
											   required_packages=("amsmath",),
											   indent_level=indent_level)

	def write(self, s: Any) -> None:
		r"""
		Shorthand for writing to the handler of this instance. Automatically applies :py:func:`.tex_maths_string` to every
		``s`` object passed to it.

		:raise TeXError: if the document has not been opened
		"""
		super(MathsEnvironment, self).write(tex_maths_string(s))

	def newline(self) -> None:
		r"""
		Shorthand for writing a newline to the handler of this instance. Instead of ``\n`` this method places ``\\`` to
		cause a line break.

		:raise TeXError: if the document has not been opened
		"""
		super(MathsEnvironment, self).write(r"\\")
