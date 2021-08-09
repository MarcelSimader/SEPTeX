# SEPTeX

[![Publish to PyPI](https://github.com/MarcelSimader/SEPTeX/actions/workflows/python-publish.yml/badge.svg)](https://github.com/MarcelSimader/SEPTeX/actions/workflows/python-publish.yml)
|  [Documentation](https://marcelsimader.github.io/SEPTeX/)

SEPTeX is a wrapper library for generating TeX/TikZ code through Python.

This project is in version ``v0.x.y`` and hence in rapid development phase. Once a stable public API has formed version ``v1.0.0`` will be released.

---

The package currently divided into two basic components: the TeX component, and the TikZ component. Below is an outline of the most important namespaces:

- ### TeX Part

  - #### TeXBase
    The basic TeX wrapper classes which form the framework.
  - #### LaTeX
    The LaTeX wrapper classes extending ``TeXBase``.
  - #### TeXUtils
    Diverse functions for converting between different objects and ``SEPTeX`` objects.

- ### TikZ Part

  - #### TikZBase
    The TikZ objects and environments which form the TikZ framework.
  - #### TikZ
    Concrete TikZ types extending ``TikZBase``.

  > Under construction:
  > - #### TikZGraph
  >   More complex graph data structures and algorithms which interface ``TikZ``.

---

## Example Usages

Examples are under construction. See documentation for simple examples.
