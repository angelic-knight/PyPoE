"""
Overview
===============================================================================

+----------+------------------------------------------------------------------+
| Path     | PyPoE/cli/exporter/wiki/parsers/masteries.py                     |
+----------+------------------------------------------------------------------+
| Version  | 1.0.0a0                                                          |
+----------+------------------------------------------------------------------+
| Revision | $Id$                  |
+----------+------------------------------------------------------------------+
| Author   | angelic_knight                                                   |
+----------+------------------------------------------------------------------+

Description
===============================================================================



Agreement
===============================================================================

See PyPoE/LICENSE

Documentation
===============================================================================

Public API
-------------------------------------------------------------------------------

Internal API
-------------------------------------------------------------------------------
"""

# =============================================================================
# Imports
# =============================================================================

# Python
import re
import os.path
import warnings
from functools import partialmethod
from collections import OrderedDict

# 3rd-party

# self
from PyPoE.cli.core import console, Msg
from PyPoE.cli.exporter.wiki import parser
from PyPoE.cli.exporter.wiki.handler import ExporterHandler, ExporterResult
from PyPoE.poe.file.psg import PSGFile

# =============================================================================
# Globals
# =============================================================================

__all__ = []

# =============================================================================
# Classes
# =============================================================================


class WikiCondition(parser.WikiCondition):
    COPY_KEYS = (
        'main_page',
    )

    NAME = 'Mastery'
    ADD_INCLUDE = False
    INDENT = 36


class MasteryCommandHandler(ExporterHandler):
    def __init__(self, sub_parser):
        self.parser = sub_parser.add_parser(
            'mastery',
            help='Mastery exporter',
        )
        self.parser.set_defaults(func=lambda args: self.parser.print_help())

        self.add_default_subparser_filters(
            sub_parser=self.parser.add_subparsers(),
            cls=MasterySkillParser,
        )

        # filtering
        '''a_filter = sub.add_parser(
            'filter',
            help='Extract passives using filters.'
        )
        self.add_default_parsers(
            parser=a_filter,
            cls=PassiveSkillParser,
            func=PassiveSkillParser.by_filter,
        )

        a_filter.add_argument(
            '-ft-id', '--filter-id', '--filter-metadata-id',
            help='Regular expression on the id',
            type=str,
            dest='re_id',
        )'''

    def add_default_parsers(self, *args, **kwargs):
        super().add_default_parsers(*args, **kwargs)
        self.add_format_argument(kwargs['parser'])
        self.add_image_arguments(kwargs['parser'])
        kwargs['parser'].add_argument(
            '-ft-id', '--filter-id', '--filter-metadata-id',
            help='Regular expression on the id',
            type=str,
            dest='re_id',
        )


class MasterySkillParser(parser.BaseParser):
    _MASTERY_FILE_NAME = 'PassiveSkillMasteryEffects.dat'
    _files = [
        _MASTERY_FILE_NAME,
    ]

    _passive_column_index_filter = partialmethod(
        parser.BaseParser._column_index_filter,
        dat_file_name=_MASTERY_FILE_NAME,
        error_msg='Several masteries have not been found:\n%s',
    )

    _MAX_STAT_ID = 3 # How many stats each one can have.

    _COPY_KEYS = OrderedDict((
        ('Id', {
            'template': 'id',
        }),
    ))

    def _apply_filter(self, parsed_args, masteries):
        if parsed_args.re_id:
            parsed_args.re_id = re.compile(parsed_args.re_id, flags=re.UNICODE)
        else:
            return masteries

        new = []

        for mastery in masteries:
            if parsed_args.re_id and not \
                    parsed_args.re_id.match(mastery['Id']):
                continue

            new.append(mastery)

        return new

    def by_rowid(self, parsed_args):
        return self.export(
            parsed_args,
            self.rr[self._MASTERY_FILE_NAME][parsed_args.start:parsed_args.end],
        )

    def by_id(self, parsed_args):
        return self.export(parsed_args, self._passive_column_index_filter(
            column_id='Id', arg_list=parsed_args.id
        ))

    def by_name(self, parsed_args):
        return self.export(parsed_args, self._passive_column_index_filter(
            column_id='Name', arg_list=parsed_args.name
        ))

    def export(self, parsed_args, masteries):
        r = ExporterResult()

        masteries = self._apply_filter(parsed_args, masteries)

        if not masteries:
            console(
                'No passives found for the specified parameters. Quitting.',
                msg=Msg.warning,
            )
            return r

        console('Accessing additional data...')

        self.rr[self._MASTERY_FILE_NAME]

        #self._image_init(parsed_args)

        console(f'Found {len(masteries)}, parsing...')

        for mastery in masteries:
            data = dict()

            for row_key, copy_data in self._COPY_KEYS.items():
                value = mastery[row_key]

                condition = copy_data.get('condition')
                if condition is not None and not condition(mastery):
                    continue

                # Skip default values to reduce size of template
                if value == copy_data.get('default'):
                    continue

                fmt = copy_data.get('format')
                if fmt:
                    value = fmt(value)
                data[copy_data['template']] = value

            stat_ids = []
            values = []

            j = 0
            for i in range(0, self._MAX_STAT_ID):
                try:
                    stat = mastery['StatsKeys'][i]
                except IndexError:
                    break
                j = i + 1
                stat_ids.append(stat['Id'])
                data['stat%s_id' % j] = stat['Id']
                values.append(mastery['Stat%sValue' % j])
                data['stat%s_value' % j] = mastery['Stat%sValue' % j]

            data['stat_text'] = '<br>'.join(self._get_stats(
                stat_ids, values,
                translation_file='passive_skill_stat_descriptions.txt' # this might be wrong
            ))

            # # For now this is being added to the stat text
            # for ps_buff in mastery['PassiveSkillBuffsKeys']:
            #     stat_ids = [stat['Id'] for stat in
            #                 ps_buff['BuffDefinitionsKey']['StatsKeys']]
            #     values = ps_buff['Buff_StatValues']
            #     #if passive['Id'] == 'AscendancyChampion7':
            #     #    index = stat_ids.index('damage_taken_+%_from_hits')
            #     #    del stat_ids[index]
            #     #    del values[index]
            #     for i, (sid, val) in enumerate(zip(stat_ids, values)):
            #         j += 1
            #         data['stat%s_id' % j] = sid
            #         data['stat%s_value' % j] = val

            #     text = '<br>'.join(self._get_stats(
            #         stat_ids, values,
            #         translation_file='passive_skill_aura_stat_descriptions.txt'
            #     ))

            #     if data['stat_text']:
            #         data['stat_text'] += '<br>' + text
            #     else:
            #         data['stat_text'] = text

            cond = WikiCondition(
                data=data,
                cmdargs=parsed_args,
            )

            r.add_result(
                text=cond,
                out_file='mastery_%s.txt' % data['id'],
                wiki_page=[
                    {
                        'page': 'Mastery:' + self._format_wiki_title(data['id']),
                        'condition': cond,
                    },
                ],
                wiki_message='Mastery updater',
            )

        return r

# =============================================================================
# Functions
# =============================================================================
