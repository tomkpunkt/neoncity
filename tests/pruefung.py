"""Rauchtest für Neonstadt mit Playwright (Python).

Aufruf:  python3 tests/pruefung.py [ausgabeordner]

- Holt three.js, GSAP und Tone.js in genau den Versionen aus index.html per `npm pack`
  in einen Zwischenspeicher (Standard: <tmp>/neonstadt-libs, änderbar mit NEON_LIBCACHE)
  und leitet die CDN-Adressen dorthin um. So läuft der Test auch ohne Zugriff auf das CDN.
  Vorgehen nach gamedev/techniken/playwright-canvas-pruefung ("CDN-Bibliotheken aus npm einspielen").
- Chrome-Pfad über NEON_CHROME, sonst das von Playwright installierte Chromium.
- Screenshots landen im Ausgabeordner (Standard: <tmp>/neonstadt-pruefung), nie im Projektordner.
- Exit-Code 1, sobald eine Prüfung fehlschlägt.
"""
import os
import sys
import pathlib
import subprocess
import tempfile

from playwright.sync_api import sync_playwright

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIBS = {'three': '0.170.0', 'gsap': '3.12.5', 'tone': '14.8.49'}
CACHE = pathlib.Path(os.environ.get('NEON_LIBCACHE', pathlib.Path(tempfile.gettempdir()) / 'neonstadt-libs'))
OUT = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path(tempfile.gettempdir()) / 'neonstadt-pruefung')
FEHLER = []


def libs_holen():
    html = (ROOT / 'index.html').read_text(encoding='utf-8')
    for name, ver in LIBS.items():
        if f'{name}@{ver}' not in html:
            sys.exit(f'Version {name}@{ver} steht nicht in index.html – LIBS in diesem Skript anpassen.')
        ziel = CACHE / f'{name}-{ver}'
        if (ziel / 'package').exists():
            continue
        ziel.mkdir(parents=True, exist_ok=True)
        tgz = subprocess.check_output(['npm', 'pack', f'{name}@{ver}', '--silent'], cwd=ziel, text=True).strip().splitlines()[-1]
        subprocess.check_call(['tar', 'xzf', tgz], cwd=ziel)


def umleiten(route):
    url = route.request.url
    for name, ver in LIBS.items():
        marke = f'{name}@{ver}/'
        if marke in url:
            pfad = CACHE / f'{name}-{ver}' / 'package' / url.split(marke, 1)[1]
            if pfad.exists():
                return route.fulfill(path=str(pfad), content_type='application/javascript')
    return route.abort()


def pruefe(name, ok, info=''):
    print(('ok    ' if ok else 'FEHLER ') + name + (f'  ({info})' if info else ''))
    if not ok:
        FEHLER.append(name)


def seite(p, w, h, touch=False):
    args = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']
    exe = os.environ.get('NEON_CHROME')
    browser = p.chromium.launch(executable_path=exe, args=args) if exe else p.chromium.launch(args=args)
    ctx = browser.new_context(viewport={'width': w, 'height': h}, has_touch=touch, is_mobile=touch)
    pg = ctx.new_page()
    meldungen = []
    pg.on('pageerror', lambda e: meldungen.append(str(e)))
    pg.on('console', lambda m: meldungen.append(m.text) if m.type == 'error' else None)
    pg.route('https://cdn.jsdelivr.net/**', umleiten)
    pg.route('https://fonts.googleapis.com/**', lambda r: r.fulfill(body='', content_type='text/css'))
    pg.route('https://fonts.gstatic.com/**', lambda r: r.abort())
    pg.goto((ROOT / 'index.html').as_uri())
    pg.wait_for_function('!!window.NEON', timeout=30000)
    return browser, pg, meldungen


def proj(pg, x, y, z):
    return pg.evaluate(f'NEON.project({x},{y},{z})')


LEER = "NEON.G=Array.from({length:400},()=>({k:0,h:0,s:0,c:0,a:0,sg:[]}));NEON.rebuild()"
D, H = 0.14, 0.62


def desktop(p):
    browser, pg, meldungen = seite(p, 1400, 860)
    pg.wait_for_timeout(6000)
    st = pg.evaluate('NEON.STATS')
    pruefe('Startviertel erzeugt', st['floors'] > 100, f"{st['floors']} Etagen")
    pg.screenshot(path=str(OUT / 'start.png'))

    pg.evaluate(LEER)
    a, b = proj(pg, -1.5, 0, -1.5), proj(pg, 1.5, 0, 1.5)
    pg.mouse.move(*a)
    pg.mouse.down()
    for t in range(1, 11):
        pg.mouse.move(a[0] + (b[0] - a[0]) * t / 10, a[1] + (b[1] - a[1]) * t / 10)
    lbl = pg.evaluate("document.getElementById('lbl').textContent")
    pg.mouse.up()
    n = pg.evaluate('NEON.G.filter(c=>c.k===3).length')
    pruefe('Fläche 4×4 aufziehen', n == 16 and lbl == '4 × 4', f'{n} Zellen, Etikett „{lbl}“')
    pruefe('Fläche ist ein Gebäude (gleicher Stil und gleiche Farbe)', pg.evaluate("new Set(NEON.G.filter(c=>c.k===3).map(c=>c.s+'/'+c.c)).size") == 1)

    pg.evaluate("NEON.setTool('shape')")
    p0 = proj(pg, 0, D + H, 0)
    pg.mouse.move(*p0)
    pg.mouse.down()
    for t in range(1, 11):
        pg.mouse.move(p0[0], p0[1] - t * 15)
    pg.mouse.up()
    hs = pg.evaluate('[...new Set(NEON.G.filter(c=>c.k===3).map(c=>c.h))]')
    pruefe('Dach hochziehen (Push/Pull)', len(hs) == 1 and hs[0] > 3, f'Höhe {hs}')

    q, qq = proj(pg, 2.0, D + 1.5 * H, 0.5), proj(pg, 4.0, D + 1.5 * H, 0.5)
    pg.mouse.move(*q)
    pg.mouse.down()
    for t in range(1, 11):
        pg.mouse.move(q[0] + (qq[0] - q[0]) * t / 10, q[1] + (qq[1] - q[1]) * t / 10)
    pg.mouse.up()
    n = pg.evaluate('NEON.G.filter(c=>c.k===3).length')
    pruefe('Fassade herausziehen', n > 16, f'{n} Zellen')

    pg.evaluate("NEON.setTool('corner')")
    h = pg.evaluate('NEON.G.find(c=>c.k===3).h')
    pg.mouse.click(*proj(pg, 0.5, D + h * H, 0.5))
    cn = pg.evaluate("NEON.G.filter(c=>c.k===3).every(c=>c.cn&&c.cn.every(v=>v===2))")
    pruefe('Ganzes Gebäude abrunden (Dachmitte)', cn)
    pg.wait_for_timeout(1200)
    pg.screenshot(path=str(OUT / 'formen.png'))

    vorher = pg.evaluate('NEON.snap()')
    pg.evaluate('NEON.undo()')
    pg.evaluate('NEON.redo()')
    pruefe('Rückgängig und Wiederholen', pg.evaluate('NEON.snap()') == vorher)
    pruefe('Stadt-Code Rundreise', pg.evaluate('(()=>{const s=NEON.snap();NEON.load(s);return NEON.snap()===s})()'))

    erg = pg.evaluate("""(()=>{NEON.generate(7);NEON.rebuild();
      NEON.rectPlan({tool:'erase',i0:0,j0:0,i1:19,j1:19,Lb:2}).run();
      return Math.max(...NEON.G.filter(c=>c.k===3).map(c=>c.h))})()""")
    pruefe('Abriss-Rechteck schneidet auf Höhe 2', erg == 2, f'höchstes Gebäude {erg}')
    pruefe('Keine Seitenfehler (Desktop)', not meldungen, '; '.join(meldungen[:3]))
    browser.close()


def handy(p):
    browser, pg, meldungen = seite(p, 390, 844, touch=True)
    pg.wait_for_timeout(5000)
    pg.evaluate(LEER)
    pg.touchscreen.tap(*proj(pg, 0.5, 0, 0.5))
    pg.wait_for_timeout(300)
    pg.touchscreen.tap(*proj(pg, 0.5, D + H, 0.5))
    pg.wait_for_timeout(300)
    hs = pg.evaluate("NEON.G.filter(c=>c.k===3).map(c=>c.h).join(',')")
    pruefe('Tippen baut und stockt auf', hs == '2', hs)
    pg.screenshot(path=str(OUT / 'handy.png'))
    pruefe('Keine Seitenfehler (Handy)', not meldungen, '; '.join(meldungen[:3]))
    browser.close()


if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    libs_holen()
    with sync_playwright() as p:
        desktop(p)
        handy(p)
    print(f'\nScreenshots: {OUT}')
    sys.exit(1 if FEHLER else 0)
