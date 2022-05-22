#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2020, 2021, 2022 Adam.Dybbroe

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

"""Calculate the total percentage area coverage of PMW data available over a
given domain during a given time interval.

"""

import numpy as np
from glob import glob
import os
from datetime import datetime, timedelta
from collections.abc import Sequence

from trollsched.satpass import Pass
from trollsched.drawing import save_fig, show
from pyorbital.orbital import Orbital
from pyresample.boundary import AreaDefBoundary
from pyresample import load_area
from pyorbital import tlefile
from trollsift import Parser, globify
from pyresample.spherical_utils import GetNonOverlapUnions


AREA_DEF_FILE = '/home/a000680/usr/src/pytroll-config/etc/areas.yaml'
#AREAID = 'euron1'
#AREAID = 'arome3km'
AREAID = 'se_north'

# Location = Longitude (deg), Latitude (deg), Altitude (km)
NRK = (16.148649, 58.581844, 0.052765)
SDK = (26.632, 67.368, 0.18)
BLACK_RIDGE = (-50.62074, 66.99571, 0.4)

TLE_REALTIME_ARCHIVE = "/data/24/saf/polar_in/tle"
TLE_LONGTIME_ARCHIVE = "/data/lang/satellit/polar/orbital_elements/TLE"

INSTRUMENTS = {'Metop-A': 'mhs',
               'Metop-B': 'mhs',
               'Metop-C': 'mhs',
               'NOAA-18': 'mhs',
               'NOAA-19': 'mhs',
               'Suomi-NPP': 'atms',
               'NOAA-20': 'atms',
               'FY-3C': 'mwhs-2',
               'FY-3D': 'mwhs-2'}

# tle-202103222030.txt
tlepattern = 'tle-{time:%Y%m%d%H%M}.txt'
tlepattern2 = 'tle-{time:%Y%m%d}.txt'


def find_valid_file_from_list(parse_obj, obstime, tlefiles, tol_sec):

    found_file = None
    tlefiles.sort()
    seconds_dist = timedelta(days=10).total_seconds()
    for filepath in tlefiles[::-1]:
        res = parse_obj.parse(os.path.basename(filepath))
        dsecs = abs((res['time'] - obstime).total_seconds())

        if dsecs < seconds_dist:
            seconds_dist = dsecs
            found_file = filepath

        if seconds_dist < tol_sec:
            break

    return found_file


def find_actual_tlefile(obstime):
    """Given a time find the tle-file with the timestamp closest in time and return filename."""

    tlefiles = glob(os.path.join(TLE_REALTIME_ARCHIVE, globify(tlepattern)))

    p__ = Parser(tlepattern)
    found_file = None
    tol_sec = 3600

    found_file = find_valid_file_from_list(p__, obstime, tlefiles, tol_sec)
    if not found_file:
        for pattern in [tlepattern, tlepattern2]:
            p__ = Parser(pattern)
            tlefiles_archive = glob(os.path.join(TLE_LONGTIME_ARCHIVE + obstime.strftime("/%Y%m"), globify(pattern)))
            found_file = find_valid_file_from_list(p__, obstime, tlefiles_archive, tol_sec)
            if found_file:
                break

    return found_file


def get_sats_within_horizon(satnames, obstime, forward=1, tle_filename=None, location=NRK):
    """For a given time find all passes for a list of satellites within the horizon of a given location."""

    passes = {}
    local_horizon = 0
    for satname in satnames:
        satorb = Orbital(satname, tle_file=tle_filename)
        passlist = satorb.get_next_passes(obstime,
                                          forward,
                                          *location,
                                          horizon=local_horizon)

        passes[satname] = passlist

    return passes


def create_passes_inside_time_window(allpasses, instruments, time_left, time_right, tle_filename):
    """Go through list of passes and adapt passes so they are fully inside the relevant time window."""

    passes = []
    for satname in allpasses:
        for mypass in allpasses[satname]:
            rtime, ftime, uptime = mypass
            time_start = max(rtime, time_left)
            time_end = min(ftime, time_right)
            sensor = instruments.get(satname, 'mhs')
            if time_start > time_end:
                continue
            print(satname, sensor, rtime, ftime, time_start, time_end)
            passes.append(create_pass(satname, sensor,
                                      time_start, time_end, tle_filename))

    return passes


def create_pass(satname, instrument, starttime, endtime, tle_filename=None):
    """Create a satellite pass given a start and an endtime."""
    tle = tlefile.Tle(satname, tle_file=tle_filename)
    cpass = Pass(satname, starttime, endtime, instrument=instrument, tle1=tle.line1, tle2=tle.line2)

    return cpass


def draw_overpasses_on_area(passes, area_def, plotpath="./plots", outline='-r'):

    area_boundary = AreaDefBoundary(area_def, frequency=100)
    area_boundary = area_boundary.contour_poly

    for apass in passes:
        acov = apass.area_coverage(area_def)
        # print(acov)
        # save_fig(apass, area_boundary, outline='*')
        save_fig(apass, area_boundary, directory=plotpath, outline=outline)


def get_accumulated_coverage(passes, area_boundary):
    """From a list of passes get the accumulated relative coverage of the area"""

    coverage = 0
    for mypass in passes:
        isect = mypass.boundary.contour_poly.intersection(area_boundary)
        if isect:
            coverage = coverage + isect.area()

    return coverage / area_boundary.area()


def derive_combined_coverage(passes, area_def):
    """From a sequence of satellite overpasses derived the total coverage of an area."""

    npasses = len(passes)
    if npasses == 0:
        print("No passes in time window!")
        return 0

    instruments = set({})
    mintime = 0
    maxtime = 0
    # Get the minimum and maximum times and the list of instruments involved:
    for mypass in passes:
        instruments.update({mypass.instrument})
        if mintime == 0 or mypass.risetime < mintime:
            mintime = mypass.risetime
        if maxtime == 0 or mypass.falltime > maxtime:
            maxtime = mypass.falltime

    area_boundary = AreaDefBoundary(area_def, frequency=100)
    area_boundary = area_boundary.contour_poly

    list_of_polygons = []
    for mypass in passes:
        list_of_polygons.append(mypass.boundary.contour_poly)

    non_overlaps = GetNonOverlapUnions(list_of_polygons)
    non_overlaps.merge()

    polygons = non_overlaps.get_polygons()
    pass_ids = non_overlaps.get_ids()

    coverage = 0
    for polygon in polygons:
        isect = polygon.intersection(area_boundary)
        if isect:
            coverage = coverage + isect.area()

    area_cov = coverage / area_boundary.area()
    print("Area coverage = {0}".format(area_cov))

    # instrlist = " ".join(instruments)
    # plot_title = "{N} passes between {start_time} and {end_time}".format(N=npasses,
    #                                                                      start_time=mintime.strftime(
    #                                                                          '%Y-%m-%dT%H:%M'),
    #                                                                      end_time=maxtime.strftime('%Y-%m-%dT%H:%M'))
    # plot_title = plot_title + "\nInstruments: {instrlist:s}".format(instrlist=instrlist)

    # plotfilename = "./{N}_passes_between_{start_time}_and_{end_time}.png".format(N=npasses,
    #                                                                              start_time=mintime.strftime(
    #                                                                                  '%Y%m%d%H%M'),
    #                                                                              end_time=maxtime.strftime('%Y%m%d%H%M'))

    # import matplotlib as mpl
    # import matplotlib.pyplot as plt
    # from trollsched.drawing import Mapper

    # mpl.use('Agg')
    # plt.clf()

    # outline = '-r'
    # labels = None
    # # poly_color = []
    # plot_parameters = {}

    # # Get a time to use for the nightshade:
    # for passid in pass_ids:
    #     if isinstance(passid, Sequence):
    #         avg_time = passes[passid[0]].uptime
    #     else:
    #         avg_time = passes[passid].uptime
    #     break
    #     # if isinstance(passid, int):
    #     #     avg_time = passes[passid].uptime
    #     # else:
    #     #     avg_time = passes[passid[0]].uptime
    #     # break

    # with Mapper(**plot_parameters) as mapper:
    #     mapper.nightshade(avg_time, alpha=0.2)
    #     col = '-b'
    #     for poly in polygons:
    #         lons = poly.lon
    #         lats = poly.lat
    #         draw((lons, lats), mapper, col)

    #     draw((area_boundary.lon, area_boundary.lat), mapper, outline)

    # plt.title(plot_title)
    # for label in labels or []:
    #     plt.figtext(*label[0], **label[1])

    # plt.savefig(plotfilename)

    return area_cov


def draw(lonlat, mapper, options, **more_options):
    """Draw (lon,lat) points on map."""

    lons = np.rad2deg(lonlat[0].take(np.arange(len(lonlat[0]) + 1), mode="wrap"))
    lats = np.rad2deg(lonlat[1].take(np.arange(len(lonlat[1]) + 1), mode="wrap"))

    rx, ry = mapper(lons, lats)
    mapper.plot(rx, ry, options, **more_options)


def derive_average_coverage_one_timewindow(satnames, starthour, length_minutes, dates):
    """For a given time window and one set of satellites derive the average coverage over several days."""

    areadef = load_area(AREA_DEF_FILE, AREAID)

    rel_areacov = []
    for mydate in dates:
        start_time = datetime(mydate.year, mydate.month, mydate.day) + timedelta(hours=starthour)
        end_time = (datetime(mydate.year, mydate.month, mydate.day) +
                    timedelta(hours=starthour) + timedelta(minutes=length_minutes))
        tle_file = find_actual_tlefile(start_time)

        delta_t = timedelta(minutes=5)
        nhours = int((end_time - start_time + delta_t).total_seconds()/3600. + 1)

        nextpasses = get_sats_within_horizon(satnames, start_time - delta_t, forward=nhours, tle_filename=tle_file)

        mypasses = create_passes_inside_time_window(nextpasses, INSTRUMENTS, start_time, end_time, tle_file)
        for p in mypasses:
            draw_overpasses_on_area([p, ], areadef, plotpath="/tmp/plots/")
            #save_fig(p, directory="/tmp/plots/")

        rel_areacov.append(derive_combined_coverage(mypasses, areadef))

    return np.array(rel_areacov)


if __name__ == "__main__":

    # SATS = ['Metop-B', 'Metop-C', 'Metop-A', 'NOAA-18', 'NOAA-19',
    #        'Suomi-NPP', 'NOAA-20', 'FY-3D']
    #SATS = ['Metop-C', 'Metop-B', 'Metop-A', 'NOAA-18', 'NOAA-19', 'FY-3C', 'FY-3D']
    #SATS = ['Metop-B', 'Metop-A', 'NOAA-18', 'NOAA-19']
    SATS = ['NOAA-19', 'Metop-B', 'Metop-C', 'Suomi-NPP', 'NOAA-20']
    #SATS = ['Metop-B', 'Metop-C', 'Suomi-NPP', 'NOAA-20']

    strsats_prefix = '_'.join(SATS)

    somedates = []
    # for i in range(10):
    for i in range(9, 10, 1):
        somedates.append(datetime(2020, 1, i+1).date())

    str_time_period = 'jan20'
    areacovs = {}
    # Time-window: -90 - +90min
    # Cut-off: 75min
    # Latency: 20 min
    # cycle_distance = 3.0
    # time_window_size = 180
    # cutoff = 15
    # latency = 20

    # Time-window: -30 - +30 min
    # Cut-off: +15 min
    # Latency: 20 min
    cycle_distance = 1.0
    time_window_size = 60
    cutoff = 0
    latency = 0

    minutes_ahead = time_window_size - cutoff - latency
    textstr = '\n'.join((
        'Time window: -%d to +%d' % (int(time_window_size/2),
                                     int(time_window_size/2 - cutoff)),
        'Latency: %d min' % (latency),))

    for fhour in np.arange(-time_window_size/60*0.5, 24-cycle_distance/2, cycle_distance):
        print("Hour: ", fhour)
        acov = derive_average_coverage_one_timewindow(SATS, fhour, minutes_ahead, somedates)
        areacovs[fhour + 1.5] = acov

    str_areacovs = {}
    for key in areacovs:
        str_areacovs['%3.1f' % key] = areacovs[key]

    time_window_desc = "{latency}min_{timewindow}min_{cutoff}min".format(latency=latency,
                                                                         timewindow=time_window_size,
                                                                         cutoff=cutoff)
    np.savez('./areacoverage_{sats}_{time}_{desc}.npz'.format(sats=strsats_prefix,
                                                              time=str_time_period,
                                                              desc=time_window_desc),
             **str_areacovs)

    import matplotlib.pyplot as plt
    import matplotlib.dates as mdates

    hours3 = mdates.HourLocator(byhour=range(0, 24, 3))   # every 3 hours
    hours1 = mdates.HourLocator()  # every hour
    hours_fmt = mdates.DateFormatter('%H:%M')

    x = []
    covmed = []
    covmin = []
    covmax = []
    for key in areacovs:
        dtobj = datetime(2021, 3, 1, 0) + timedelta(hours=key)
        x.append(dtobj)
        covmed.append(np.mean(areacovs[key]))
        covmin.append(areacovs[key].min())
        covmax.append(areacovs[key].max())

    x = np.array(x)
    fig = plt.figure(figsize=(12, 7))
    ax = fig.add_subplot(111)

    width = 0.015
    dt_ = timedelta(seconds=60*20)
    acov1 = ax.bar(x - dt_, covmin, width, label='minimum')
    acov2 = ax.bar(x, covmed, width, label='average')
    acov3 = ax.bar(x + dt_, covmax, width, label='maximum')

    # format the ticks
    ax.xaxis.set_major_locator(hours3)
    ax.xaxis.set_major_formatter(hours_fmt)
    ax.xaxis.set_minor_locator(hours1)
    ax.format_xdata = mdates.DateFormatter('%H:%M')

    ax.set_ylim(0, 1.2)
    ax.set_ylabel('Relative coverage')

    # these are matplotlib.patch.Patch properties
    #props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)
    props = dict(boxstyle='round', facecolor='white', alpha=0.5)
    # place a text box in upper right in axes coords
    ax.text(0.95, 0.95, textstr, transform=ax.transAxes, fontsize=14,
            horizontalalignment='right', verticalalignment='top', bbox=props)

    ax.legend(loc='upper left')
    ax.grid(True)
    fig.autofmt_xdate()

    # plt.title("PMW obs coverage at each cycle over the MetCoOp domain\n" +
    plt.title("PMW obs coverage at each cycle over northern Scandinavia\n" +
              "Sats: {sats}".format(sats=' '.join(SATS)))
    plt.tight_layout()
    plt.savefig('barplot_{prefix}_{timeperiod}_{desc}.png'.format(prefix=strsats_prefix,
                                                                  timeperiod=str_time_period,
                                                                  desc=time_window_desc))
    plt.show()
