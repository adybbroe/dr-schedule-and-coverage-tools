#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2022 Adam Dybbroe

# Author(s):

#   Adam Dybbroe <Firstname.Lastname@smhi.se>

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


import os
from .pmw_data_coverage import get_sats_within_horizon
from .pmw_data_coverage import NRK, SDK, BLACK_RIDGE
from .pmw_data_coverage import find_actual_tlefile
from datetime import datetime, timedelta
from pyresample import load_area
import numpy as np
import csv

# EUMETSAT Reception priorities:
SAT_RECEPTION_PRIOLIST = {'Metop-C': 1,
                          'Metop-B': 4,
                          'NOAA-20': 5,
                          'Suomi-NPP': 2,
                          'FY-3D': 7,
                          'NOAA-18': 6,
                          'NOAA-18': 3}


class ReceptionsConflictResolution():
    """Take a time sorted reception list and resolve conflicts."""

    def __init__(self, sorted_passlist):
        self._raw_sorted = sorted_passlist

        self.passlist = self._get_annotated_pass_list()
        self.receptions = []
        self.rejections = []

    def _get_annotated_pass_list(self):
        """Get annotated pass list from sorted passlist."""
        passlist_dict = {}
        for idx, overpass in enumerate(self._raw_sorted):
            apass = {'start': overpass[0], 'end': overpass[1], 'platform_name': overpass[2],
                     'conflicts': []}
            passlist_dict['pass_%.3d' % idx] = apass

        return passlist_dict

    def check_for_conflicts(self):
        """Check the passlist for possible conflicts and for each pass add the list of conflicting passes."""
        pass_ids = list(self.passlist.keys())
        number_of_passes = len(pass_ids)

        for idx, pass_id in enumerate(pass_ids):
            is_overlap = True
            overlapping_passes = []
            next_id = idx + 1
            while is_overlap and next_id < number_of_passes:
                next_pass_id = pass_ids[next_id]
                is_overlap = passes_overlap(self.passlist[pass_id],
                                            self.passlist[next_pass_id])
                if is_overlap:
                    overlapping_passes.append(next_pass_id)
                next_id = next_id + 1

            is_overlap = True
            next_id = max(0, idx - 1)
            while is_overlap and next_id >= 0:
                next_pass_id = pass_ids[next_id]
                is_overlap = passes_overlap(self.passlist[pass_id],
                                            self.passlist[next_pass_id])
                if is_overlap:
                    overlapping_passes.append(next_pass_id)
                next_id = next_id - 1

            self.passlist[pass_id]['conflicts'] = overlapping_passes

    def resolve_conflicts(self):
        """Resolve the conflicts, and store passes for reception in a seperate list."""
        pass_ids = list(self.passlist.keys())
        number_of_passes = len(pass_ids)

        for idx, pass_id in enumerate(pass_ids):
            # Check on all conflicts:
            if len(self.passlist[pass_id]['conflicts']) == 0:
                self.receptions.append(pass_id)
                continue

            platform_name = self.passlist[pass_id]['platform_name']
            rejected = False
            for confl_pass in self.passlist[pass_id]['conflicts']:
                confl_platform_name = self.passlist[confl_pass]['platform_name']
                if (SAT_RECEPTION_PRIOLIST.get(platform_name, 999) >
                        SAT_RECEPTION_PRIOLIST.get(confl_platform_name, 999)):
                    rejected = True
                    break

            if rejected:
                self.rejections.append(pass_id)
            else:
                self.receptions.append(pass_id)


def passes_overlap_dict(pass1, pass2):
    """Check if two passes overlap/conflicts.

    pass1 and pass2 are dicts.
    """
    if pass1['end'] < pass2['end'] and pass1['end'] > pass2['start']:
        return True
    if pass2['end'] < pass1['end'] and pass2['end'] > pass1['start']:
        return True
    if pass1['start'] > pass2['start'] and pass1['start'] < pass2['end']:
        return True
    if pass2['start'] > pass1['start'] and pass2['start'] < pass1['end']:
        return True

    return False


def passes_overlap_list(pass1, pass2):
    """Check if two passes overlap/conflicts.

    pass1 and pass2 are lists, with start and end times and platform name in
    that order.
    """
    if pass1[1] < pass2[1] and pass1[1] > pass2[0]:
        return True
    if pass2[1] < pass1[1] and pass2[1] > pass1[0]:
        return True
    if pass1[0] > pass2[0] and pass1[0] < pass2[1]:
        return True
    if pass2[0] > pass1[0] and pass2[0] < pass1[1]:
        return True

    return False


def passes_overlap(pass1, pass2):
    """Check if two passes overlap/conflicts."""
    if isinstance(pass1, dict):
        return passes_overlap_dict(pass1, pass2)
    elif isinstance(pass1, list):
        return passes_overlap_list(pass1, pass2)


def merge_two_passes(pass1, pass2):
    """Merge two overlapping passes of the same satellite."""
    starttime = min(pass1[0], pass2[0])
    endtime = max(pass1[1], pass2[1])
    return [starttime, endtime, pass1[2]]


def merge_passes_one_satellite(allpasses):
    """Take a passlist of one satellite only and merge overlapping passes."""
    newlist = []
    num_of_passes = len(allpasses)
    idx = 0
    apass = allpasses[0]
    while idx < num_of_passes:
        if idx == num_of_passes - 1:
            newlist.append(apass)
            break

        nextpass = allpasses[idx+1]
        overlaps = passes_overlap(apass, nextpass)
        if overlaps:
            newpass = merge_two_passes(apass, nextpass)
            newlist.append(newpass)
            idx = idx+2
        else:
            newlist.append(apass)
            idx = idx+1

        if idx < num_of_passes:
            apass = allpasses[idx]

    if len(newlist) == len(allpasses):
        return newlist
    else:
        return merge_passes_one_satellite(newlist)


def calculate_total_minutes_received(passlist):
    """Take a list of passes for one satellite and calculate the total minutes received."""
    passlist = merge_passes_one_satellite(passlist)
    total_minutes = 0
    for apass in passlist:
        minutes_one_pass = (apass[1] - apass[0]).total_seconds()/60.
        total_minutes = total_minutes + minutes_one_pass

    return total_minutes


class CreateReceptionList():
    """Create  a list of possible satellite receptions at station."""

    def __init__(self, platform_names, time_window, location):
        self.start = time_window[0]
        self.end = time_window[1]
        self.location = location
        self.platforms = platform_names
        self.center_id = 'SMHI'

        self._tlefile = None
        self.nhours = int((self.end - self.start).total_seconds() / 3600.)
        self.sorted_passlist = []

        self.receptions = []
        self.rejected = []

    def get_passes(self, tle_file):
        """Get all passes within horizon and time window."""
        delta_t = timedelta(seconds=1800)
        self._tlefile = tle_file
        self._satpass_list = get_sats_within_horizon(self.platforms, self.start - delta_t,
                                                     forward=self.nhours, tle_filename=self._tlefile,
                                                     location=self.location)

        self.sorted_passlist = self._get_sorted_satpasslist()

    def _get_sorted_satpasslist(self):
        """Sort the satellite pass list by time."""
        sorted_passlist = []
        for satname in self.platforms:
            for item in self._satpass_list[satname]:
                sorted_passlist.append([item[0],
                                        item[1],
                                        satname])

        sorted_passlist.sort()
        return sorted_passlist

    def generate_csv_file(self, output_filename):
        """Generate a file with comma separated items."""
        rows = []
        for item in self.sorted_passlist:
            rows.append('%s,%s,%s' % (item[0].strftime('%Y-%m-%d %H:%M'),
                                      item[1].strftime('%Y-%m-%d %H:%M'),
                                      item[2]))

        with open(output_filename, 'w') as fpt:
            wrt = csv.writer(fpt, delimiter=',')
            wrt.writerows([x.split(',') for x in rows])

# ----------------
