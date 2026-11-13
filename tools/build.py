"""Builds index.html, the page the site serves.

src/site.html is the page as written, with a few placeholders (__LIKE_THIS__) where data and images are embedded. This
script fills them in from src/data and src/brand, then wraps the page in a complete HTML document.

    python3 tools/build.py
"""
import base64, datetime, json, os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC, DATA, BRAND = (os.path.join(ROOT, 'src', d) for d in ('', 'data', 'brand'))


def text(*parts):
    with open(os.path.join(*parts), encoding='utf-8') as f:
        return f.read()


def b64(*parts):
    with open(os.path.join(*parts), 'rb') as f:
        return base64.b64encode(f.read()).decode()


page = text(SRC, 'site.html')
sats_raw = text(DATA, 'sats.json')
debris = text(DATA, 'debris.b64').strip()
latest = max(s[0] for s in json.loads(sats_raw)) / 1000
tle_date = datetime.datetime.fromtimestamp(latest, datetime.timezone.utc).strftime('%B %d, %Y').replace(' 0', ' ')

fills = {
    '__LAND_MASK__': b64(DATA, 'land_mask.png'),
    '__US_DATA__': text(DATA, 'us.json'),
    '__SATS__': sats_raw,
    '__TLE_DATE__': tle_date,
    '__NAV_MARK_LIGHT__': b64(BRAND, 'orbit-n-nav-light.png'),
    '__NAV_MARK__': b64(BRAND, 'orbit-n-nav.png'),
    '__N_MARK__': text(BRAND, 'n_contours.json'),
    '__DEBRIS_N__': '{:,}'.format(len(base64.b64decode(debris)) // 32),
    '__DEBRIS__': debris,
}
# Longer keys first, so __NAV_MARK_LIGHT__ is filled before __NAV_MARK__ and __DEBRIS_N__ before __DEBRIS__.
for key in sorted(fills, key=len, reverse=True):
    page = page.replace(key, fills[key])

# The page opens with its title, font links and stylesheet; those go in <head>, everything after them in <body>.
cut = page.index('</style>') + len('</style>')
head = '\n'.join(line for line in page[:cut].splitlines()
                 if not line.startswith('<title>') and 'claude:' not in line)
body = page[cut:].lstrip('\n')

DESCRIPTION = ('The Space, Cyber, and National Security Law Society, a student organization at the University of '
               'Nebraska College of Law. Read the Society’s monthly newsletter and subscribe.')
doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Space, Cyber, and National Security Law Society · Nebraska Law</title>
<meta name="description" content="{DESCRIPTION}">
<meta property="og:title" content="Space, Cyber, and National Security Law Society">
<meta property="og:description" content="{DESCRIPTION}">
<meta property="og:type" content="website">
<link rel="icon" type="image/png" href="favicon.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<style>
/* Base styles the page was designed on. */
:root{{color-scheme:light;padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}
body{{margin:0;font:14px/1.4 system-ui,-apple-system,"Segoe UI",sans-serif}}
img{{max-width:100%}}
[hidden]{{display:none!important}}
</style>
{head}
</head>
<body>
{body}
</body>
</html>
"""
with open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8') as f:
    f.write(doc)
left = [k for k in fills if k in doc]
print(f'index.html: {len(doc):,} bytes; satellite data from {tle_date}' + (f'; UNFILLED: {left}' if left else ''))
