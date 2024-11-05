# -*- coding: utf-8 -*-

from __future__ import unicode_literals
import warnings


__title__ = "drf-haystack"
__version__ = "1.9.1"
__author__ = "Rolf Haavard Blindheim"
__license__ = "MIT License"

VERSION = __version__


def show_sunset_warning():
    """Show a warning about potential future sunsetting."""
    message = (
        "\n"
        "==============================================================================\n"
        "The `drf-haystack` project urgently needs new maintainers!\n"
        "\n"
        "The current maintainers are no longer actively using drf-haystack and would\n"
        "like to hand over the project to other developers who are using the package.\n"
        "\n"
        "We will still do the bare minimum maintenance of keeping dependency references\n"
        "up to date with new releases of related packages until January 1st 2026.\n"
        "\n"
        "If by that time no new maintainers have joined to take over the project, we\n"
        "will archive the project and make the repository read-only, with a final\n"
        "release with whatever versions the dependencies have at that time.\n"
        "\n"
        "This gives everyone more than a year to either consider joining as maintainers\n"
        "or switch to other packages for handling their search in DRF.\n"
        "\n"
        "Do you want to join as a maintainer? Have a look at:\n"
        "<https://github.com/rhblind/drf-haystack/issues/146>\n"
        "==============================================================================\n"
    )
    warnings.warn(message, UserWarning, stacklevel=2)


show_sunset_warning()
