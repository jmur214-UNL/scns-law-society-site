# Space, Cyber, and National Security Law Society — website

The public site of the Space, Cyber, and National Security Law Society, a student organization at the University of
Nebraska College of Law. Its main job is hosting the Society's monthly newsletter.

It is a single static page: plain HTML, CSS and JavaScript, with no framework and nothing to install to view it. Any
static host can serve it as it is (GitHub Pages, Netlify, Cloudflare Pages, a university web server).

## What's here

```
index.html              The site. This is the file that gets served. Built from src/ — don't edit it by hand.
favicon.png             Browser-tab icon (the orbit N).
apple-touch-icon.png    Home-screen icon for phones.
newsletter/2026-10/     Issue 01: the seven page images and the PDF.
src/site.html           The page as written: all the markup, styles and scripts. Edit this.
src/data/               Data embedded at build time: land mask, U.S. state and county lines, satellites, debris.
src/brand/              The orbit-N marks used in the nav bar and on the spacecraft.
tools/build.py          Builds index.html from src/.
tools/update_satellites.py   Refreshes the satellite and debris data (see below).
```

The page loads two things from outside: the Three.js 3D library (r128, from cdnjs) and the Oswald and Work Sans fonts
(from Google Fonts).

## Editing

1. Change `src/site.html`.
2. Rebuild: `python3 tools/build.py` (Python 3, no extra packages).
3. Preview: from the repo folder, run `python3 -m http.server 8000` and open <http://localhost:8000>. Use a local server
   rather than opening the file directly, so the newsletter pages and PDF load the way they will online.
4. Commit both `src/site.html` and the rebuilt `index.html`.

Placeholders like `__SATS__` in `src/site.html` are where `build.py` embeds data and images. Leave them in place.

### Things that are switched off, not deleted

- **Events section.** In the markup as `<section ... id="events" hidden>`, with its nav link also `hidden`. Remove both
  `hidden` attributes to bring it back.
- **Preview options panel** (season, time of day, weather and debris presets, for trying looks). Set
  `var PREVIEW_ON = false;` to `true` near the top of the main script to bring it back. While it is off, every visitor
  sees the defaults in `var ENV = {...}` just above it: the real season, golden hour, clear weather, debris off.
  Changing `time: 'golden'` to `time: 'live'` makes the sky follow the real sun in Lincoln.

### A new newsletter issue

Add the page images (`p1.webp`, `p2.webp`, …, 1400 × 1812) and the PDF to a new `newsletter/YYYY-MM/` folder. Then, in
`src/site.html`, update the issue paths and text in the newsletter section and in the `var ISSUE = {...}` block (title,
PDF path, file name, and one description per page for screen readers), and rebuild.

## Keeping the satellites current

The globe works out where each satellite and piece of debris is, live in the browser, from orbital elements captured on
the date `build.py` prints. They age: after a few weeks the dots drift away from where the real objects are, though the
page looks the same. To refresh:

```
python3 tools/update_satellites.py --catalog path/to/catalog.tle
python3 tools/build.py
```

The satellites (space stations and the brightest satellites) and the satellite catalog download from CelesTrak. The
debris layer needs a full-catalog TLE file with every tracked object, which Space-Track.org offers with a free account;
without `--catalog` the debris data is left as it is.

## Publishing with GitHub Pages

In the repository on GitHub: **Settings → Pages → Build and deployment**, source **Deploy from a branch**, branch
**main**, folder **/ (root)**. The site appears at `https://<account>.github.io/scns-law-society-site/` a minute or so
later, and a custom domain can be set on the same page.

## Credits

Coastlines and lakes from Natural Earth; state and county lines from the U.S. Census Bureau; orbital elements from
CelesTrak.
