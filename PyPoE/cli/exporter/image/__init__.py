"""
.dat Exporter

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/dat/__init__.py                               |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | Omega_K2                                                         |
+----------+------------------------------------------------------------------+

Description
===============================================================================

.dat Exporter

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python

# 3rd-party

# self
from PyPoE.cli.exporter.image.parsers.path import PathExportHandler
from PyPoE.cli.exporter.image.parsers.visualid import VisualIDExportHandler
from PyPoE.cli.exporter.image.parsers.unique import UniqueExportHandler

# =============================================================================
# Globals
# =============================================================================

__all__ = ['ImageHandler']

# =============================================================================
# Classes
# =============================================================================


class ImageHandler:
    """

    :type sql: argparse.ArgumentParser
    """
    def __init__(self, sub_parser):
        """

        :type sub_parser: argparse._SubParsersAction
        """
        parser = sub_parser.add_parser(
            'image',
            help='Image export',
        )
        parser.set_defaults(func=lambda args: parser.print_help())

        sub = parser.add_subparsers(help='Export type')
        PathExportHandler(sub)
        VisualIDExportHandler(sub)
        UniqueExportHandler(sub)

# =============================================================================
# Functions
# =============================================================================
