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

from datetime import datetime, timedelta
from dr_schedule_and_coverage.sat_receptions import CreateReceptionList
# from dr_schedule_and_coverage.stations import
from dr_schedule_and_coverage.pmw_data_coverage import NRK, SDK, BLACK_RIDGE

if __name__ == "__main__":

    starttime = datetime(2022, 3, 21, 22, 30)
    endtime = datetime(2022, 3, 22, 0, 0)
    #starttime = datetime(2022, 5, 19, 0, 0)
    #endtime = datetime(2022, 5, 20, 0, 0)

    tle_file = "/home/a000680/data/tles/aws_weather202203210000.tle"
    #tle_file = find_actual_tlefile(starttime)

    platform_name_list = ['NOAA-19', 'NOAA-20', 'Suomi-NPP', 'Metop-B', 'Metop-C', 'FY-3D', 'AWS-4']

    # Create a list of passes possible to receive
    candidate_schedule = CreateReceptionList(platform_name_list, (starttime, endtime), NRK)
    candidate_schedule.get_passes(tle_file)

    candidate_schedule.generate_csv_file('./candidate_pass_list.csv')

    mypasslist = candidate_schedule.sorted_passlist
