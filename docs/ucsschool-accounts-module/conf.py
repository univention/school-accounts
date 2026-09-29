# SPDX-FileCopyrightText: 2023-2026 Univention GmbH
# SPDX-License-Identifier: AGPL-3.0-only

# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
import os
import sys

from datetime import date

# -- Project information -----------------------------------------------------


def read_version_from_ci() -> str:
    """Read the version for the documentation from the pipeline definition

    To not maintain the documentation version in different places, just define
    at one place and use it in different places.

    The documentation version influences the version shown in the content of
    the document and the path of the published documentation.

    :returns: The version number for the documentation as defined in the CI/CD
        pipeline.

    :rtype: str
    """

    import yaml

    class GitLabCILoader(yaml.SafeLoader):
        """Loader that tolerates GitLab's custom tags, e.g. ``!reference``."""

    GitLabCILoader.add_multi_constructor("!", lambda loader, suffix, node: None)

    with open("../../.gitlab-ci/gitlab-ci.yml", "r") as f:
        ci = yaml.load(f, Loader=GitLabCILoader)  # noqa: S506
        return ci.get("variables", {"DOC_TARGET_VERSION": "1.0"}).get(
            "DOC_TARGET_VERSION"
        )


release = read_version_from_ci()
version = release

project = "School Accounts {}".format(release)
copyright = "{}, Univention GmbH".format(date.today().year)
author = "Univention GmbH"
language = "en"

html_title = project

# The doc_basename must match the documents root directory name on the public
# target location. Otherwise the PDF link on the overview page will point to
# the wrong file.
doc_basename = os.path.basename(os.path.dirname(__file__))

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    "sphinx_copybutton",
    "sphinxcontrib.spelling",
    "univention_sphinx_extension",
    "sphinx_sitemap",
    "sphinx_last_updated_by_git",
    "sphinx.ext.intersphinx",
]

intersphinx_mapping = {
    "uv-keycloak": ("https://docs.software-univention.de/keycloak-app/latest", None),
    "uv-school-kelvin": (
        "https://docs.software-univention.de/ucsschool-kelvin-rest-api",
        None,
    ),
    "uv-school-manual": (
        "https://docs.software-univention.de/ucsschool-manual/latest/de",
        None,
    ),
    "uv-ucs-manual": (
        "https://docs.software-univention.de/manual/latest/en/",
        None,
    ),
    "uv-nubus-manual": (
        "https://docs.software-univention.de/nubus-manual/1.x/en/",
        None,
    ),
    "uv-ucs-operation": (
        "https://docs.software-univention.de/ucs-operation/5.2/en/",
        None,
    ),
}


# For more configuration options of Sphinx-copybutton, see the documentation
# https://sphinx-copybutton.readthedocs.io/en/latest/index.html
copybutton_prompt_text = r"\$ "
copybutton_prompt_is_regexp = True
copybutton_line_continuation_character = "\\"
copybutton_here_doc_delimiter = "EOT"

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "univention_sphinx_book_theme"
html_theme_options = {
    "pdf_download_filename": f"{doc_basename}.pdf",
    "show_source_license": True,
    "typesense_search": True,
    "typesense_document": doc_basename,
    "typesense_document_version": version,  # or "latest"
    "univention_matomo_tracking": True,
    "univention_docs_deployment": True,
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]

numfig = True

rst_epilog = r"""
.. |UCSUAS| replace:: UCS\@school
.. |UASUMM| replace:: School Accounts
"""

suppress_warnings = ["git.too_shallow"]
git_last_updated_timezone = "Europe/Berlin"

if "spelling" in sys.argv:
    spelling_lang = "en"
    spelling_show_suggestions = True
    spelling_word_list_filename = ["spelling_wordlist"]

root_doc = "contents"

latex_engine = "lualatex"
latex_show_pagerefs = True
latex_show_urls = "footnote"
latex_documents = [(root_doc, f"{doc_basename}.tex", project, author, "manual", False)]
latex_elements = {
    "papersize": "a4paper",
    "babel": "\\usepackage{babel}",
}

# Configure Univention feedback link
# See https://git.knut.univention.de/univention/documentation/univention_sphinx_extension#univention_feedback

# Deactivated per default. To activate, set it to True.
univention_feedback = True

# See https://git.knut.univention.de/univention/documentation/univention_sphinx_extension
univention_doc_basename = doc_basename
univention_pdf_show_source_license = True
univention_use_doc_base = True
univention_release_language_scheme = "{release}"
