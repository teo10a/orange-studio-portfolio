#!/usr/bin/env python3
"""data/cv.json 하나로 포트폴리오와 이력서의 데이터 영역을 다시 만듭니다.

  python3 build.py          # 생성 영역·sitemap·robots·llms.txt를 다시 씀
  python3 build.py --check  # 디스크 내용이 data/cv.json과 다르면 목록을 찍고 1로 종료

HTML은 손으로 쓴 그대로 두고 <!-- build:이름 --> … <!-- /build:이름 --> 사이만 바꿉니다.
같은 입력이면 같은 출력이 나오도록 정렬·고정 순서만 쓰고, 날짜는 data의 meta.updated만 씁니다.
표준 라이브러리만 씁니다.
"""
import html
import json
import re
import sys
from pathlib import Path
from string import Template
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent
CV_ROOT = ROOT.parent / 'cv' / 'hwangtaegeon-cv'
D = json.loads((ROOT / 'data' / 'cv.json').read_text('utf-8'))

PERSON = D['person']
SITES = D['sites']
PAGES = D['pages']
BIZ = D['business']
ENT = {x['id']: x for k in ('organizations', 'events', 'education', 'positions', 'works', 'series', 'films', 'tools', 'skills')
       for x in D[k]}
ENT[PERSON['id']] = PERSON
P_URL, C_URL = SITES['portfolio']['url'], SITES['cv']['url']
UPDATED = D['meta']['updated']


# ---------- 공통 도우미 ----------
def t(s):
    """텍스트 노드용 이스케이프 (따옴표는 그대로 둠)"""
    return html.escape(str(s), quote=False)


def a(s):
    """속성값용 이스케이프"""
    return html.escape(str(s), quote=True)


def num(n):
    return f'{n:,}'


def ym(s):
    """'2027-04' → '2027.04', '2026' → '2026' (화면 표기 하나로 통일)"""
    return s.replace('-', '.')


def span(start, end):
    if end is None:
        return f'{ym(start)} – 현재'
    return ym(start) if start == end else f'{ym(start)} – {ym(end)}'


def org_label(oid):
    o = ENT[oid]
    return o.get('short', o['name'])


def client_label(w):
    return w.get('clientLabel') or org_label(w['client'])


def yt_url(w):
    return f'https://www.youtube.com/watch?v={w["youtube"]}'


def iso_duration(d):
    if not d:
        return None
    m, s = d.split(':')
    return f'PT{int(m)}M{int(s)}S'


def rel(url):
    """포트폴리오 안의 주소는 상대경로로"""
    return url[len(P_URL):] if url.startswith(P_URL) else url


def by_year(items):
    """최신순 (같은 해 안에서는 데이터에 적은 순서)"""
    return sorted(items, key=lambda x: -int(x['year']))


def by_period(items):
    return sorted(items, key=lambda x: (-int(x['start'][:4]), -(int(x['end'][:4]) if x.get('end') else 9999)))


ICONS = {
    'arrow-right': '<path d="M5 12h14"/><path d="m12 5 7 7-7 7"/>',
    'arrow-up-right': '<path d="M7 7h10v10"/><path d="M7 17 17 7"/>',
    'play': '<path d="M6 3 20 12 6 21Z"/>',
    'calendar': '<rect width="18" height="18" x="3" y="4" rx="2"/><path d="M16 2v4"/><path d="M8 2v4"/><path d="M3 10h18"/>',
    'map-pin': '<path d="M20 10c0 6-8 12-8 12s-8-6-8-12a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
    'video': '<path d="m22 8-6 4 6 4V8Z"/><rect width="14" height="12" x="2" y="6" rx="2"/>',
    'palette': '<circle cx="13.5" cy="6.5" r=".5"/><circle cx="17.5" cy="10.5" r=".5"/><circle cx="8.5" cy="7.5" r=".5"/><circle cx="6.5" cy="12.5" r=".5"/><path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.93 0 1.65-.75 1.65-1.69 0-.44-.18-.84-.44-1.13-.29-.29-.44-.65-.44-1.13a1.64 1.64 0 0 1 1.67-1.67h2c3.05 0 5.55-2.5 5.55-5.55C21.97 6.01 17.46 2 12 2Z"/>',
    'link': '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>',
    'user': '<circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 0 0-16 0"/>',
    'message': '<path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2Z"/>',
    'clock': '<circle cx="12" cy="12" r="10"/><path d="M12 6v6l4 2"/>',
    'clipboard': '<rect width="8" height="4" x="8" y="2" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
    'file': '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M16 13H8"/><path d="M16 17H8"/><path d="M10 9H8"/>',
    'camera': '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3Z"/><circle cx="12" cy="13" r="3"/>',
    'eye': '<path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7S2 12 2 12Z"/><circle cx="12" cy="12" r="3"/>',
    'send': '<path d="m22 2-7 20-4-9-9-4Z"/><path d="M22 2 11 13"/>',
    'aperture': '<circle cx="12" cy="12" r="10"/><path d="m14.31 8 5.74 9.94"/><path d="M9.69 8h11.48"/><path d="m7.38 12 5.74-9.94"/><path d="M9.69 16 3.95 6.06"/><path d="M14.31 16H2.83"/><path d="m16.62 12-5.74 9.94"/>',
    'laptop': '<path d="M20 16V7a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v9m16 0H4m16 0 1.28 2.55A1 1 0 0 1 20.38 20H3.62a1 1 0 0 1-.9-1.45L4 16"/>',
    'sliders': '<path d="M21 4h-7"/><path d="M10 4H3"/><path d="M21 12h-9"/><path d="M8 12H3"/><path d="M21 20h-5"/><path d="M12 20H3"/><path d="M14 2v4"/><path d="M8 10v4"/><path d="M16 18v4"/>',
    'mail': '<rect width="20" height="16" x="2" y="4" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/>',
    'phone': '<path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.7 2.81a2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45c.91.34 1.85.57 2.81.7A2 2 0 0 1 22 16.92Z"/>',
    'instagram': '<rect width="20" height="20" x="2" y="2" rx="5"/><path d="M16 11.37A4 4 0 1 1 12.63 8 4 4 0 0 1 16 11.37Z"/><path d="M17.5 6.5h.01"/>',
    'check': '<path d="M20 6 9 17l-5-5"/>',
    'chevron-down': '<path d="m6 9 6 6 6-6"/>',
}


def icon(name):
    return (f'<svg class="ic" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" '
            f'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">{ICONS[name]}</svg>')


NEW = ' target="_blank" rel="noopener"'
EXT = '<span aria-hidden="true">↗</span><span class="sr-only">(새 창)</span>'


def mailto_template():
    body = '\n'.join(f'{b["label"]}: ' for b in BIZ['brief']) + '\n'
    return f'mailto:{PERSON["email"]}?subject={quote("[의뢰] ")}&body={quote(body)}'


# ---------- JSON-LD (schema.org) ----------
def ref(i):
    return {'@id': P_URL + '#' + i}


def node(x, **extra):
    n = {'@type': x['type'], '@id': P_URL + '#' + x['id']}
    n.update({k: v for k, v in extra.items() if v not in (None, '', [], {})})
    return n


def person_role(role_name):
    return {'@type': 'Role', 'roleName': role_name, 'contributor': ref(PERSON['id'])}


def ld_work(w):
    stat = {'@type': 'InteractionCounter', 'interactionType': 'https://schema.org/WatchAction', 'userInteractionCount': w['views']} if w.get('views') else None
    return node(w, name=w['title'], url=yt_url(w), embedUrl=f'https://www.youtube-nocookie.com/embed/{w["youtube"]}',
                thumbnailUrl=f'https://i.ytimg.com/vi/{w["youtube"]}/hqdefault.jpg', dateCreated=w['year'],
                duration=iso_duration(w.get('duration')), description=w.get('summary'), inLanguage='ko',
                genre=w.get('categories'), interactionStatistic=stat, contributor=person_role(w['credit']),
                sourceOrganization=ref(w['client']) if w.get('client') else None,
                recordedAt=ref(w['event']) if w.get('event') else None,
                isPartOf=ref(w['partOf']) if w.get('partOf') else None)


def ld_series(s):
    parts = [ref(p['work']) if 'work' in p else {'@type': 'CreativeWork', 'name': p['name'], 'url': p['url']} for p in s['parts']]
    return node(s, name=s['title'], dateCreated=s['year'], description=s['cvDescription'], hasPart=parts,
                contributor=person_role(s['credit']), sourceOrganization=ref(s['client']), about=ref(s['event']))


def ld_core(job_title):
    p = PERSON
    roles = [{'@type': 'OrganizationRole', 'roleName': r['roleName'], 'startDate': r['start'], 'endDate': r.get('end'),
              'memberOf': ref(r['org'])} for r in by_period(D['positions']) if r.get('org')]
    for r in roles:
        if r['endDate'] is None:
            del r['endDate']
    edu = ENT[p['alumniOf']]
    nodes = [
        node(p, name=p['name'], jobTitle=job_title, email='mailto:' + p['email'], telephone=p['telephone'],
             url=P_URL, sameAs=[p['instagram']['url'], C_URL], alumniOf=ref(edu['org']), memberOf=roles,
             knowsAbout=[ref(s['id']) for s in D['skills']] + [ref(x['id']) for x in D['tools']],
             subjectOf=ref(p['showreel']['id'])),
        node(p['showreel'], name=p['showreel']['name'], contentUrl=p['showreel']['url'], thumbnailUrl=p['showreel']['thumbnail'],
             duration=iso_duration(p['showreel']['duration']), creator=ref(p['id'])),
    ]
    for o in D['organizations']:
        nodes.append(node(o, name=o['name'], alternateName=o.get('short'), description=o.get('description'), url=o.get('url'),
                          parentOrganization=ref(o['parent']) if o.get('parent') else None,
                          founder=ref(o['founder']) if o.get('founder') else None))
    for e in D['events']:
        nodes.append(node(e, name=e['name'], startDate=e.get('startDate'), description=e.get('description'),
                          organizer=ref(e['organizer']) if e.get('organizer') else None,
                          superEvent=ref(e['superEvent']) if e.get('superEvent') else None))
    for s in D['skills']:
        nodes.append(node(s, name=s['name'], hasDefinedTerm=[{'@type': 'DefinedTerm', 'name': i} for i in s['items']]))
    for x in D['tools']:
        nodes.append(node(x, name=x['name']))
    return nodes


def ld_graph(key):
    pg = PAGES[key]
    site = SITES[pg['site']]
    url = site['url'] + pg['path']
    job = pg.get('role', PERSON['roleKo'])
    g = ld_core(job)
    g.append({'@type': 'WebSite', '@id': site['url'] + '#website', 'name': site['name'], 'url': site['url'],
              'inLanguage': 'ko', 'author': ref(PERSON['id'])})
    page = {'@type': 'WebPage', '@id': url + '#webpage', 'url': url, 'name': pg['title'], 'description': pg['description'],
            'inLanguage': 'ko', 'isPartOf': {'@id': site['url'] + '#website'}, 'about': ref(PERSON['id']), 'dateModified': UPDATED}
    if pg['site'] == 'cv':
        page['@type'] = 'ProfilePage'
        page['mainEntity'] = ref(PERSON['id'])
        ids = pg['works']
        g += [ld_series(ENT[i]) if ENT[i]['type'] == 'CreativeWorkSeries' else ld_work(ENT[i]) for i in ids]
        g += [ld_work(ENT[p['work']]) for i in ids if ENT[i]['type'] == 'CreativeWorkSeries' for p in ENT[i]['parts'] if 'work' in p]
        g += [node(f, name=f['title'], productionCompany=ref(f['org']), contributor=person_role(' · '.join(f['roles']))) for f in D['films']]
    elif key == 'portfolio:index':
        g += [ld_work(w) for w in D['works']] + [ld_series(s) for s in D['series']]
        page['mainEntity'] = {'@type': 'ItemList', 'name': '대표작',
                              'itemListElement': [{'@type': 'ListItem', 'position': w['featured'], 'item': ref(w['id'])} for w in featured()]}
    else:
        g += [node(s, name=s['name'], description=s['description'], provider=ref('studio'), areaServed='KR') for s in BIZ['services']]
        if key == 'portfolio:request':
            page['@type'] = ['WebPage', 'FAQPage']
            page['mainEntity'] = [{'@type': 'Question', 'name': f['q'], 'acceptedAnswer': {'@type': 'Answer', 'text': f['a']}} for f in BIZ['faq']]
    g.append(page)
    return {'@context': 'https://schema.org', '@graph': g}


def jsonld(key):
    s = json.dumps(ld_graph(key), ensure_ascii=False, sort_keys=True, indent=1)
    return '<script type="application/ld+json">\n' + s.replace('</', '<\\/') + '\n</script>'


def head(key):
    pg = PAGES[key]
    site = SITES[pg['site']]
    url = site['url'] + pg['path']
    return '\n'.join([
        f'<title>{t(pg["title"])}</title>',
        f'<meta name="description" content="{a(pg["description"])}">',
        f'<link rel="canonical" href="{a(url)}">',
        '<meta property="og:type" content="' + ('profile' if pg['site'] == 'cv' else 'website') + '">',
        f'<meta property="og:site_name" content="{a(site["name"])}">',
        '<meta property="og:locale" content="ko_KR">',
        f'<meta property="og:title" content="{a(pg["title"])}">',
        f'<meta property="og:description" content="{a(pg["description"])}">',
        f'<meta property="og:url" content="{a(url)}">',
        f'<meta property="og:image" content="{a(site["image"])}">',
        '<meta name="twitter:card" content="summary_large_image">',
        jsonld(key),
    ])


# ---------- 포트폴리오 ----------
def featured():
    return sorted([w for w in D['works'] if w.get('featured')], key=lambda w: w['featured'])


def thumb(w):
    yid = w['youtube']
    dur = f'<span class="dur">{t(w["duration"])}</span>' if w.get('duration') else ''
    return (f'<div class="thumb"><img src="https://i.ytimg.com/vi/{yid}/maxresdefault.jpg" '
            f'data-fallback="https://i.ytimg.com/vi/{yid}/hqdefault.jpg" alt="" width="1280" height="720" loading="lazy"><span class="play" aria-hidden="true">{icon("play")}</span>{dur}</div>')


def work_link(w):
    return f'<a class="card-link" href="{a(yt_url(w))}" data-work="{a(w["id"])}">{t(w["title"])}</a>'


def p_featured():
    out = ['<ol class="feat-list">']
    for w in featured():
        views = f' · 조회수 {num(w["views"])}' if w.get('views') else ''
        out.append(
            f'  <li class="card feat">\n'
            f'    {thumb(w)}\n'
            f'    <div class="feat-body">\n'
            f'      <h3>{work_link(w)}</h3>\n'
            f'      <p class="meta">{t(client_label(w))} · {w["year"]}{views}</p>\n'
            f'      <p class="credit">{t(w["credit"])}</p>\n'
            f'      <p class="desc">{t(w["summary"])}</p>\n'
            f'    </div>\n'
            f'  </li>')
    out.append('</ol>')
    return '\n'.join(out)


def p_works():
    works = by_year(D['works'])
    cats = [c for c in D['categories'] if any(c in w['categories'] for w in works)]
    chips = [('전체', len(works))] + [(c, sum(c in w['categories'] for w in works)) for c in cats]
    out = ['<ul class="filters" id="filters" aria-label="역할별로 보기">']
    out += [f'  <li><button class="chip-btn" type="button" data-cat="{a(c)}" aria-pressed="{"true" if i == 0 else "false"}">'
            f'{t(c)}<span class="n">{n}<span class="sr-only">편</span></span></button></li>' for i, (c, n) in enumerate(chips)]
    out += ['</ul>', '<p class="sr-only" id="filter-status" role="status" aria-live="polite"></p>', '<div class="grid" id="grid">']
    for w in works:
        lead = f'<span class="lead-role">{t(w["lead"])}</span>' if w.get('lead') else ''
        out.append(
            f'  <article class="card" data-cats="{a(" ".join(w["categories"]))}">\n'
            f'    {thumb(w)}\n'
            f'    <h3>{work_link(w)}</h3>\n'
            f'    <p class="meta"><span>{t(client_label(w))} · {w["year"]}</span>{lead}</p>\n'
            f'    <p class="roles"><span class="sr-only">역할: </span>{t(" · ".join(w["categories"]))}</p>\n'
            f'  </article>')
    out.append('</div>')
    data = {w['id']: {'t': w['title'], 'c': client_label(w), 'y': w['year'], 'yt': w['youtube'], 'v': w.get('views', 0),
                      'cr': w['credit'], 'x': w['summary']} for w in works}
    js = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(',', ':')).replace('</', '<\\/')
    out.append(f'<script type="application/json" id="works-data">{js}</script>')
    return '\n'.join(out)


def p_reel():
    r = PERSON['showreel']
    return (f'<div class="reel" id="reel">\n'
            f'  <video id="reel-video" src="{a(rel(r["url"]))}" poster="{a(rel(r["thumbnail"]))}" preload="none" playsinline '
            f'aria-label="{a(r["name"])}, {r["duration"]}"></video>\n'
            f'  <button class="reel-play" type="button" data-play-reel><span class="disc" aria-hidden="true">{icon("play")}</span>'
            f'<span class="reel-cap">쇼릴 재생 <span class="dur">{r["duration"]}</span></span></button>\n'
            f'</div>')


def p_stats():
    lc = PERSON['lightingCredits']
    recap_years = {w['year'] for w in D['works'] if w['id'].endswith('-recap') and ENT.get(w.get('event'), {}).get('superEvent') == 'furraid'}
    values = {
        'views_total': num(sum(w.get('views', 0) for w in D['works'])),
        'lighting_total': lc['director'] + lc['crew'], 'lighting_director': lc['director'], 'lighting_crew': lc['crew'],
        'furraid_years': len(recap_years),
        'sameday_count': sum(len(w['sameDay']['items']) for w in D['works'] if w.get('sameDay')),
    }
    out = []
    for s in PAGES['portfolio:index']['stats']:
        v, lbl = Template(s['value']).substitute(values), Template(s['label']).substitute(values)
        if s.get('jumpCat'):
            out.append(f'<a class="stat stat-link" href="#work" data-jump-cat="{a(s["jumpCat"])}"><b>{t(v)}</b>'
                       f'<span>{t(lbl)} {icon("arrow-right")}</span></a>')
        else:
            out.append(f'<div class="stat"><b>{t(v)}</b><span>{t(lbl)}</span></div>')
    return '\n'.join(out)


def p_partners():
    out = ['<ul class="partner-list">']
    for x in PAGES['portfolio:index']['partners']:
        name = org_label(x['org']) if x.get('org') else x['label']
        out.append(f'  <li><strong>{t(name)}</strong><span>{t(x["note"])}</span></li>')
    return '\n'.join(out + ['</ul>'])


def timeline_items():
    return by_period([r for r in D['positions'] if r.get('short')] + D['education'])


def p_profile():
    p = PERSON
    out = [f'<h3 id="profile-name">{t(p["name"])}</h3>', f'<p class="role">{t(p["roleKo"])}</p>', f'<p class="bio">{t(p["bio"])}</p>',
           '<ol class="timeline">']
    out += [f'  <li><span class="when">{span(x["start"], x.get("end"))}</span><span>{t(x["short"])}</span></li>' for x in timeline_items()]
    out += ['</ol>', f'<p class="btns"><a class="btn btn-ghost" href="{a(C_URL)}"{NEW}>이력서 보기 {icon("arrow-up-right")}<span class="sr-only">(새 창)</span></a></p>']
    return '\n'.join(out)


def contact_rows():
    p = PERSON
    return [
        ('mail', '이메일', p['email'], mailto_template(), ''),
        ('phone', '전화', p['telephone'], 'tel:' + p['telephone'], ''),
        ('instagram', '인스타그램', p['instagram']['handle'], p['instagram']['url'], NEW),
    ]


def p_contact():
    out = ['<ul class="cta-links">',
           f'  <li><a href="request.html"><span class="k">{icon("clipboard")}의뢰 안내</span><span class="v">보내주실 것 · 진행 순서 {icon("arrow-right")}</span></a></li>']
    for ic, k, v, href, tgt in contact_rows():
        tail = f' {icon("arrow-up-right")}<span class="sr-only">(새 창)</span>' if tgt else ''
        out.append(f'  <li><a href="{a(href)}"{tgt}><span class="k">{icon(ic)}{t(k)}</span><span class="v">{t(v)}{tail}</span></a></li>')
    return '\n'.join(out + ['</ul>'])


def p_footer(home):
    links = [('이력서', C_URL, NEW), ('YouTube', ENT['productiongal']['url'], NEW), ('Instagram', PERSON['instagram']['url'], NEW), ('서비스 소개서', 'guide.html', NEW)]
    lis = ''.join(f'<li><a href="{a(u)}"{tg}>{t(n)}<span class="sr-only">(새 창)</span></a></li>' for n, u, tg in links)
    return (f'<footer class="site-footer">\n  <div class="wrap">\n'
            f'    <a class="logo" href="{home}"><span class="logo-mark" aria-hidden="true"></span><span><b>주황색</b> 영상공방</span></a>\n'
            f'    <ul class="foot-links">{lis}</ul>\n'
            f'    <p>© {UPDATED[:4]} {t(PERSON["name"])}</p>\n  </div>\n</footer>')


def r_quick():
    return '<ul class="quick">' + ''.join(f'<li>{icon(q["icon"])}{t(q["text"])}</li>' for q in BIZ['quick']) + '</ul>'


def r_brief():
    p = PERSON
    out = [f'<form class="brief-form" id="brief-form" action="mailto:{a(p["email"])}" method="post" enctype="text/plain" data-to="{a(p["email"])}">']
    for b in BIZ['brief']:
        k, fid = b['key'], f'f-{b["key"]}'
        badge = '<span class="req">필수</span>' if b['required'] else '<span class="opt">선택</span>'
        hint = f'<p class="hint" id="{fid}-hint">{t(b["hint"])}</p>'
        if b.get('options') == 'services':
            checks = ''.join(f'<label class="check"><input type="checkbox" name="{k}" value="{a(s["name"])}"><span>{t(s["name"])}</span></label>'
                             for s in BIZ['services'])
            out.append(f'  <fieldset class="field" data-field="{k}" data-label="{a(b["label"])}" aria-describedby="{fid}-hint">'
                       f'<legend>{icon(b["icon"])}{t(b["label"])} {badge}</legend><div class="checks">{checks}</div>{hint}</fieldset>')
            continue
        req = ' required' if b['required'] else ''
        if b.get('input') == 'textarea':
            ctl = f'<textarea id="{fid}" name="{k}" rows="3" aria-describedby="{fid}-hint"{req}></textarea>'
        else:
            mode = ' inputmode="url" autocomplete="url"' if b.get('input') == 'url' else ''
            ctl = f'<input id="{fid}" name="{k}" type="text"{mode} aria-describedby="{fid}-hint"{req}>'
        out.append(f'  <div class="field" data-field="{k}" data-label="{a(b["label"])}"><label for="{fid}">{icon(b["icon"])}{t(b["label"])} {badge}</label>{ctl}{hint}</div>')
    out += [
        f'  <div class="form-foot"><button class="btn btn-solid" type="submit">{icon("mail")}메일 앱에서 보내기</button>',
        f'  <p class="form-note">메일 앱이 열리지 않으면 <a href="mailto:{a(p["email"])}">{t(p["email"])}</a>로 같은 내용을 보내 주세요.</p>',
        '  <p class="form-done" id="brief-done" role="status" hidden>메일 앱에서 내용을 확인하고 보내기를 눌러 주세요.</p></div>',
        '</form>']
    return '\n'.join(out)


def r_flow():
    out = ['<ol class="flow">']
    for i, s in enumerate(BIZ['process'], 1):
        out.append(f'  <li><span class="no">{i:02d}</span>{icon(s["icon"])}<h3>{t(s["name"])}</h3><p>{t(s["body"])}</p></li>')
    return '\n'.join(out + ['</ol>'])


def r_services():
    out = ['<div class="svc-grid">']
    for s in BIZ['services']:
        lis = ''.join(f'<li>{icon("check")}{t(i)}</li>' for i in s['items'])
        out.append(f'  <article class="svc">{icon(s["icon"])}<h3>{t(s["name"])}</h3><p>{t(s["description"])}</p><ul>{lis}</ul></article>')
    return '\n'.join(out + ['</div>'])


def r_gear():
    g = D['gear']
    out = [f'<p class="lead">{t(g["note"])}</p>', '<ul class="gear">']
    out += [f'  <li>{icon(x["icon"])}<span class="k">{t(x["kind"])}</span><h3>{t(ENT[x["tool"]]["name"])}</h3><p>{t(x["note"])}</p></li>' for x in g['items']]
    return '\n'.join(out + ['</ul>'])


def r_faq():
    out = ['<div class="faq">']
    out += [f'  <details><summary>{t(f["q"])}{icon("chevron-down")}</summary><p>{t(f["a"])}</p></details>' for f in BIZ['faq']]
    return '\n'.join(out + ['</div>'])


def r_contact():
    hints = {'mail': '날짜 · 장소 · 작업을 적을 칸이 채워진 채로 열립니다', 'phone': '모바일에서 누르면 바로 연결됩니다', 'instagram': '작업 근황과 DM 문의'}
    out = [f'<p class="lead">{t(BIZ["bookingNote"])}</p>', '<ul class="contact-cards">']
    for ic, k, v, href, tgt in contact_rows():
        sr = '<span class="sr-only">(새 창)</span>' if tgt else ''
        out.append(f'  <li><a href="{a(href)}"{tgt}>{icon(ic)}<span class="k">{t(k)}</span><b>{t(v)}</b><span>{t(hints[ic])}</span>{sr}</a></li>')
    out += ['</ul>', f'<p class="note">작업물이 궁금하시면 <a href="index.html#featured">대표작</a>과 <a href="{a(C_URL)}"{NEW}>이력서<span class="sr-only">(새 창)</span></a>를 함께 봐 주세요.</p>']
    return '\n'.join(out)


# ---------- 이력서 ----------
def cv_toolbar():
    r = PERSON['showreel']
    return (f'<nav class="toolbar" aria-label="바로가기">\n'
            f'  <a href="{a(r["url"])}"{NEW}>쇼릴 보기 {EXT}</a>\n'
            f'  <a href="{a(P_URL)}"{NEW}>포트폴리오 보기 {EXT}</a>\n'
            f'  <button type="button" onclick="window.print()">PDF로 저장 / 인쇄</button>\n'
            f'</nav>')


def sec(sid, title, body, cls=''):
    c = f' class="{cls}"' if cls else ''
    return f'<section{c} aria-labelledby="sec-{sid}">\n  <h2 class="sec" id="sec-{sid}">{title}</h2>\n{body}\n</section>'


def entry(when, title, org, body):
    p = f'<p>{t(body)}</p>' if body else ''
    return f'  <div class="entry"><div class="when">{when}</div><div class="what"><h3>{t(title)}</h3><span class="org">{t(org)}</span>{p}</div></div>'


def cv_top(key):
    pg, p = PAGES[key], PERSON
    head = (f'<header class="head">\n'
            f'  <div>\n    <h1>{t(p["name"])}</h1>\n    <p class="role">{t(pg["role"])}</p>\n'
            f'    <p class="note">{t(p["affiliationNote"])} · {ym(p["availableFrom"])}부터 근무 가능</p>\n  </div>\n'
            f'  <address class="contact">\n'
            f'    <a href="tel:{a(p["telephone"])}">{t(p["telephone"])}</a>\n'
            f'    <a href="mailto:{a(p["email"])}">{t(p["email"])}</a>\n'
            f'    <span class="links"><a href="{a(P_URL)}"{NEW}>포트폴리오 {EXT}</a> <a href="{a(p["showreel"]["url"])}"{NEW}>쇼릴 {EXT}</a></span>\n'
            f'  </address>\n</header>')
    edu = '\n'.join(entry(span(e['start'], e['end']), ENT[e['org']]['name'],
                          ' · '.join([e['status']] + [f'{ym(m["date"])} {m["label"]}' for m in e['milestones']]),
                          f'학점 {e["gpa"]}') for e in D['education'])

    def roles(section):
        return '\n'.join(entry(span(r['start'], r.get('end')), r['roleName'], r.get('orgLine') or ENT[r['org']]['name'], r['body'])
                         for r in by_period([r for r in D['positions'] if r['section'] == section]))
    return '\n\n'.join([head, sec('summary', '소개', f'  <p>{t(pg["summary"])}</p>', 'summary'), sec('edu', '학력', edu),
                        sec('exp', '경력', roles('experience')), sec('proj', '프로젝트', roles('project'))])


def cv_work(x):
    links = ''
    if x['type'] == 'CreativeWorkSeries':
        parts = [dict(ENT[pp['work']], name=ENT[pp['work']]['partTitle'], url=yt_url(ENT[pp['work']])) if 'work' in pp else pp for pp in x['parts']]
        links = f' {x["partsLabel"]}: ' + ' · '.join(f'<a href="{a(pp["url"])}"{NEW}>{t(pp["name"])}</a>' for pp in parts)
        top = max((pp for pp in parts if pp.get('views')), key=lambda pp: pp['views'])
        meta = f'{x["year"]} · 공개 {len(parts)}편 · 최다 조회 {num(top["views"])} · <a href="{a(top["url"])}"{NEW}>보기 {EXT}</a>'
        title = x['title']
    elif x.get('sameDay'):
        sd = x['sameDay']
        links = f' {sd["label"]}: ' + ' · '.join(f'<a href="{a(i["url"])}"{NEW} class="nowrap">{t(i["name"])} {num(i["views"])}</a>' for i in sd['items'])
        meta = f'{x["year"]} · {sd["platform"]} 당일 리캡 합산 {num(sum(i["views"] for i in sd["items"]))}회 · <a href="{a(yt_url(x))}"{NEW}>본편 보기 {EXT}</a>'
        title = f'{x["title"]} / 현장 당일 리캡 {len(sd["items"])}편'
    else:
        views = f' · 조회수 {num(x["views"])}' if x.get('views') else ''
        meta = f'{x["year"]}{views} · <a href="{a(yt_url(x))}"{NEW}>보기 {EXT}</a>'
        title = x['title']
    stats = f'\n    <p class="stats">{t(x["cvStats"])}</p>' if x.get('cvStats') else ''
    return (f'  <article class="work">\n'
            f'    <div><span class="tag">{t(x["cvTag"])}</span><h3>{t(title)}</h3><div class="info">{t(client_label(x))} · {t(x["credit"])}</div>\n'
            f'    <p class="desc">{t(x["cvDescription"])}{links}</p>{stats}</div>\n'
            f'    <div class="meta">{meta}</div>\n'
            f'  </article>')


def cv_bottom(key):
    pg = PAGES[key]
    works = '  <div class="worklist">\n' + '\n'.join(cv_work(ENT[i]) for i in [w['id'] for w in by_year([ENT[i] for i in pg['works']])]) + '\n  </div>'
    films = '  <div class="worklist">\n' + '\n'.join(
        f'  <div class="work"><div><h3>{t(f["title"])}</h3><div class="info">{t(ENT[f["org"]]["name"])} {t(f["kind"])} · {t(" · ".join(f["roles"]))}</div></div></div>'
        for f in D['films']) + '\n  </div>'
    skills = '\n'.join(f'  <div class="skillgroup">\n    <h3>{t(ENT[s]["name"])}</h3>\n    <ul>' + ''.join(f'\n      <li>{t(i)}</li>' for i in ENT[s]['items']) + '\n    </ul>\n  </div>'
                       for s in pg['skills'])
    clients = '  <p class="tags">' + ''.join(f'<span>{t(org_label(o))}</span>' for o in D['cvClients']) + '</p>'
    foot = f'<footer class="foot">\n  <span>{t(PERSON["name"])}</span>\n  <span>{ym(UPDATED[:7])} 갱신</span>\n</footer>'
    return '\n\n'.join([sec('works', '주요 작업', works), sec('films', '영화 현장', films, 'films'), sec('skills', '기술', skills),
                        sec('clients', '클라이언트', clients), foot])


# ---------- 사이트 루트 파일 ----------
def sitemap(site):
    urls = [SITES[site]['url'] + pg['path'] for k, pg in sorted(PAGES.items()) if pg['site'] == site]
    body = ''.join(f'  <url><loc>{u}</loc><lastmod>{UPDATED}</lastmod></url>\n' for u in sorted(urls))
    return f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{body}</urlset>\n'


def robots(site):
    return f'User-agent: *\nAllow: /\n\nSitemap: {SITES[site]["url"]}sitemap.xml\n'


def llms_facts():
    p = PERSON
    edu = D['education'][0]
    return [
        f'- 이름: {p["name"]} · 역할: {p["roleKo"]}',
        f'- 연락: {p["email"]} · {p["telephone"]} · 인스타그램 {p["instagram"]["handle"]} ({p["instagram"]["url"]})',
        f'- 학력: {ENT[edu["org"]]["name"]} {span(edu["start"], edu["end"])} ({edu["status"]}, ' + ', '.join(f'{ym(m["date"])} {m["label"]}' for m in edu['milestones']) + ')',
        f'- 근무 가능: {ym(p["availableFrom"])}부터',
        f'- 조명 참여: 조명감독 {p["lightingCredits"]["director"]}편 · 조명부 {p["lightingCredits"]["crew"]}편',
        f'- 쇼릴: {p["showreel"]["url"]} ({p["showreel"]["duration"]})',
        f'- 구조화 데이터 원본: {P_URL}data/cv.json (schema.org 타입과 고정 id로 정리, 이 파일과 각 페이지 JSON-LD는 여기서 생성)',
        f'- 기준일: {UPDATED}',
    ]


def llms_work(w):
    views = f' · 조회수 {num(w["views"])}' if w.get('views') else ''
    return f'- [{w["title"]}]({yt_url(w)}): {w["year"]} · {client_label(w)} · {w["credit"]}{views}. {w["summary"]}'


def llms_portfolio():
    out = [f'# {SITES["portfolio"]["name"]} ({PERSON["name"]})', '', f'> {SITES["portfolio"]["summary"]}', '']
    out += llms_facts() + ['', '## 페이지', '']
    out += [f'- [{PAGES[k]["title"]}]({P_URL}{PAGES[k]["path"]}): {PAGES[k]["description"]}' for k in ('portfolio:index', 'portfolio:request', 'portfolio:guide')]
    out += [f'- [{PAGES["cv:index"]["title"]}]({C_URL}): {PAGES["cv:index"]["description"]}', '', '## 대표작', '']
    out += [llms_work(w) for w in featured()]
    out += ['', '## 의뢰', '']
    out += [f'- {s["name"]}: {s["description"]} ' + ' / '.join(s['items']) for s in BIZ['services']]
    out += [f'- 진행 순서: ' + ' → '.join(s['name'] for s in BIZ['process'])]
    out += [f'- {f["q"]} {f["a"]}' for f in BIZ['faq']]
    out += ['', '## Optional', '']
    out += [llms_work(w) for w in by_year(D['works']) if not w.get('featured')]
    return '\n'.join(out) + '\n'


def llms_cv():
    out = [f'# {SITES["cv"]["name"]}', '', f'> {SITES["cv"]["summary"]}', '']
    out += llms_facts() + ['', '## 페이지', '']
    out += [f'- [{PAGES[k]["title"]}]({C_URL}{PAGES[k]["path"]}): {PAGES[k]["description"]} 역할 표기: {PAGES[k]["role"]}' for k in ('cv:index', 'cv:di', 'cv:inhouse')]
    out += [f'- [포트폴리오]({P_URL}): {SITES["portfolio"]["summary"]}', '', '## 경력 · 프로젝트', '']
    out += [f'- {span(r["start"], r.get("end"))} · {r["roleName"]} · {r.get("orgLine") or ENT[r["org"]]["name"]}. {r["body"]}' for r in by_period(D['positions'])]
    out += ['', '## 주요 작업', '']
    out += [llms_work(w) for w in by_year(D['works'])]
    out += ['', '## 기술', '']
    out += [f'- {s["name"]}: ' + ' / '.join(s['items']) for s in D['skills']]
    out += ['', '## Optional', '']
    out += [f'- 영화 현장: ' + ' / '.join(f'{f["title"]} ({ENT[f["org"]]["name"]} {f["kind"]} · {" · ".join(f["roles"])})' for f in D['films'])]
    return '\n'.join(out) + '\n'


# ---------- 조립 ----------
def put(text, name, content, path):
    pat = re.compile(r'(<!-- build:%s -->\n).*?(<!-- /build:%s -->)' % (re.escape(name), re.escape(name)), re.S)
    if len(pat.findall(text)) != 1:
        sys.exit(f'{path}: <!-- build:{name} --> 영역이 정확히 한 개 있어야 합니다')
    return pat.sub(lambda m: m.group(1) + content + '\n' + m.group(2), text)


def fill(path, regions):
    text = path.read_text('utf-8')
    for name, content in regions.items():
        text = put(text, name, content, path)
    return text


def outputs():
    if not CV_ROOT.is_dir():
        sys.exit(f'이력서 저장소를 찾을 수 없습니다: {CV_ROOT}')
    out = {}
    out[ROOT / 'index.html'] = fill(ROOT / 'index.html', {
        'head': head('portfolio:index'), 'reel': p_reel(), 'stats': p_stats(), 'featured': p_featured(), 'partners': p_partners(),
        'works': p_works(), 'profile': p_profile(), 'contact': p_contact(), 'footer': p_footer('#top')})
    out[ROOT / 'request.html'] = fill(ROOT / 'request.html', {
        'head': head('portfolio:request'), 'quick': r_quick(), 'brief': r_brief(), 'flow': r_flow(), 'services': r_services(),
        'gear': r_gear(), 'faq': r_faq(), 'contact': r_contact(), 'footer': p_footer('index.html')})
    out[ROOT / 'guide.html'] = fill(ROOT / 'guide.html', {'head': head('portfolio:guide')})
    style = re.search(r'^<style>\n.*?^</style>', (CV_ROOT / 'index.html').read_text('utf-8'), re.S | re.M).group(0)
    for key in ('cv:index', 'cv:di', 'cv:inhouse'):
        path = CV_ROOT / PAGES[key]['file']
        regions = {'head': head(key), 'cv-toolbar': cv_toolbar(), 'cv-top': cv_top(key), 'cv-bottom': cv_bottom(key)}
        if key != 'cv:index':
            regions['style'] = style
        out[path] = fill(path, regions)
    for site, root, llms in (('portfolio', ROOT, llms_portfolio()), ('cv', CV_ROOT, llms_cv())):
        out[root / 'sitemap.xml'] = sitemap(site)
        out[root / 'robots.txt'] = robots(site)
        out[root / 'llms.txt'] = llms
    return out


def main():
    check = '--check' in sys.argv[1:]
    stale = []
    for path, text in outputs().items():
        old = path.read_text('utf-8') if path.exists() else None
        if old != text:
            stale.append(path)
            if not check:
                path.write_text(text, 'utf-8')
    if check:
        for p in stale:
            print(f'오래됨: {p}')
        print('최신 상태입니다' if not stale else f'{len(stale)}개 파일이 data/cv.json과 다릅니다. python3 build.py를 실행하세요.')
        sys.exit(1 if stale else 0)
    print(f'{len(stale)}개 파일을 새로 썼습니다' if stale else '바뀐 파일이 없습니다')


if __name__ == '__main__':
    main()
