# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.

import os
import sys

sys.path.insert(0, os.path.abspath("../.."))

# -- Project information -----------------------------------------------------

project = 'SEPTeX'
copyright = '2021, Marcel Simader'
author = 'Marcel Simader'

# The full version, including alpha/beta/rc tags
release = '0.2.0'
version = release

# ~~~~~~~~~~~~~~~ CUSTOM CONF ~~~~~~~~~~~~~~~

add_module_names = False

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ["sphinx.ext.autodoc", "sphinx.ext.todo", "sphinx_rtd_theme"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']
html_static_path = ["_static"]
html_css_files = ["custom.css"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
html_theme = "sphinx_rtd_theme"

html_theme_options = {
		"display_version"    : True,
		"collapse_navigation": False
		}

# ~~~~~~~~~~~~~~~ sphinx.ext.to do CONFIG ~~~~~~~~~~~~~~~
todo_include_todos = True

# ~~~~~~~~~~~~~~~ AUTODOC CONFIG ~~~~~~~~~~~~~~~
# autodoc_preserve_defaults = True
autodoc_typehints = "description"
autodoc_inherit_docstrings = True
autodoc_class_signature = "separated"
autodoc_typehints_description_target = "documented"
autodoc_type_aliases = {
		}

autodoc_default_options = {
		"member-order": "bysource",
		}
