#!/usr/bin/env python2

#
# Statistics plotter for Qubes OS infrastructure.
# Copyright (C) 2015  Wojtek Porczyk <woju@invisiblethingslab.com>
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

from __future__ import print_function

import argparse
import datetime
import distutils.version
import json
import logging
import logging.handlers
import os
import sys

import dateutil.parser

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates
import matplotlib.ticker


MM = 1 / 25.4
DPI = 300.0

parser = argparse.ArgumentParser()

parser = argparse.ArgumentParser()
parser.add_argument('--datafile', metavar='FILE',
    default=os.path.expanduser('~/.stats.json'),
    help='location of the data file (default: %(default)s)')

parser.add_argument('--output', metavar='PATH',
    default=os.path.expanduser('~/public_html/counter/stats'),
    help='location of the output files (default: %(default)s)')

x_major_locator = matplotlib.dates.MonthLocator()
x_major_formatter = matplotlib.dates.DateFormatter('%Y-%m')
y_major_formatter = matplotlib.ticker.ScalarFormatter()

#TANGO = {
#    'Aluminium1': '#2e3436',
#    'ScarletRed1': '#a40000',
#    'ScarletRed2': '#cc0000',
#    'Plum1': '#5c3566',
#    'SkyBlue1': '#204a87',
#    'Chameleon1': '#4e9a06',
#}
#
#COLOURS = {
#    'r1': TANGO['Aluminium1'],
#    'r2': TANGO['Plum1'],
#    'r2-beta2': TANGO['Aluminium1'],
#    'r2-beta3': TANGO['Aluminium1'],
#    'r3.0': TANGO['Chameleon1'],
#    'r3.1': TANGO['SkyBlue1'],
#}

COLOURS = {
    'r1': '#666666',
    'r2': '#9f389f',
    'r2-beta2': '#666666',
    'r2-beta3': '#666666',
    'r3.0': '#5ad840',
    'r3.1': '#63a0ff',
}


logging.addLevelName(25, 'NOTICE')
class BetterSysLogHandler(logging.handlers.SysLogHandler):
    priority_map = logging.handlers.SysLogHandler.priority_map.copy()
    priority_map['NOTICE'] = 'notice'

def excepthook(exctype, value, traceback):
    logging.exception('exception')
    return sys.__excepthook__(exctype, value, traceback)

def setup_logging(level=25):
    handler = BetterSysLogHandler(address='/var/run/log')
    handler.setFormatter(
        logging.Formatter('%(module)s[%(process)d]: %(message)s'))
    logging.root.addHandler(handler)

#   handler = logging.StreamHandler(sys.stderr)
#   handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
#   logging.root.addHandler(handler)

    sys.excepthook = excepthook
    logging.root.setLevel(level)


def main():
    setup_logging()
    args = parser.parse_args()
    stats = json.load(open(args.datafile))

    meta = stats['meta']
    del stats['meta']

    logging.log(25, 'loaded datafile {!r}, last updated {!r}'.format(
        args.datafile, meta['last-updated']))

    all_versions = set()
    for month in stats.values():
        all_versions.update(month)
    all_versions.discard('any')
    all_versions = list(sorted(all_versions,
        key=distutils.version.LooseVersion))

    fig = matplotlib.pyplot.figure(figsize=(160 * MM, 120 * MM), dpi=DPI)
    ax = fig.add_axes((.12, .12, .85, .80))
    ax.xaxis.set_major_locator(x_major_locator)
    ax.xaxis.set_major_formatter(x_major_formatter)
    ax.yaxis.set_major_formatter(y_major_formatter)
    ax.tick_params(labelsize='small')

    months = list(sorted(stats))
    ax.set_xlim(
        dateutil.parser.parse(months[ 0]).replace(day=1)
            - datetime.timedelta(days=20),
        dateutil.parser.parse(months[-1]).replace(day=1)
            + datetime.timedelta(days=20))

    ax.set_ylabel('Unique IP addresses')

    for spine in ('top', 'bottom', 'left', 'right'):
        ax.spines[spine].set_linewidth(0.5)

#   ax.set_xlim
    ax.grid(True, which='major', linestyle=':', alpha=0.7)

    bar_width = 25.0 / len(all_versions)
    for i in range(len(all_versions)):
        version = all_versions[i]
        offset = datetime.timedelta(
            days=25.0 * (float(i) / len(all_versions) - 0.5))
        data = []
        for month, mdata in sorted(stats.items()):
            if version in mdata:
                data.append((
                    dateutil.parser.parse(month).replace(day=1) + offset,
                    mdata[version]))

        ax.bar(*zip(*data), label=version,
            color=COLOURS.get(version, '#ff0000'), #TANGO['ScarletRed1']),
            width=bar_width,
            linewidth=0.5)

    data = []
    for month, mdata in sorted(stats.items()):
        data.append((dateutil.parser.parse(month).replace(day=1), mdata['any']))
    ax.plot(*zip(*data), label='any', color='#e79e27', linewidth=3)
        #TANGO['ScarletRed2'])

    fig.text(0.02, 0.02,
        'last updated: {meta[last-updated]}\n{meta[source]}'.format(meta=meta),
        size='x-small', alpha=0.5)
    fig.text(0.98, 0.02,
        'Stats are based on counting the number of unique IPs\n'
        'connecting to the Qubes updates server each month.',
        size='x-small', alpha=0.5, ha='right')

    plt.legend(loc=2, ncol=2, prop={'size': 8}, ).get_frame().set_linewidth(0.5)
    plt.title(meta['title'])
    fig.savefig(args.output + '.png', format='png')
    fig.savefig(args.output + '.svg', format='svg')
    plt.close()



if __name__ == '__main__':
    main()

# vim: ts=4 sts=4 sw=4 et
