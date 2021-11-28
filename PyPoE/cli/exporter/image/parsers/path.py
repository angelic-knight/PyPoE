"""
image export from file path

Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/dat/parsers/json.py                           |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | angelic_knight                                                   |
+----------+------------------------------------------------------------------+

Description
===============================================================================

image export from file path

Agreement
===============================================================================

See PyPoE/LICENSE
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import argparse
from json import dump
import os.path

# self
from PyPoE.cli.exporter import config
from PyPoE.cli.core import console, Msg
from PyPoE.cli.exporter.image.handler import ImageExportHandler
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.cli.exporter.util import get_content_path, fix_path

# =============================================================================
# Globals
# =============================================================================

__all__ = ['PathExportHandler']

# =============================================================================
# Classes
# =============================================================================


class PathExportHandler(ImageExportHandler):
    def __init__(self, sub_parser):
        """
        :type sub_parser: argparse._SubParsersAction
        """
        self.path = sub_parser.add_parser(
            'path',
            help='Export based on a path',
            formatter_class=argparse.RawTextHelpFormatter,
        )
        
        # Add and user image parameters?

        self.add_default_arguments(self.path)

    def handle(self, args):
        super().handle(args)

        self.file_system = FileSystem(root_path=get_content_path())

        temp_dir = config.get_option('temp_dir')
        img_path = os.path.join(temp_dir, 'img')

        if args.files is None:
            return
        else:
            for file_path in args.files:
                (directory, file_name) = os.path.split(file_path)
                dds = os.path.join(img_path, file_name)
                png = os.path.join(img_path, file_name.replace('.dds', '.png'))
                if not (os.path.exists(dds) or os.path.exists(png)):
                    self._write_dds(
                        data=self.file_system.get_file(file_path),
                        out_path=dds,
                    )

        console('Done.')

# =============================================================================
# Functions
# =============================================================================
