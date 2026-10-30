"""Writes repo/README.md, LICENSE, jurisdiction.json from corpus.json."""
import json
import os

from state_lib import write_docs

HERE = os.path.dirname(os.path.abspath(__file__))
c = json.load(open(os.path.join(HERE, 'corpus.json'), encoding='utf-8'))
last = lambda a: len(a['versions'][-1]['units'])
const = [a for a in c['acts'] if a['slug'].startswith('constitution-')]
rows = [('constitution-*/', 'Constitution of Tennessee, one folder per article (and the preamble, schedule and ordinance)', sum(len(a['versions']) for a in const),
         f'{len(const)} folders, {sum(last(a) for a in const)} provisions, releases 72-76')]
for t, name in (('39', 'Criminal Offenses'), ('48', 'Corporations'), ('66', 'Property')):
    acts = [a for a in c['acts'] if a['slug'].startswith(f'title-{t}-chapter-')]
    rows.append((f'title-{t}-chapter-*/', f'Tennessee Code, Title {t}: {name}, one folder per chapter', sum(len(a['versions']) for a in acts),
                 f'{len(acts)} chapters, {sum(last(a) for a in acts)} sections, releases 72-76'))
write_docs(HERE, {
    'name': 'United States (Tennessee)', 'state': 'Tennessee', 'code': 'US-TN', 'slug': 'tennessee',
    'domain': 'gov.tn', 'acts_table': rows,
    'source': 'The five bulk releases (72 to 76) of the Official Code of Tennessee Annotated that the State issued between 2020-09-01 and 2021-05-21, as [posted on the Internet Archive](https://archive.org/details/gov.tn.tca) by Public.Resource.Org, which is the source of the bytes. English. Only the statute text is taken: each section\'s heading, text and history line (the Acts that enacted and amended it). The annotations (Sentencing Commission Comments, Compiler\'s Notes, Amendments, Cross-References, Law Reviews, Attorney General Opinions, Notes to Decisions) are not.',
    'dates': 'Each version is dated the day its release was issued: 2020-09-01 (release 72), 2020-09-30 (73), 2020-12-22 (74), 2021-02-04 (75) and 2021-05-21 (76). A release date is not the day the changes in it took effect, and the Acts behind each change are not credited, so every change after the first release is committed by the publisher as "unexplained". A release identical to the one before for a chapter is not a version.',
    'limits': 'This is a 2020-2021 record, not the Tennessee Code as it stands today. The Internet Archive holds no release after 2021-05-21, and the current Code is published by LexisNexis on a free-access site behind a click-through agreement, which this build does not use. Only the Constitution and Titles 39, 48 and 66 are included. Amendments after 2021-05-21 are missing.',
    'license': """Source of the bytes: Public.Resource.Org's posting of the Official Code of Tennessee Annotated, releases 72-76, on the Internet Archive (https://archive.org/details/gov.tn.tca), retrieved 2026-10-30.

Statute text is not copyrightable: under the government edicts doctrine, as the Supreme Court applied it in Georgia v.
Public.Resource.Org, Inc., 590 U.S. 255 (2020), no one holds copyright in the laws that legislators make in their
official capacity. The Archive item carries a public domain mark and states that the Code "is an Edict of Government
and thus is in the Public Domain"; each file says "This document is not subject to copyright and is in the public
domain". archive.org/robots.txt disallows only /control/ and /report/. The annotations in the releases are not used.""",
})
