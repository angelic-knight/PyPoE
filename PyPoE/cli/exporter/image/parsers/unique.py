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
from enum import unique
from json import dump
import os.path

# self
from PyPoE.cli.exporter import config
from PyPoE.cli.core import console, Msg
from PyPoE.cli.exporter.image.handler import ImageExportHandler
from PyPoE.poe.file.file_system import FileSystem
from PyPoE.cli.exporter.util import get_content_path
from PyPoE.poe.file.dat import RelationalReader, set_default_spec
from PyPoE.poe.file.translations import (
    TranslationFileCache,
    MissingIdentifierWarning,
    get_custom_translation_file,
    install_data_dependant_quantifiers,
)

# =============================================================================
# Globals
# =============================================================================

__all__ = ['PathExportHandler']

# =============================================================================
# Classes
# =============================================================================


class UniqueExportHandler(ImageExportHandler):
    _files = [
        'UniqueStashLayout.dat',
        'Words.dat',
        'ItemVisualIdentity.dat',
    ]

    def __init__(self, sub_parser):
        """
        :type sub_parser: argparse._SubParsersAction
        """
        self.path = sub_parser.add_parser(
            'unique',
            help='Export based on the name of a unique item',
            formatter_class=argparse.RawTextHelpFormatter,
        )
        
        # Add and user image args?

        self.add_name_arguments(self.path)
        
    def add_name_arguments(self, parser):
        """

        :param parser:
        :type parser: argparse.ArgumentParser

        :return:
        """
        parser.set_defaults(func=self.handle)
        parser.add_argument(
            '--names', '--name',
            help='Names of unique items to export',
            nargs='*',
        )


    def handle(self, args):
        super().handle(args)
        

        ###
        # This is ripped off from wiki->parser.py
        # It should do proper inheritance, not copy-pasting code.
        ###
        # Make sure to load the appropriate version of the specification
        set_default_spec(version=config.get_option('version'))
        self.file_system = FileSystem(root_path=get_content_path())

        opt = {
            'use_dat_value': False,
            'auto_build_index': True,
        }

        # Load rr and translations which will be undoubtedly be needed for
        # parsing
        self.rr = RelationalReader(
            path_or_file_system=self.file_system,
            files=self._files,
            read_options=opt,
            raise_error_on_missing_relation=False,
            language=config.get_option('language'),
        )
        install_data_dependant_quantifiers(self.rr)


        target_names = args.names
        if target_names is None:
            return

        unique_entries = self.rr['UniqueStashLayout.dat']
        file_paths = []
        path_to_name = {}
        for unique_entry in unique_entries:
            unique_name = unique_entry['WordsKey']['Text']
            if unique_name in target_names:
                file_path = unique_entry['ItemVisualIdentityKey']['DDSFile']
                file_paths.append(file_path)
                path_to_name[file_path] = unique_name

            if len(file_paths) == len(target_names):
                break

        self.file_system = FileSystem(root_path=get_content_path())

        temp_dir = config.get_option('temp_dir')
        img_path = os.path.join(temp_dir, 'img')

        if file_paths is None:
            return
        else:
            for file_path in file_paths:
                unique_name = path_to_name[file_path] + ' Inventory Icon'
                dds = os.path.join(img_path, unique_name + '.dds')
                png = os.path.join(img_path, unique_name + '.png')
                if not (os.path.exists(dds) or os.path.exists(png)):
                    self._write_dds(
                        data=self.file_system.get_file(file_path),
                        out_path=dds,
                    )

        console('Done.')

# =============================================================================
# Functions
# =============================================================================
