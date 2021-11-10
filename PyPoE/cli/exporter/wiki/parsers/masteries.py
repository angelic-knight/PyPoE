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
Parses out masteries and mastery effects into formats that are useful for the wiki


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


class EffectWikiCondition(parser.WikiCondition):
    COPY_KEYS = (
        'main_page',
    )

    NAME = 'Mastery Effect' # Seems to be the wiki template that will get called
    ADD_INCLUDE = False
    INDENT = 36

class GroupWikiCondition(parser.WikiCondition):
    COPY_KEYS = (
        'main_page',
    )

    NAME = 'Mastery Group' # Seems to be the wiki template that will get called
    ADD_INCLUDE = False
    INDENT = 36


class MasteryCommandHandler(ExporterHandler):
    def __init__(self, sub_parser, *args, **kwargs):
        super().__init__(self, sub_parser, *args, **kwargs)
        self.parser = sub_parser.add_parser(
            'mastery',
            help='Passive Skill Tree Mastery exporter',
        )
        self.parser.set_defaults(func=lambda args: self.parser.print_help())
        core_sub = self.parser.add_subparsers()

        # Export for each mastery option:
        mastery_eff_parser = core_sub.add_parser(
            'effects',
            help='Mastery exporter for mastery effects (i.e. the bonus you can actually pick)',
        )
        mastery_eff_parser.set_defaults(func=lambda args: parser.print_help())
        mastery_eff_sub = mastery_eff_parser.add_subparsers()

        self.add_default_subparser_filters(
            sub_parser=mastery_eff_sub,
            cls=MasteryEffectParser,
        )

        # Export for each mastery group:
        mastery_grp_parser = core_sub.add_parser(
            'groups',
            help='Mastery exporter for mastery groups',
        )
        mastery_grp_parser.set_defaults(func=lambda args: parser.print_help())
        mastery_grp_sub = mastery_grp_parser.add_subparsers()

        self.add_default_subparser_filters(
            sub_parser=mastery_grp_sub,
            cls=MasteryGroupParser,
        )
        # we don't support filtering right now.

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
    
    def add_default_subparser_filters(self, sub_parser, cls, *args, **kwargs):
        # By Id
        super().add_id_subparser_filters(sub_parser, cls, *args, **kwargs)

        # By row id
        super().add_rowid_subparser_filters(sub_parser, cls, *args, **kwargs)

        # Not by name because name is not available for groups or effects


class MasteryEffectParser(parser.BaseParser):
    _MASTERY_FILE_NAME = 'PassiveSkillMasteryEffects.dat'
    _files = [
        _MASTERY_FILE_NAME,
    ]

    _passive_column_index_filter = partialmethod(
        parser.BaseParser._column_index_filter,
        dat_file_name=_MASTERY_FILE_NAME,
        error_msg='Several mastery effects have not been found:\n%s',
    )

    _MAX_STAT_ID = 3 # How many stats each mastery effect can have.

    _COPY_KEYS = OrderedDict((
        ('Id', {
            'template': 'id',
        }),
    ))

    def _apply_filter(self, parsed_args, mastery_effs):
        if parsed_args.re_id:
            parsed_args.re_id = re.compile(parsed_args.re_id, flags=re.UNICODE)
        else:
            return mastery_effs

        new = []

        for mastery_eff in mastery_effs:
            if parsed_args.re_id and not \
                    parsed_args.re_id.match(mastery_eff['Id']):
                continue

            new.append(mastery_eff)

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

    def export(self, parsed_args, masteries):
        r = ExporterResult()

        masteries = self._apply_filter(parsed_args, masteries)

        if not masteries:
            console(
                'No masteries found for the specified parameters. Quitting.',
                msg=Msg.warning,
            )
            return r

        console('Accessing additional data...')

        # Read from the .dat file
        self.rr[self._MASTERY_FILE_NAME]

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

            one_based_stat_index = 0
            for stat_index in range(0, self._MAX_STAT_ID):
                try:
                    stat = mastery['StatsKeys'][stat_index]
                except IndexError:
                    break
                one_based_stat_index = stat_index + 1
                stat_ids.append(stat['Id'])
                data[f'stat{one_based_stat_index}_id'] = stat['Id']
                values.append(mastery[f'Stat{one_based_stat_index}Value'])
                data['stat{one_based_stat_index}_value'] = mastery[f'Stat{one_based_stat_index}Value']

            data['stat_text'] = '<br>'.join(self._get_stats(
                stat_ids, values,
                translation_file='passive_skill_stat_descriptions.txt'
            ))

            cond = EffectWikiCondition(
                data=data,
                cmdargs=parsed_args,
            )

            r.add_result(
                text=cond,
                out_file='mastery_%s.txt' % data['id'],
                wiki_page=[
                    {
                        'page': 'Mastery Effect:' + self._format_wiki_title(data['id']),
                        'condition': cond,
                    },
                ],
                wiki_message='Mastery updater',
            )

        return r



class MasteryGroupParser(parser.BaseParser):
    _MASTERY_FILE_NAME = 'PassiveSkillMasteryGroups.dat'
    _files = [
        _MASTERY_FILE_NAME,
    ]

    _passive_column_index_filter = partialmethod(
        parser.BaseParser._column_index_filter,
        dat_file_name=_MASTERY_FILE_NAME,
        error_msg='Several masteries have not been found:\n%s',
    )

    _COPY_KEYS = OrderedDict((
        ('Id', {
            'template': 'id',
        }),
        ('MasteryEffects', {
            'template': 'mastery_effects',
            'format': lambda value: ','.join([x['Id'] for x in value]),
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

    def export(self, parsed_args, mastery_grps):
        r = ExporterResult()

        mastery_grps = self._apply_filter(parsed_args, mastery_grps)

        if not mastery_grps:
            console(
                'No mastery groups found for the specified parameters. Quitting.',
                msg=Msg.warning,
            )
            return r

        console('Accessing additional data...')

        # Read the .dat file
        self.rr[self._MASTERY_FILE_NAME]

        console(f'Found {len(mastery_grps)}, parsing...')

        for mastery_grp in mastery_grps:
            data = dict()

            for row_key, copy_data in self._COPY_KEYS.items():
                value = mastery_grp[row_key]

                condition = copy_data.get('condition')
                if condition is not None and not condition(mastery_grp):
                    continue

                # Skip default values to reduce size of template
                if value == copy_data.get('default'):
                    continue

                fmt = copy_data.get('format')
                if fmt:
                    value = fmt(value)
                data[copy_data['template']] = value

            cond = GroupWikiCondition(
                data=data,
                cmdargs=parsed_args,
            )

            r.add_result(
                text=cond,
                out_file='mastery_group_%s.txt' % data['id'],
                wiki_page=[
                    {
                        'page': self._format_wiki_title(data['id']) + " Mastery",
                        'condition': cond,
                    },
                ],
                wiki_message='Mastery Group updater',
            )

        return r

# =============================================================================
# Functions
# =============================================================================
