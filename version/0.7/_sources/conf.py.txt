"""Sphinx documentation configuration file."""

from datetime import datetime
import os
import pathlib
import shutil

from ansys_sphinx_theme import ansys_favicon, get_version_match
import sphinx
from sphinx.builders.latex import LaTeXBuilder
from sphinx.util import logging
from sphinx.util.display import status_iterator

from ansys.speos.core import __version__

LaTeXBuilder.supported_image_types = ["image/png", "image/pdf", "image/svg+xml"]
os.environ["DOCUMENTATION_BUILDING"] = "true"
os.environ["PYANSYS_VISUALIZER_HTML_BACKEND"] = "true"
logger = logging.getLogger(__name__)

# Project information
project = "ansys-speos-core"
copyright = f"(c) {datetime.now().year} ANSYS, Inc. All rights reserved"
author = "Ansys Inc."
release = version = __version__
cname = os.getenv("DOCUMENTATION_CNAME", default="speos.docs.pyansys.com")

# use the default pyansys logo
html_theme = "ansys_sphinx_theme"
html_favicon = ansys_favicon

# Specify the location of the github repo
html_context = {
    "github_user": "ansys",
    "github_repo": "pyspeos",
    "github_version": "main",
    "doc_path": "doc/source",
    "pyansys_tags": ["Optics"],
}

# specify the location of your github repo
html_theme_options = {
    "logo": "pyansys",
    "github_url": "https://github.com/ansys/pyspeos",
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
BUILD_CHEATSHEET = os.environ.get("BUILD_CHEATSHEET", "false").lower() == "true"
if BUILD_CHEATSHEET:
    html_theme_options["cheatsheet"] = {
        "file": "cheat_sheet/cheat_sheet_script.qmd",
        "title": "PySpeos cheat sheet",
        "version": f"v{version}",
        "pages": ["index"],
    }

# Sphinx extensions
extensions = [
    "numpydoc",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx.ext.autodoc",
    "sphinx_design",
    "sphinx_jinja",
    "ansys_sphinx_theme.extension.autoapi",
    "nbsphinx",
    "myst_parser",
    "sphinxcontrib.mermaid",
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
html_css_files = ["custom.css"]

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
    nbsphinx_custom_formats = {
        ".mystnb": ["jupytext.reads", {"fmt": "mystnb"}],
        ".py": ["jupytext.reads", {"fmt": ""}],
    }
    nbsphinx_thumbnails = {
        "examples/core/bsdf": "_static/thumbnails/bsdf.png",
        "examples/core/opt-prop": "_static/thumbnails/property_520x520.png",
        "examples/core/source": "_static/thumbnails/source_520x520.png",
        "examples/core/sensor": "_static/thumbnails/sensor_520x520.png",
        "examples/core/part": "_static/thumbnails/part_520x520.png",
        "examples/core/simulation": "_static/thumbnails/simulation_520x520.png",
        "examples/core/project": "_static/thumbnails/how_to_create_a_project.PNG",
        "examples/core/lpf-preview": "_static/thumbnails/script_lpf_preview.PNG",
        "examples/core/prism-example": "_static/thumbnails/prism_example_using_script_layer.PNG",
        "examples/kernel/object-link": "_static/thumbnails/pySpeos_520x520.png",
        "examples/kernel/scene-job": "_static/thumbnails/pySpeos_520x520.png",
        "examples/kernel/modify-scene": "_static/thumbnails/pySpeos_520x520.png",
        "examples/workflow/open-result": "_static/thumbnails/workflow_open_result.png",
        "examples/workflow/combine-speos": "_static/thumbnails/workflow_moving_car.PNG",
    }
    nbsphinx_prompt_width = ""
    nbsphinx_prolog = """

    .. grid:: 5

        .. grid-item::

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

            .. button-link:: {cname_pref}/{assets_loc}
               :color: primary
               :shadow:

                Download example's assets :fa:`file`

        .. grid-item::

----

    """.format(
        cname_pref=f"https://{cname}/version/{get_version_match(version)}",
        python_file_loc="{{ env.docname }}.py",
        ipynb_file_loc="{{ env.docname }}.ipynb",
        assets_loc="_static/assets/download/assets.zip",
    )


jinja_contexts = {
    "linux_containers": {},
    "main_toctree": {
        "build_examples": BUILD_EXAMPLES,
    },
}


def copy_examples_to_output_dir(app: sphinx.application.Sphinx, exception: Exception):
    """
    Copy the examples directory to the output directory of the documentation.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        Sphinx application instance containing the all the doc build configuration.
    exception : Exception
        Exception encountered during the building of the documentation.

    """
    OUTPUT_EXAMPLES = pathlib.Path(app.outdir) / "examples"
    OUTPUT_IMAGES = OUTPUT_EXAMPLES / "img"
    OUTPUT_CORE = OUTPUT_EXAMPLES / "core"
    OUTPUT_KERNEL = OUTPUT_EXAMPLES / "kernel"
    OUTPUT_WORKFLOW = OUTPUT_EXAMPLES / "workflow"
    for directory in [
        OUTPUT_EXAMPLES,
        OUTPUT_IMAGES,
        OUTPUT_CORE,
        OUTPUT_KERNEL,
        OUTPUT_WORKFLOW,
    ]:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)

    SOURCE_EXAMPLES = pathlib.Path(app.srcdir) / "examples"
    EXAMPLES_DIRECTORY = SOURCE_EXAMPLES.parent.parent.parent / "examples"

    # Copyt the examples
    examples = list(EXAMPLES_DIRECTORY.glob("**/*.py"))
    for file in status_iterator(
        examples,
        "Copying example to doc/_build/examples/",
        "green",
        len(examples),
        verbosity=1,
        stringify_func=(lambda file: file.name),
    ):
        destination_file = OUTPUT_EXAMPLES / file.parent.name / file.name
        destination_file.write_text(file.read_text(encoding="utf-8"), encoding="utf-8")


def copy_examples_files_to_source_dir(app: sphinx.application.Sphinx):
    """
    Copy the examples directory to the source directory of the documentation.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        Sphinx application instance containing the all the doc build configuration.

    """
    SOURCE_EXAMPLES = pathlib.Path(app.srcdir) / "examples"
    SOURCE_IMAGES = SOURCE_EXAMPLES / "img"
    CORE_EXAMPLES = SOURCE_EXAMPLES / "core"
    KERNEL_EXAMPLES = SOURCE_EXAMPLES / "kernel"
    WORKFLOW_EXAMPLES = SOURCE_EXAMPLES / "workflow"
    for directory in [
        SOURCE_EXAMPLES,
        SOURCE_IMAGES,
        CORE_EXAMPLES,
        KERNEL_EXAMPLES,
        WORKFLOW_EXAMPLES,
    ]:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)

    EXAMPLES_DIRECTORY = SOURCE_EXAMPLES.parent.parent.parent / "examples"

    # Copy the the examples
    examples = list(EXAMPLES_DIRECTORY.glob("**/*.py"))
    for file in status_iterator(
        examples,
        "Copying example to doc/source/examples/",
        "green",
        len(examples),
        verbosity=1,
        stringify_func=(lambda file: file.name),
    ):
        destination_file = SOURCE_EXAMPLES / file.parent.name / file.name
        destination_file.write_text(file.read_text(encoding="utf-8"), encoding="utf-8")


def copy_assets_to_output_dir(app: sphinx.application.Sphinx, exception: Exception):
    """Copy the assets directory to the output directory of the documentation.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        Sphinx application instance containing the all the doc build configuration.
    exception : Exception
        Exception encountered during the building of the documentation.
    """
    if app.builder.name != "html":
        logger.info(
            "Skip assets extraction with build %s.",
            app.builder.name,
        )
        return

    source_assets = pathlib.Path(app.outdir).parent.parent.parent / "tests" / "assets"

    output_dir = pathlib.Path(app.outdir) / "_static" / "assets" / "download"

    if not source_assets.exists():
        logger.warning(
            "Assets directory not found at %s; skipping asset packaging.",
            source_assets,
        )
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Packaging assets for documentation output...")

    archive_base = output_dir / "assets"
    zip_path = shutil.make_archive(
        base_name=str(archive_base),
        format="zip",
        root_dir=str(source_assets),
    )

    logger.info("Assets packaged at %s.", zip_path)


def remove_examples_from_source_dir(app: sphinx.application.Sphinx, exception: Exception):
    """
    Remove the example files from the documentation source directory.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        Sphinx application instance containing the all the doc build configuration.
    exception : Exception
        Exception encountered during the building of the documentation.

    """
    EXAMPLES_DIRECTORY = pathlib.Path(app.srcdir) / "examples"
    logger.info(f"\nRemoving {EXAMPLES_DIRECTORY} directory...")
    shutil.rmtree(EXAMPLES_DIRECTORY)


def setup(app: sphinx.application.Sphinx):
    """
    Run different hook functions during the documentation build.

    Parameters
    ----------
    app : sphinx.application.Sphinx
        Sphinx application instance containing the all the doc build configuration.

    """
    # HACK: rST files are copied to the doc/source directory before the build.
    # Sphinx needs all source files to be in the source directory to build.
    # However, the examples are desired to be kept in the root directory. Once the
    # build has completed, no matter its success, the examples are removed from
    # the source directory.
    if BUILD_EXAMPLES:
        app.connect("builder-inited", copy_examples_files_to_source_dir)
        app.connect("build-finished", remove_examples_from_source_dir)
        app.connect("build-finished", copy_assets_to_output_dir)
        app.connect("build-finished", copy_examples_to_output_dir)
