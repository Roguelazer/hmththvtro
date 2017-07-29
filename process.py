#!/usr/bin/env python

from __future__ import print_function

try:
    import ujson as json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        import json

import argparse
import codecs
import collections
import datetime
import itertools
import os
import operator
import re
import sys

import dateutil.parser
import jinja2


REPEAL_REGEXES = (
    re.compile(r'(repeal|deauthorize|defund).*(patient protection|affordable care act|obamacare)', re.I),
    re.compile(r'prohibit .* from enforcing the Patient Protection and Affordable Care Act', re.I),
    re.compile(r'no.*Internal Revenue Service.*carry out.* Patient Protection and Affordable Care Act', re.I),
    re.compile(r'To prevent implementation and enforcement of Obamacare.', re.I),
    re.compile(r'restoring americans. healthcare freedom', re.I),
    re.compile(r'repeal the requirements added by the Patient Protection and Affordable Care Act', re.I),
    re.compile(r'American Health Care Act', re.I),
)

PPACA_BILL_ID = 'hr3590-111'

# most of these are attempts to repeal some Medicare portion of the ACA
NOT_REPEAL_BILL_IDS = frozenset([
    'hr1270-114',
    'hr1580-112',
    'hr2453-113',
    'hr452-112',
    'hr584-112',
    'hr6303-111',
    'hr1159-112',
    'hr763-113',
    'hr351-113',
    'hr1190-114',
    'hr1370-112',
    'hr6502-111',
    'hr928-114',
    'hr2835-113',
    'hr588-114',
    'hr2488-114',
    'hr1213-112',
    'hr3633-112',
    'hr5433-111',  # this one seems extra scummy
    'hr5110-113',
])

DEFINITELY_REPEAL_BILL_IDS = frozenset([
    'hr683-114',
    'hr5570-111',
    'hr2087-113',
])


if sys.version_info < (3, 0):
    iteritems = dict.iteritems
else:
    iteritems = dict.items


def is_repeal(hr_summary_dict):
    if hr_summary_dict['bill_id'] in NOT_REPEAL_BILL_IDS:
        return False
    if hr_summary_dict['bill_id'] in DEFINITELY_REPEAL_BILL_IDS:
        return True
    titles = [hr_summary_dict.get(f) for f in ('official_title', 'short_title')]
    titles = map(lambda x: x.lower() if x else '', titles)
    if any(any(r.search(title) for r in REPEAL_REGEXES) for title in titles):
        return True
    if any('nobamacare' in title for title in titles):
        return True
    if any('defund obamacare' in title for title in titles):
        return True
    return False


def get_vote_dict(roll_number, vote_source_directory):
    path = os.path.join(vote_source_directory, 'h%s' % roll_number, 'data.json')
    with open(path, 'r') as f:
        vote = json.load(f)
    by_party = collections.defaultdict(collections.Counter)
    by_result = collections.Counter()
    for vote_type, votes in iteritems(vote['votes']):
        for vote_item in votes:
            by_party[vote_type][vote_item['party']] += 1
            by_result[vote_type] += 1
    return {
        'result': vote['result'],
        'by_party': dict((k, dict(v)) for (k, v) in by_party.items()),
        'by_result': dict(by_result),
    }


def parse_hrs(congress_num, source_directory, vote_source_directory):
    if os.path.exists(os.path.join(source_directory, '.summary')):
        pass
    else:
        for house_resolution in os.listdir(source_directory):
            with open(os.path.join(source_directory, house_resolution, 'data.json'), 'r') as f:
                data = json.load(f)
            if is_repeal(data):
                vote = None
                for action in sorted(data['actions'], key=operator.itemgetter('acted_at')):
                    if action['type'] != 'vote':
                        continue
                    vote = get_vote_dict(action['roll'], vote_source_directory)
                yield {
                    'congress': congress_num,
                    'bill_id': data['bill_id'],
                    'resolution': data,
                    'vote': vote
                }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-w', '--write-summary', action='store_true', help='Write summary of repeals (for debugging)')
    parser.add_argument('data_directory', help='Directory containing all house resolutions and votes')
    args = parser.parse_args()

    data_directory = os.path.realpath(os.path.expanduser(args.data_directory))

    legislators_by_thomas_id = {}
    legislator_affiliations = collections.defaultdict(set)
    for legislator in itertools.chain(
        json.load(open(os.path.join(data_directory, 'legislators-current.json'))),
        json.load(open(os.path.join(data_directory, 'legislators-historical.json')))
    ):
        if 'thomas' in legislator['id']:
            thomas_id = legislator['id']['thomas']
            legislators_by_thomas_id[thomas_id] = legislator
            for term in legislator.get('terms'):
                affiliation = '%s-%s' % (
                    term['party'][0],
                    term['state']
                )
                legislator_affiliations[thomas_id].add(affiliation)

    context = {
        'repeals': [],
        'last_update': datetime.datetime(1970, 1, 1),
        'sponsors': collections.defaultdict(list),
        'legislators_by_thomas_id': legislators_by_thomas_id,
        'legislator_affiliations': legislator_affiliations,
        'ALL_PARTIES': ['D', 'R'],
        'PARTY_MAP': {'D': 'democrat', 'R': 'republican', 'I': 'independent'},
    }

    with codecs.open('hmththvtro.tmpl', encoding='utf-8', errors='replace') as jtf:
        template = jinja2.Template(jtf.read())

    summary_file = os.path.join(data_directory, 'summary')

    if os.path.exists(summary_file):
        repeals = json.load(open(summary_file, 'r'))
    else:
        repeals = []
        for congress in os.listdir(os.path.join(data_directory, 'hr')):
            congress_num = int(congress)
            hr_directory = os.path.join(data_directory, 'hr', congress)
            vote_directory = os.path.join(data_directory, 'votes', congress)
            repeals = itertools.chain(repeals, parse_hrs(congress_num, hr_directory, vote_directory))

        if args.write_summary:
            with open(summary_file, 'w') as f:
                repeals = list(repeals)
                f.write(json.dumps(list(repeals)))

    for repeal in sorted(repeals, key=lambda h: h['resolution']['introduced_at']):
        if not is_repeal(repeal['resolution']):
            continue
        this_date = dateutil.parser.parse(repeal['resolution']['introduced_at'])
        repeal['date'] = this_date
        context['last_update'] = this_date
        context['repeals'].append(repeal)
        for sponsor in repeal['resolution']['cosponsors'] + [repeal['resolution']['sponsor']]:
            # ignore people who withdrew their sponsorship
            if sponsor.get('withdrawn_at') is not None:
                continue
            if 'thomas_id' in sponsor:
                context['sponsors'][sponsor['thomas_id']].append(repeal['bill_id'])

    # XXX: sort by number of bills sponsored here instead of the teamplate because I can't figure out how to do it in
    # Jinja
    context['sponsors'] = list(sorted(
        iteritems(context['sponsors']),
        key=lambda kv: len(kv[1]),
        reverse=True
    ))

    context['count'] = len(context['repeals'])
    context['cost'] = context['count'] * 435 * 174000 / 225

    print(template.render(context).encode('utf-8'))


if __name__ == '__main__':
    main()
