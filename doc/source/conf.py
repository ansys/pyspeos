"""Sphinx documentation configuration file."""
from datetime import datetime
import os

from ansys_sphinx_theme import ansys_favicon, get_version_match
from sphinx.builders.latex import LaTeXBuilder

from ansys.speos import __version__

LaTeXBuilder.supported_image_types = ["image/png", "image/pdf", "image/svg+xml"]

# Project information
project = "ansys-pyspeos"
copyright = f"(c) {datetime.now().year} ANSYS, Inc. All rights reserved"
author = "Ansys Inc."
release = version = __version__
cname = os.getenv("DOCUMENTATION_CNAME", default="speos.docs.pyansys.com")

# use the default pyansys logo
html_theme = "ansys_sphinx_theme"
html_favicon = ansys_favicon

# specify the location of your github repo
html_theme_options = {
    "logo": "pyansys",
    "github_url": "https://github.com/ansys-internal/pyspeos",
    "show_prev_next": False,
    "switcher": {
        "json_url": f"https://{cname}/versions.json",
        "version_match": get_version_match(__version__),
    },
    "check_switcher": False,
    "ansys_sphinx_theme_autoapi": {
        "project": project,
    },
}

# Sphinx extensions
extensions = [
    "numpydoc",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "sphinx_design",
    "sphinx_jinja",
    "sphinx.ext.autodoc",
    "ansys_sphinx_theme.extension.autoapi",
    "nbsphinx",
    "myst_parser",
]

# Intersphinx mapping
intersphinx_mapping = {
    "python": ("https://docs.python.org/3/", None),
    "grpc": ("https://grpc.github.io/grpc/python/", None),
    "pypim": ("https://pypim.docs.pyansys.com/version/stable", None),
    # kept here as an example
    # "scipy": ("https://docs.scipy.org/doc/scipy/reference", None),
    # "numpy": ("https://numpy.org/devdocs", None),
    # "matplotlib": ("https://matplotlib.org/stable", None),
    # "pandas": ("https://pandas.pydata.org/pandas-docs/stable", None),
    # "pyvista": ("https://docs.pyvista.org/", None),
}

numpydoc_show_class_members = False
numpydoc_xref_param_type = True
numpydoc_validate = True
numpydoc_validation_checks = {
    "GL06",  # Found unknown section
    "GL07",  # Sections are in the wrong order.
    # "GL08",  # The object does not have a docstring
    "GL09",  # Deprecation warning should precede extended summary
    "GL10",  # reST directives {directives} must be followed by two colons
    "SS01",  # No summary found
    "SS02",  # Summary does not start with a capital letter
    # "SS03", # Summary does not end with a period
    "SS04",  # Summary contains heading whitespaces
    # "SS05", # Summary must start with infinitive verb, not third person
    "RT02",  # The first line of the Returns section should contain only the
    # type, unless multiple values are being returned"
}

# static path
html_static_path = ["_static"]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix(es) of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"
suppress_warnings = ["autoapi"]
autodoc_typehints = "description"

# -- Declare the Jinja context -----------------------------------------------
BUILD_EXAMPLES = True if os.environ.get("BUILD_EXAMPLES", "true") == "true" else False
if BUILD_EXAMPLES:
    extensions.extend(["myst_parser", "nbsphinx"])
    nbsphinx_execute = "always"
    nbsphinx_allow_errors = True
    nbsphinx_custom_formats = {
        ".mystnb": ["jupytext.reads", {"fmt": "mystnb"}],
        ".py": ["jupytext.reads", {"fmt": ""}],
    }
    nbsphinx_prompt_width = ""
    nbsphinx_prolog = """

    .. grid:: 3
        :gutter: 1

        .. grid-item::
            :child-align: center

            .. button-link:: {cname_pref}/{python_file_loc}
                :color: primary
                :shadow:

                Download as Python script :fab:`python`

        .. grid-item::
            :child-align: center

            .. button-link:: {cname_pref}/{ipynb_file_loc}
               :color: primary
               :shadow:

                Download as Jupyter notebook :fas:`book`

        .. grid-item::
            :child-align: center

            .. button-link:: {cname_pref}/{pdf_file_loc}
               :color: primary
               :shadow:

                Download as PDF document :fas:`file-pdf`

----

    """.format(
        cname_pref=f"https://{cname}/version/{get_version_match(version)}",
        python_file_loc="{{ env.docname }}.py",
        ipynb_file_loc="{{ env.docname }}.ipynb",
        pdf_file_loc="{{ env.docname }}.pdf",
    )


jinja_contexts = {
    "linux_containers": {},
    "main_toctree": {
        "build_examples": BUILD_EXAMPLES,
    },
}
