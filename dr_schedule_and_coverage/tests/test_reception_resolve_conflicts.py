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
from dr_schedule_and_coverage.sat_receptions import merge_passes_one_satellite
from dr_schedule_and_coverage.sat_receptions import merge_two_passes
from dr_schedule_and_coverage.sat_receptions import calculate_total_minutes_received


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

EXPECTED_AFTER_CONFLICTS_IDENTIFIED = {'pass_000':
                                       {'start': datetime.datetime(2022, 3, 21, 22, 2, 40, 571967),
                                        'end': datetime.datetime(2022, 3, 21, 22, 13, 31, 600542),
                                        'platform_name': 'Metop-B', 'conflicts': []},
                                       'pass_001':
                                       {'start': datetime.datetime(2022, 3, 21, 22, 44, 52, 900537),
                                        'end': datetime.datetime(2022, 3, 21, 22, 56, 40, 669264),
                                        'platform_name': 'Suomi-NPP', 'conflicts': ['pass_002', 'pass_003']},
                                       'pass_002':
                                       {'start': datetime.datetime(2022, 3, 21, 22, 45, 14, 318336),
                                        'end': datetime.datetime(2022, 3, 21, 22, 54, 18, 809748),
                                        'platform_name': 'AWS-4', 'conflicts': ['pass_003', 'pass_001']},
                                       'pass_003':
                                       {'start': datetime.datetime(2022, 3, 21, 22, 47, 55, 860367),
                                        'end': datetime.datetime(2022, 3, 21, 22, 58, 19, 719066),
                                        'platform_name': 'FY-3D', 'conflicts': ['pass_002', 'pass_001']}}

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

PASS_LIST_AWS_OVERLAPPING = [[datetime.datetime(2022, 3, 21, 19, 31, 11, 641153),
                              datetime.datetime(2022, 3, 21, 19, 43, 25, 330605),
                              'AWS-4'],
                             [datetime.datetime(2022, 3, 21, 19, 39, 59, 571714),
                              datetime.datetime(2022, 3, 21, 19, 49, 53, 570213),
                              'AWS-4'],
                             [datetime.datetime(2022, 3, 21, 21, 6, 39, 137588),
                              datetime.datetime(2022, 3, 21, 21, 19, 15, 546503),
                              'AWS-4'],
                             [datetime.datetime(2022, 3, 21, 21, 13, 55, 987764),
                              datetime.datetime(2022, 3, 21, 21, 24, 27, 852150),
                              'AWS-4']]

PASS_LIST_AWS_OVERLAPPING_2 = [[datetime.datetime(2022, 3, 21, 11, 39, 23, 729258),
                                datetime.datetime(2022, 3, 21, 11, 51, 20, 797967),
                                'AWS-4'],
                               [datetime.datetime(2022, 3, 21, 11, 42, 13, 716539),
                                datetime.datetime(2022, 3, 21, 11, 53, 38, 950161),
                                'AWS-4'],
                               [datetime.datetime(2022, 3, 21, 11, 42, 44, 604863),
                                datetime.datetime(2022, 3, 21, 11, 50, 55, 236519),
                                'AWS-4']]


def test_create_annotated_list_of_passes():
    """Test the creation of an annotated list of passes."""
    schedule_resolver = ReceptionsConflictResolution(TEST1_SORTED_LIST)

    annotated = schedule_resolver.passlist
    assert EXPECTED_1 == annotated


def test_check_for_conflicts():
    """Test checking of the passlist for conflicts."""
    schedule_resolver = ReceptionsConflictResolution(TEST1_SORTED_LIST)
    schedule_resolver.check_for_conflicts()

    assert schedule_resolver.passlist == EXPECTED_AFTER_CONFLICTS_IDENTIFIED


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


def test_resolve_conflicts():
    """Test the resolution of conflicts."""
    schedule_resolver = ReceptionsConflictResolution(TEST1_SORTED_LIST)
    schedule_resolver.check_for_conflicts()

    assert schedule_resolver.passlist == EXPECTED_AFTER_CONFLICTS_IDENTIFIED


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


def test_resolve_conflicts():
    """Test the resolution of conflicts."""
    schedule_resolver = ReceptionsConflictResolution(TEST1_SORTED_LIST)
    schedule_resolver.check_for_conflicts()

    schedule_resolver.resolve_conflicts()

    assert schedule_resolver.rejections == ['pass_002', 'pass_003']
    assert schedule_resolver.receptions == ['pass_000', 'pass_001']


def test_merge_two_passes():
    """Test merging two overlapping passes of the same satellite."""
    pass1 = [datetime.datetime(2022, 3, 21, 19, 31, 11, 641153),
             datetime.datetime(2022, 3, 21, 19, 43, 25, 330605),
             'AWS-4']
    pass2 = [datetime.datetime(2022, 3, 21, 19, 39, 59, 571714),
             datetime.datetime(2022, 3, 21, 19, 49, 53, 570213),
             'AWS-4']

    merged = merge_two_passes(pass1, pass2)

    expected = [datetime.datetime(2022, 3, 21, 19, 31, 11, 641153),
                datetime.datetime(2022, 3, 21, 19, 49, 53, 570213),
                'AWS-4']

    assert merged == expected


def test_merge_passes_one_satellite():
    """test merging a list of passes for one satellite."""
    merged_passes = merge_passes_one_satellite(PASS_LIST_AWS_OVERLAPPING)

    expected_list = [[datetime.datetime(2022, 3, 21, 19, 31, 11, 641153),
                      datetime.datetime(2022, 3, 21, 19, 49, 53, 570213),
                      'AWS-4'],
                     [datetime.datetime(2022, 3, 21, 21, 6, 39, 137588),
                      datetime.datetime(2022, 3, 21, 21, 24, 27, 852150),
                      'AWS-4']]
    assert merged_passes == expected_list

    merged_passes = merge_passes_one_satellite(PASS_LIST_AWS_OVERLAPPING_2)

    expected_list = [[datetime.datetime(2022, 3, 21, 11, 39, 23, 729258),
                      datetime.datetime(2022, 3, 21, 11, 53, 38, 950161),
                      'AWS-4']]
    assert merged_passes == expected_list


def test_calculate_total_minutes_received():
    """Test the total minutes ereceived for a list of passes."""
    total_min = calculate_total_minutes_received(PASS_LIST_AWS_OVERLAPPING)
    assert pytest.approx(total_min, 0.05) == 36.5
