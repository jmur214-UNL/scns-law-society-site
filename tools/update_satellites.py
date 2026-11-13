"""Refreshes the satellite and debris data the globe draws (src/data/sats.json and src/data/debris.b64).

The positions on the globe are worked out live in the browser from orbital elements, but those elements age: after a few
weeks the dots drift away from where the real objects are. Run this now and then, then rebuild:

    python3 tools/update_satellites.py --catalog path/to/catalog.tle
    python3 tools/build.py

Satellites: the "space stations" and "brightest" groups and the satellite catalog, downloaded from CelesTrak.
Debris: needs a full-catalog TLE file (every tracked object, debris and rocket bodies included), passed with --catalog.
Space-Track.org (free account) offers one. Without --catalog the debris layer is left as it is.
Use --from DIR to read stations.tle, visual.tle and satcat.csv from a folder instead of downloading them.
"""
import argparse, base64, csv, datetime, io, json, math, os, re, struct, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, 'src', 'data')
CELESTRAK = {
    'stations.tle': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=stations&FORMAT=tle',
    'visual.tle': 'https://celestrak.org/NORAD/elements/gp.php?GROUP=visual&FORMAT=tle',
    'satcat.csv': 'https://celestrak.org/pub/satcat.csv',
}
MU = 398600.4418
RE = 6378.137
# Debris times are counted in days from this date; the page uses the same reference.
EPOCH0 = datetime.datetime(2026, 1, 1, tzinfo=datetime.timezone.utc)
# International designators of the four big breakup clouds drawn in red: Fengyun-1C, Iridium 33, Cosmos 2251, Cosmos 1408.
CLOUDS = ('1999-025', '1993-036', '1997-051', '1982-092')


def fetch(name, src_dir):
    if src_dir:
        with open(os.path.join(src_dir, name), encoding='utf-8', errors='replace') as f:
            return f.read()
    req = urllib.request.Request(CELESTRAK[name], headers={'User-Agent': 'scns-law-society-site data refresh'})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode('utf-8', errors='replace')


def triples(tle_text):
    lines = [l.rstrip('\n') for l in tle_text.splitlines() if l.strip()]
    for k in range(0, len(lines) - 2, 3):
        name, l1, l2 = lines[k].strip(), lines[k + 1], lines[k + 2]
        if l1.startswith('1 ') and l2.startswith('2 '):
            yield name, l1, l2


def elements(l1, l2):
    yy, doy = int(l1[18:20]), float(l1[20:32])
    year = 2000 + yy if yy < 57 else 1900 + yy
    ep = datetime.datetime(year, 1, 1, tzinfo=datetime.timezone.utc) + datetime.timedelta(days=doy - 1)
    inc, raan = float(l2[8:16]), float(l2[17:25])
    ecc = float('0.' + l2[26:33].strip())
    argp, M, n = float(l2[34:42]), float(l2[43:51]), float(l2[52:63])
    a = (MU / (n * 2 * math.pi / 86400) ** 2) ** (1 / 3)
    return ep, inc, raan, ecc, argp, M, n, a


def satellites(src_dir, cat):
    sats, seen = [], set()
    for group in ('stations.tle', 'visual.tle'):
        for name, l1, l2 in triples(fetch(group, src_dir)):
            norad = l1[2:7].strip()
            if norad in seen:
                continue
            ep, inc, raan, ecc, argp, M, n, a = elements(l1, l2)
            # Low orbits only, and nothing in a steep decay.
            if a * (1 + ecc) - RE > 3000 or abs(float(l1[33:43])) > 0.002:
                continue
            seen.add(norad)
            c = cat.get(str(int(norad)), {})
            if c.get('ORBIT_TYPE') == 'DOC':
                continue
            sats.append([round(ep.timestamp() * 1000), round(inc, 4), round(raan, 4), round(ecc, 7), round(argp, 4),
                         round(M, 4), round(n, 8), 1 if norad == '25544' else 0, re.sub(r'\s+', ' ', name).strip(),
                         int(norad), c.get('OBJECT_TYPE', ''), c.get('OWNER', ''), (c.get('LAUNCH_DATE') or '')[:4]])
    return sats


def debris(catalog_path, cat):
    with open(catalog_path, encoding='utf-8', errors='replace') as f:
        text = f.read()
    vals, n, seen = [], 0, set()
    for _, l1, l2 in triples(text):
        norad = str(int(l1[2:7]))
        if norad in seen:
            continue
        c = cat.get(norad, {})
        if c.get('OBJECT_TYPE') not in ('DEB', 'R/B') or c.get('DECAY_DATE'):
            continue
        seen.add(norad)
        ep, inc, raan, ecc, argp, M, mm, a = elements(l1, l2)
        if a * (1 + ecc) - RE > 3000:
            continue
        grp = 1 if (c.get('OBJECT_ID') or '').startswith(CLOUDS) else 0
        vals += [(ep - EPOCH0).total_seconds() / 86400, inc, raan, ecc, argp, M, mm, grp]
        n += 1
    return base64.b64encode(struct.pack('<%df' % len(vals), *vals)).decode(), n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--catalog', help='full-catalog TLE file, for the debris layer')
    ap.add_argument('--from', dest='src_dir', help='read stations.tle, visual.tle and satcat.csv from this folder')
    args = ap.parse_args()
    cat = {r['NORAD_CAT_ID']: r for r in csv.DictReader(io.StringIO(fetch('satcat.csv', args.src_dir)))}
    sats = satellites(args.src_dir, cat)
    if not any(s[7] for s in sats):
        raise SystemExit('The ISS is missing from the download; leaving the data as it is.')
    with open(os.path.join(DATA, 'sats.json'), 'w', encoding='utf-8') as f:
        json.dump(sats, f, separators=(',', ':'))
    print(len(sats), 'satellites written')
    if args.catalog:
        b, n = debris(args.catalog, cat)
        with open(os.path.join(DATA, 'debris.b64'), 'w') as f:
            f.write(b)
        print(n, 'pieces of debris and rocket stages written')
    else:
        print('Debris left as it is (no --catalog given).')


if __name__ == '__main__':
    main()
