"""
image export base handler

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/dat/handler.py                                |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | angelic_knight                                                   |
+----------+------------------------------------------------------------------+

Description
===============================================================================

image export base handler

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import os.path

# self
from PyPoE.poe.constants import VERSION
from PyPoE.poe.file import dat
from PyPoE.cli.core import console, Msg
from PyPoE.cli.exporter import config
from PyPoE.cli.exporter.util import fix_path
from PyPoE.poe.file.file_system import FileSystem

# =============================================================================
# Globals
# =============================================================================

__all__ = []

# =============================================================================
# Classes
# =============================================================================


class ImageExportHandler:
    def add_default_arguments(self, parser):
        """

        :param parser:
        :type parser: argparse.ArgumentParser

        :return:
        """
        parser.set_defaults(func=self.handle)
        parser.add_argument(
            '--files', '--file',
            help='Image paths to export',
            nargs='*',
        )
        
    def add_id_arguments(self, parser):
        """

        :param parser:
        :type parser: argparse.ArgumentParser

        :return:
        """
        parser.set_defaults(func=self.handle)
        parser.add_argument(
            '--ids', '--id',
            help='IDs from ItemVisualIdentity.dat to export',
            nargs='*',
        )

    def handle(self, args):
        pass


    def _write_dds(self, data, out_path):
        out_path = fix_path(out_path)
        with open(out_path, 'wb') as f:
            f.write(self.file_system.extract_dds(data))

            console('Wrote "%s"' % out_path)


        os.system('process-image convert "%s" "%s"' % (
            out_path, out_path.replace('.dds', '.png'),
        ))
        os.remove(out_path)

        console('Converted "%s" to png' % out_path)


# =============================================================================
# Functions
# =============================================================================
