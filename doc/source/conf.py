"""Sphinx documentation configuration file."""
from datetime import datetime
import os
from pathlib import Path

from ansys_sphinx_theme import (
    ansys_favicon,
    get_autoapi_templates_dir_relative_path,
    get_version_match,
    pyansys_logo_black,
)
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
html_logo = pyansys_logo_black
html_theme = "ansys_sphinx_theme"
html_favicon = ansys_favicon

# specify the location of your github repo
html_theme_options = {
    "github_url": "https://github.com/ansys-internal/pyspeos",
    "show_prev_next": False,
    "switcher": {
        "json_url": f"https://{cname}/versions.json",
        "version_match": get_version_match(__version__),
    },
    "check_switcher": False,
}

# Sphinx extensions
extensions = [
    "numpydoc",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "autoapi.extension",
    "sphinx_design",
    "sphinx_jinja",
    "sphinx.ext.autodoc",
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

autoapi_type = "python"
autoapi_dirs = ["../../src"]
autoapi_root = "api"
autoapi_options = [
    "members",
    "undoc-members",
    "show-inheritance",
    "show-module-summary",
    "special-members",
]
autoapi_template_dir = get_autoapi_templates_dir_relative_path(Path(__file__))
suppress_warnings = ["autoapi"]
autoapi_python_use_implicit_namespaces = True
autoapi_keep_files = True
autoapi_own_page_level = "class"
autodoc_typehints = "description"

jinja_contexts = {
    "linux_containers": {},
}


def prepare_jinja_env(jinja_env) -> None:
    """
    Customize the jinja env.

    Notes
    -----
    See https://jinja.palletsprojects.com/en/3.0.x/api/#jinja2.Environment
    """
    jinja_env.globals["project_name"] = project


autoapi_prepare_jinja_env = prepare_jinja_env
