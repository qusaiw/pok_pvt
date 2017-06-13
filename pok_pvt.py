#!/usr/bin/env python
"""reads a collection of retention PVTs and produces the full POK pvts required"""
import argparse
import sys
import re
from collections import defaultdict

parser = argparse.ArgumentParser(formatter_class=argparse.RawTextHelpFormatter, description=__doc__)
parser.add_argument('pvts_file', nargs=1, help="file containing the names of the ret PVTs in different lines")
args = parser.parse_args()


def read_list():
    """
    Reads the provided list file
    :return: a list of pvt names
    """
    try:
        f = open(args.pvts_file[0], 'r').readlines()
        pvt_list = [i.strip() for i in f if len(i.strip())]
        if any('_' in pvt for pvt in pvt_list):
            sys.exit("Some PVTs seem to be in wrong format\nPlease provide retention PVTs only")
        return pvt_list
    except IOError:
        sys.exit("Error in reading PVTs file")


def combinations(pvt_list):
    """
    Reads a list of PVTs and computes all combinations required to make POK list
    :param pvt_list: list of retention PVT names
    :return: a list of all POK PVTs sorted by type ass entered in sort order
    """
    groups = defaultdict(list)
    pvt_name = re.compile(r'([a-z]+)(\d+p\d+v)(n?\d+c)')

    # translates floating number to the format the input voltage is written in (i0p25v)
    def float_to_string(f):
        return '_i' + str(f).replace('.', 'p') + 'v'

    for pvt in pvt_list:
        # parts is a list that contains the process, voltage and temperature in that order
        parts = pvt_name.search(pvt).groups()
        # translates the voltage from the pvt format (1p25v) to a regular floating number
        voltage = float(parts[1].strip('v').replace('p', '.'))
        if len(parts) != 3:
            sys.exit("Some PVTs seem to be in an unrecognized format\n first found:%s" % pvt)
        # creates groups based on the process (parts[0]) and temperature (parts[1])
        group = parts[0] + parts[2]
        # saves PVTs names and voltages as floats inside each group
        groups[group].append((pvt, voltage))
    new_groups = []
    for group in groups:
        # sorts each group by their voltages
        groups[group].sort(key=lambda i: i[1])
        for n, pvt in enumerate(groups[group]):
            new_groups.extend([pvt[0], 'pg_' + pvt[0], 'ulvl_' + pvt[0], 'dlvl_' + pvt[0]])
            # now that the PVTs are sorted, dlvl with input voltage gets all the voltages of the latter PVTs
            dlvl_i = [('dlvl_' + pvt[0] + float_to_string(i[1])) for i in groups[group][n + 1:]]
            # ulvl here takes the input voltages from all the ones lower than the one we're at
            ulvl_i = [('ulvl_' + pvt[0] + float_to_string(i[1])) for i in groups[group][:n]]
            new_groups.extend(dlvl_i + ulvl_i)
    # sorts PVTs by type
    sort_order = {'ret': 1, 'ulvl': 2, 'dlvl': 3, 'pg': 4}
    new_groups.sort(key=lambda i: sort_order[i.split('_')[0]] if '_' in i else sort_order['ret'])
    return new_groups


def main():
    pvt_list = read_list()
    pok_list = combinations(pvt_list)
    f = open('pok_pvts', 'w+')
    f.write('\n'.join(pok_list))


if __name__ == '__main__':
    main()
