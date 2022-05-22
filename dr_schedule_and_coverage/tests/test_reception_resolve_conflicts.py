#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2022 Adam.Dybbroe

# Author(s):

#   Adam.Dybbroe <a000680@c21856.ad.smhi.se>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
"""

import pytest
import datetime
from dr_schedule_and_coverage.sat_receptions import ReceptionsConflictResolution
from dr_schedule_and_coverage.sat_receptions import passes_overlap

TEST1_SORTED_LIST = [[datetime.datetime(2022, 3, 21, 22, 2, 40, 571967),
                      datetime.datetime(2022, 3, 21, 22, 13, 31, 600542),
                      'Metop-B'],
                     [datetime.datetime(2022, 3, 21, 22, 44, 52, 900537),
                      datetime.datetime(2022, 3, 21, 22, 56, 40, 669264),
                      'Suomi-NPP'],
                     [datetime.datetime(2022, 3, 21, 22, 45, 14, 318336),
                      datetime.datetime(2022, 3, 21, 22, 54, 18, 809748),
                      'AWS-4'],
                     [datetime.datetime(2022, 3, 21, 22, 47, 55, 860367),
                      datetime.datetime(2022, 3, 21, 22, 58, 19, 719066),
                      'FY-3D']]

# EXPECTED1 = [{'start': datetime.datetime(2022, 3, 21, 22, 2, 40, 571967),
#               'end': datetime.datetime(2022, 3, 21, 22, 13, 31, 600542),
#               'platform_name': 'Metop-B',
#               'pass_id': 0, 'conflicts': []},
#              {'start': datetime.datetime(2022, 3, 21, 22, 44, 52, 900537),
#               'end': datetime.datetime(2022, 3, 21, 22, 56, 40, 669264),
#               'platform_name': 'Suomi-NPP',
#               'pass_id': 1,
#               'conflicts': []},
#              {'start': datetime.datetime(2022, 3, 21, 22, 45, 14, 318336),
#               'end': datetime.datetime(2022, 3, 21, 22, 54, 18, 809748),
#               'platform_name': 'AWS-4',
#               'pass_id': 2,
#               'conflicts': []},
#              {'start': datetime.datetime(2022, 3, 21, 22, 47, 55, 860367),
#               'end': datetime.datetime(2022, 3, 21, 22, 58, 19, 719066),
#               'platform_name': 'FY-3D',
#               'pass_id': 3,
#               'conflicts': []}]

EXPECTED_1 = {'pass_000': {'start': datetime.datetime(2022, 3, 21, 22, 2, 40, 571967),
                           'end': datetime.datetime(2022, 3, 21, 22, 13, 31, 600542),
                           'platform_name': 'Metop-B', 'conflicts': []},
              'pass_001': {'start': datetime.datetime(2022, 3, 21, 22, 44, 52, 900537),
                           'end': datetime.datetime(2022, 3, 21, 22, 56, 40, 669264),
                           'platform_name': 'Suomi-NPP', 'conflicts': []},
              'pass_002': {'start': datetime.datetime(2022, 3, 21, 22, 45, 14, 318336),
                           'end': datetime.datetime(2022, 3, 21, 22, 54, 18, 809748),
                           'platform_name': 'AWS-4', 'conflicts': []},
              'pass_003': {'start': datetime.datetime(2022, 3, 21, 22, 47, 55, 860367),
                           'end': datetime.datetime(2022, 3, 21, 22, 58, 19, 719066),
                           'platform_name': 'FY-3D', 'conflicts': []}}

PASS_0 = {'start': datetime.datetime(2022, 3, 21, 22, 2, 40, 571967),
          'end': datetime.datetime(2022, 3, 21, 22, 13, 31, 600542),
          'platform_name': 'Metop-B', 'conflicts': []}
PASS_1 = {'start': datetime.datetime(2022, 3, 21, 22, 44, 52, 900537),
          'end': datetime.datetime(2022, 3, 21, 22, 56, 40, 669264),
          'platform_name': 'Suomi-NPP', 'conflicts': []}
PASS_2 = {'start': datetime.datetime(2022, 3, 21, 22, 45, 14, 318336),
          'end': datetime.datetime(2022, 3, 21, 22, 54, 18, 809748),
          'platform_name': 'AWS-4', 'conflicts': []}
PASS_3 = {'start': datetime.datetime(2022, 3, 21, 22, 47, 55, 860367),
          'end': datetime.datetime(2022, 3, 21, 22, 58, 19, 719066),
          'platform_name': 'FY-3D', 'conflicts': []}


def test_create_annotated_list_of_passes():
    """Test the creation of an annotated list of passes."""
    schedule_resolver = ReceptionsConflictResolution(TEST1_SORTED_LIST)

    annotated = schedule_resolver.passlist
    assert EXPECTED_1 == annotated


def test_check_for_conflicts():
    """Test checking of the passlist for conflicts."""
    schedule_resolver = ReceptionsConflictResolution(TEST1_SORTED_LIST)
    annotated = schedule_resolver.passlist

    pass


def test_passes_overlap_passes_do_overlap():
    """Check that the pass-overlap function returns True when two passes are overlapping."""
    overlap = passes_overlap(PASS_1, PASS_2)
    assert overlap is True
    overlap = passes_overlap(PASS_2, PASS_1)
    assert overlap is True
    overlap = passes_overlap(PASS_2, PASS_3)
    assert overlap is True
    overlap = passes_overlap(PASS_3, PASS_2)
    assert overlap is True


def test_passes_overlap_passes_dont_overlap():
    """Check that the pass-overlap function returns False when two passes do not overlapping."""
    overlap = passes_overlap(PASS_0, PASS_1)
    assert overlap is False
    overlap = passes_overlap(PASS_1, PASS_0)
    assert overlap is False
