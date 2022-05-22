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

"""Tools to generate lists of possible satellite receptions for a given station and time period.
"""

import sys
from datetime import datetime, timedelta
from dr_schedule_and_coverage.sat_receptions import CreateReceptionList
from dr_schedule_and_coverage.sat_receptions import ReceptionsConflictResolution
from dr_schedule_and_coverage.stations import NRK, SDK, BLACK_RIDGE
from dr_schedule_and_coverage.sat_receptions import calculate_total_minutes_received
from dr_schedule_and_coverage.sat_receptions import merge_passes_one_satellite


def get_aws_passes_at_station(platform_list, time_window, station_coord, antennas=1):
    """Get list of received passes at a given station assuming *antennas* antennas."""
    if antennas not in [1, 2]:
        print("Only supports 1 or 2 antennas! %d antennas given." % antennas)
        sys.exis(-9)

    # Create a list of passes possible to receive
    candidate_schedule = CreateReceptionList(platform_list, time_window, station_coord)
    candidate_schedule.get_passes(tle_file)
    # candidate_schedule.generate_csv_file('./candidate_pass_list.csv')

    mypasslist = candidate_schedule.sorted_passlist
    awses_total = [apass for apass in mypasslist if apass[2] == 'AWS-4']

    schedule_resolver = ReceptionsConflictResolution(mypasslist)
    schedule_resolver.check_for_conflicts()
    schedule_resolver.resolve_conflicts()

    reception_passlist = []
    for pass_id in schedule_resolver.receptions:
        apass = schedule_resolver.passlist[pass_id]
        reception_passlist.append([apass['start'], apass['end'], apass['platform_name']])

    if antennas == 1:
        awses_received = [apass for apass in reception_passlist if apass[2] == 'AWS-4']
        return awses_received, awses_total

    rejection_passlist = []
    for pass_id in schedule_resolver.rejections:
        apass = schedule_resolver.passlist[pass_id]
        rejection_passlist.append([apass['start'], apass['end'], apass['platform_name']])

    # Run again, assuming another antenna taking care of the passes not received by the first:
    schedule_resolver = ReceptionsConflictResolution(rejection_passlist)
    schedule_resolver.check_for_conflicts()
    schedule_resolver.resolve_conflicts()
    for pass_id in schedule_resolver.receptions:
        apass = schedule_resolver.passlist[pass_id]
        reception_passlist.append([apass['start'], apass['end'], apass['platform_name']])

    reception_passlist.sort()

    awses_received_2antennas = [apass for apass in reception_passlist if apass[2] == 'AWS-4']
    return awses_received_2antennas, awses_total


if __name__ == "__main__":

    #starttime = datetime(2022, 3, 21, 22, 30)
    starttime = datetime(2022, 3, 21, 0, 0)
    endtime = datetime(2022, 3, 31, 0, 0)
    #endtime = datetime(2022, 3, 31, 0, 0)

    tle_file = "/home/a000680/data/tles/aws_weather202203210000.tle"
    #tle_file = find_actual_tlefile(starttime)

    platform_name_list = ['NOAA-19', 'NOAA-20', 'Suomi-NPP', 'Metop-B', 'Metop-C', 'FY-3D', 'AWS-4']

    aws_passes_kan, aws_total_kan = get_aws_passes_at_station(platform_name_list,
                                                              (starttime, endtime), BLACK_RIDGE, antennas=2)

    print("Kangerlussuaq:")
    print("Total AWS passes: %d, received: %d" % (len(aws_total_kan), len(aws_passes_kan)))
    print("Relative reception efficiency: %5.1f %%" % (100*len(aws_passes_kan)/len(aws_total_kan)))

    aws_passes_nrk, aws_total_nrk = get_aws_passes_at_station(platform_name_list,
                                                              (starttime, endtime), NRK, antennas=2)

    print("Norrkoping:")
    print("Total AWS passes: %d, received: %d" % (len(aws_total_nrk), len(aws_passes_nrk)))
    print("Relative reception efficiency: %5.1f %%" % (100*len(aws_passes_nrk)/len(aws_total_nrk)))

    aws_passes_sdk, aws_total_sdk = get_aws_passes_at_station(platform_name_list,
                                                              (starttime, endtime), SDK, antennas=2)

    print("Sodankyla:")
    print("Total AWS passes: %d, received: %d" % (len(aws_total_sdk), len(aws_passes_sdk)))
    print("Relative reception efficiency: %5.1f %%" % (100*len(aws_passes_sdk)/len(aws_total_sdk)))

    aws_passes_nrk_kan_sdk = aws_passes_kan + aws_passes_sdk + aws_passes_nrk
    aws_passes_nrk_kan_sdk.sort()
    total_min_actual = calculate_total_minutes_received(aws_passes_nrk_kan_sdk)

    aws_passes_nrk_kan_sdk_total = aws_total_kan + aws_total_sdk + aws_total_nrk
    aws_passes_nrk_kan_sdk_total.sort()
    total_min_potential = calculate_total_minutes_received(aws_passes_nrk_kan_sdk_total)
    print(total_min_potential, total_min_actual)

    total_merged = merge_passes_one_satellite(aws_passes_nrk_kan_sdk_total)
    merged = merge_passes_one_satellite(aws_passes_nrk_kan_sdk)

    print("Total number of possible AWS passes from all stations: %d" % len(total_merged))
    print("Number of scheduled AWS passes from all stations: %d" % len(merged))
