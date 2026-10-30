"""Parse the cached Tennessee Code bulk releases (Public.Resource.Org HTML) into corpus.json.

Reads only .cache; no network. Only the statute text is taken: each section's heading, its text and the history line
(the Acts that enacted and amended it). Everything from the first annotation label onwards (Sentencing Commission
Comments, Compiler's Notes, Amendments, Effective Dates, Cross-References, Textbooks, Law Reviews, Attorney General
Opinions, Notes to Decisions) is left out.
"""
import json
import os
import re
import sys

from bs4 import BeautifulSoup, NavigableString, Tag

from state_lib import Fetcher, key, norm, sha, text_of

HERE = os.path.dirname(os.path.abspath(__file__))
F = Fetcher(HERE, 'x')
ANNOT = re.compile(r"^(Sentencing Commission Comments|Compiler.s Notes|Amendments|Effective Dates|Cross-References|Textbooks|"
                   r"Law Reviews|Attorney General Opinions|Comparative Legislation|Collateral References|Research References|"
                   r"Rules of the Supreme Court|Editor.s Notes|Cited|Repealed by|Transfers|Opinions of the Attorney General|"
                   r"NOTES TO DECISIONS|Notes to Decisions)\b\.?")
SECID = re.compile(r'^t(\d+)c(\d+[a-z]?)s(.+)$')
CONID = re.compile(r'^constitution-tn-(.+?)s(\d+[A-Za-z]?)$')


def roman(n):
    out = ''
    for v, s in ((1000, 'm'), (900, 'cm'), (500, 'd'), (400, 'cd'), (100, 'c'), (90, 'xc'), (50, 'l'), (40, 'xl'), (10, 'x'),
                 (9, 'ix'), (5, 'v'), (4, 'iv'), (1, 'i')):
        while n >= v:
            out += s
            n -= v
    return out


def letter(i):
    return chr(97 + i % 26) * (i // 26 + 1)


def label_for(ol, i):
    t = ol.get('type')
    if 'alpha' in (ol.get('class') or []) or t == 'a':
        return letter(i)
    if t == 'A':
        return letter(i).upper()
    if t == 'i':
        return roman(i + 1)
    if t == 'I':
        return roman(i + 1).upper()
    return str(i + 1)


def li_lines(li, label):
    text, nested = [], []
    for ch in li.children:
        if isinstance(ch, Tag) and ch.name in ('ol', 'ul'):
            nested.append(ch)
        elif isinstance(ch, Tag):
            text.append(norm(ch.get_text(' ')))
        else:
            text.append(norm(str(ch)))
    body = norm(' '.join(t for t in text if t))
    lead = f'({label})' if label else '-'
    sub = []
    for n in nested:
        sub += list_lines(n)
    if body:
        return [f'{lead} {body}'] + sub
    if sub:
        return [lead + sub[0]] + sub[1:]
    return [lead]


def list_lines(ol):
    out = []
    for i, li in enumerate([c for c in ol.children if isinstance(c, Tag) and c.name == 'li']):
        out += li_lines(li, label_for(ol, i) if ol.name == 'ol' else None)
    return out


def section_lines(h3):
    """The heading and statute text of one section, up to the first annotation."""
    lines = ['# ' + norm(h3.get_text(' '))]
    for el in h3.next_siblings:
        if isinstance(el, NavigableString):
            if norm(str(el)):
                lines.append(norm(str(el)))
            continue
        if el.name == 'p':
            t = norm(el.get_text(' '))
            if ANNOT.match(t):
                break
            if t:
                lines.append(t)
        elif el.name in ('ol', 'ul'):
            lines += list_lines(el)
        else:                       # a div of notes to decisions, a nav, a heading: annotations
            break
    return lines


def parse_release(rel):
    """-> {act slug: (title, {unit key: unit})} for the constitution and the three titles of one release."""
    acts, urls = {}, {}
    # Constitution
    u = rel['files']['gov.tn.tca.constitution.tn.html']
    b = F.cached(u)
    s = BeautifulSoup(b.decode('utf-8', 'replace'), 'lxml')
    names = {}
    for h2 in s.find_all('h2'):
        m = re.match(r'constitution-tn-(.+)$', h2.get('id') or '')
        if m:
            names[m.group(1)] = norm(h2.get_text(' '))
    for h3 in s.find_all('h3'):
        hid = h3.get('id') or ''
        m = CONID.match(hid)
        if m:
            art, num = m.group(1), m.group(2)
            mm = re.match(r'^a0?([IVX]+)$', art)
            slug = 'constitution-art-' + mm.group(1).lower() if mm else 'constitution-' + re.sub(r'[^a-z0-9]+', '-', art.lower()).strip('-')
            title = 'Constitution of Tennessee, ' + names.get(art, art)
            k, lab = key('sec', num, 3), 'Sec. ' + num
        else:
            slug, title = 'constitution-preamble', 'Constitution of Tennessee, Preamble and Declaration of Rights'
            k, lab = 'preamble', norm(h3.get_text(' '))[:60]
        lines = section_lines(h3)
        a = acts.setdefault(slug, (title, {}))
        if len(lines) > 1 or slug == 'constitution-preamble':
            a[1][k] = {'label': lab, 'kind': 'section', 'text': text_of(lines)}
        urls[slug] = (u, sha(b))
    for tnum in ('39', '48', '66'):
        u = rel['files'][f'gov.tn.tca.title.{tnum}.html']
        b = F.cached(u)
        s = BeautifulSoup(b.decode('utf-8', 'replace'), 'lxml')
        cnames = {}
        for h2 in s.find_all('h2'):
            m = re.match(r't(\d+)c(\d+[a-z]?)$', h2.get('id') or '')
            if m:
                cnames[m.group(2)] = re.sub(r'\s*\[Repealed\]\s*$', '', norm(h2.get_text(' ')))
        for h3 in s.find_all('h3'):
            m = SECID.match(h3.get('id') or '')
            if not m:
                continue
            _, ch, sec = m.groups()
            slug = f'title-{int(tnum):02d}-chapter-{key("", ch, 3)}'
            cname = cnames.get(ch, f'Chapter {ch}')
            title = f'Tennessee Code, Title {int(tnum)}, {cname}'
            a = acts.setdefault(slug, (title, {}))
            lines = section_lines(h3)
            if len(lines) > 1 or True:
                k = key('sec', sec, 3)
                if k in a[1]:
                    k += '-dup'
                a[1][k] = {'label': 'T.C.A. § ' + sec, 'kind': 'section', 'text': text_of(lines)}
            urls[slug] = (u, sha(b))
    return acts, urls


def main():
    man = json.load(open(os.path.join(HERE, '.cache', 'manifest.json')))
    per = []
    for rel in man['releases']:
        acts, urls = parse_release(rel)
        per.append((rel, acts, urls))
        print('release', rel['release'], rel['date'], len(acts), 'acts', sum(len(a[1]) for a in acts.values()), 'units', flush=True)
    slugs = sorted({s for _, acts, _ in per for s in acts})
    out_acts, nver = [], 0
    for slug in slugs:
        versions, prev, title = [], None, ''
        for rel, acts, urls in per:
            if slug not in acts:
                continue
            title, units = acts[slug]
            if not units:
                continue
            if prev is not None and {k: v['text'] for k, v in units.items()} == {k: v['text'] for k, v in prev.items()}:
                continue        # identical to the release before: no version
            versions.append({'from': rel['date'], 'source_url': urls[slug][0], 'sha256': urls[slug][1],
                             'units': dict(sorted(units.items())),
                             'note': f'Release {rel["release"]} of the Official Code of Tennessee Annotated, released {rel["date"]}.'})
            prev = units
        if not versions:
            continue
        nver += len(versions)
        short = 'Tenn. Const. ' + slug.split('-', 1)[1] if slug.startswith('constitution') else 'T.C.A. ' + slug.replace('title-', 'title ').replace('-chapter-', ' ch. ')
        out_acts.append({'slug': slug, 'short': short, 'title': title, 'url': versions[0]['source_url'], 'first_law': None,
                         'earlier_laws': [], 'versions': versions})
    country = {'code': 'US-TN', 'name': 'United States (Tennessee)', 'slug': 'united-states-tennessee', 'lang': 'en',
               'tz': 'America/Chicago', 'future_branch': 'future',
               'publisher': {'name': 'Tennessee Code Commission (bulk releases posted by Public.Resource.Org)', 'email': 'tca@gov.tn.invalid'},
               'default_in_force_rule': {'text': 'A version is dated the day its release of the Code was issued; the release date is not the in-force date of the changes it carries.',
                                         'source': 'https://archive.org/details/gov.tn.tca'},
               'licence_note': 'Statute text is not copyrightable (Georgia v. Public.Resource.Org, 2020). Source of the bytes: Internet Archive item gov.tn.tca (Public.Resource.Org); the releases are those the State issued.'}
    sources = [{'name': 'Official Code of Tennessee Annotated, bulk releases 72-76 (Public.Resource.Org on the Internet Archive)',
                'url': 'https://archive.org/details/gov.tn.tca', 'retrieved': '2026-10-30',
                'licence': 'Statute text carries no copyright (Georgia v. Public.Resource.Org, 2020). The item states the Code "is an Edict of Government and thus is in the Public Domain" and carries a public domain mark; each file says "This document is not subject to copyright and is in the public domain". archive.org/robots.txt disallows only /control/ and /report/.',
                'notes': 'Constitution of Tennessee and Titles 39, 48 and 66, five releases from 2020-09-01 to 2021-05-21. The annotations in these files are not taken.'}]
    decisions = [
        'Source: the five bulk releases of the Official Code of Tennessee Annotated (releases 72 to 76, 2020-09-01 to 2021-05-21), as posted on the Internet Archive by Public.Resource.Org, which is the source of the bytes. The Archive holds no later release. The current Code is on the Lexis free-access site behind a click-through agreement, which is not used.',
        'A version is dated the day its release was issued. A release date is not the day the changes in it took effect, and the Acts that made each change are not credited: every change after the first release is committed by the publisher as "unexplained".',
        'Only the statute text is taken: the section heading, the text and the history line naming the Acts. The Sentencing Commission Comments, Compiler\'s Notes, Amendments, Effective Dates, Cross-References, Textbooks, Law Reviews, Attorney General Opinions and Notes to Decisions are left out; each is cut at its first label.',
        'One act per chapter of Titles 39 (Criminal Offenses), 48 (Corporations) and 66 (Property) and one per article of the Constitution; one unit per section. A release that is identical to the one before for an act is not a version.',
        'Numbering of subdivisions is rebuilt from the list markup: nested lists give (a), (1), (A), (i) by the list type, and a list item with no text of its own is joined to the first item inside it, as in (a)(1).']
    c = {'country': country, 'sources': sources, 'laws': {}, 'acts': out_acts, 'applies': [], 'decisions': decisions, 'ai_use': ['none']}
    out = os.path.join(HERE, 'corpus.json')
    with open(out + '.tmp', 'w', encoding='utf-8', newline='\n') as f:
        json.dump(c, f, ensure_ascii=False, indent=1)
        f.write('\n')
    os.replace(out + '.tmp', out)
    print('corpus.json:', len(out_acts), 'acts,', nver, 'versions')


if __name__ == '__main__':
    sys.path.insert(0, HERE)
    main()
