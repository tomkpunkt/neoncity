"""Rauchtest für Neon City mit Playwright (Python).

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


LEER = "NEON.G=Array.from({length:400},()=>({g:0,m:0,s:0,c:0,sg:[]}));NEON.rebuild()"
D, H = 0.14, 0.62
BAUTEN = "NEON.G.filter(c=>c.m)"


def desktop(p):
    browser, pg, meldungen = seite(p, 1400, 860)
    pg.wait_for_timeout(6000)
    pg.evaluate('NEON.killIntro()')
    st = pg.evaluate('NEON.STATS')
    pruefe('Startviertel erzeugt', st['floors'] > 100, f"{st['floors']} Etagen")
    pruefe('Autos auf den Straßen', pg.evaluate('NEON.gcars') > 0, f"{pg.evaluate('NEON.gcars')} Autos")
    pg.screenshot(path=str(OUT / 'start.png'))

    pg.evaluate(LEER)
    a, b = proj(pg, -1.5, 0, -1.5), proj(pg, 1.5, 0, 1.5)
    pg.mouse.move(*a)
    pg.mouse.down()
    for t in range(1, 11):
        pg.mouse.move(a[0] + (b[0] - a[0]) * t / 10, a[1] + (b[1] - a[1]) * t / 10)
    lbl = pg.evaluate("document.getElementById('lbl').textContent")
    pg.mouse.up()
    n = pg.evaluate(BAUTEN + '.length')
    pruefe('Fläche 4×4 aufziehen', n == 16 and lbl == '4 × 4', f'{n} Zellen, Etikett „{lbl}“')
    pruefe('Fläche ist ein Gebäude (gleicher Stil und gleiche Farbe)', pg.evaluate(f"new Set({BAUTEN}.map(c=>c.s+'/'+c.c)).size") == 1)

    pg.evaluate("NEON.setTool('shape')")
    p0 = proj(pg, 0, D + H, 0)
    pg.mouse.move(*p0)
    pg.wait_for_timeout(200)
    hl0 = pg.evaluate('NEON.hl.count')
    pg.mouse.down()
    for t in range(1, 11):
        pg.mouse.move(p0[0], p0[1] - t * 15)
    hl1 = pg.evaluate('NEON.hl.count')
    pg.mouse.up()
    hs = pg.evaluate(f'[...new Set({BAUTEN}.map(c=>NEON.topOf(c.m)))]')
    pruefe('Dach hochziehen (Push/Pull)', len(hs) == 1 and hs[0] > 3, f'Höhe {hs}')
    pruefe('Push/Pull-Fläche leuchtet beim Zeigen und Ziehen', hl0 == 16 and hl1 == 16, f'{hl0} / {hl1} Felder')

    q, qq = proj(pg, 2.0, D + 1.5 * H, 0.5), proj(pg, 4.0, D + 1.5 * H, 0.5)
    pg.mouse.move(*q)
    pg.mouse.down()
    for t in range(1, 11):
        pg.mouse.move(q[0] + (qq[0] - q[0]) * t / 10, q[1] + (qq[1] - q[1]) * t / 10)
    pg.mouse.up()
    n = pg.evaluate(BAUTEN + '.length')
    pruefe('Fassade herausziehen', n > 16, f'{n} Zellen')

    pg.evaluate("NEON.setTool('corner')")
    h = pg.evaluate('NEON.topOf(NEON.G.find(c=>c.m).m)')
    pg.mouse.click(*proj(pg, 0.5, D + h * H, 0.5))
    pruefe('Ganzes Gebäude abrunden (Dachmitte)', pg.evaluate(BAUTEN + '.every(c=>c.cn&&c.cn.every(v=>v===2))'))
    pg.wait_for_timeout(1200)
    pg.screenshot(path=str(OUT / 'formen.png'))

    vorher = pg.evaluate('NEON.snap()')
    pg.evaluate('NEON.undo()')
    pg.evaluate('NEON.redo()')
    pruefe('Rückgängig und Wiederholen', pg.evaluate('NEON.snap()') == vorher)
    pruefe('Stadt-Code Rundreise', pg.evaluate('(()=>{const s=NEON.snap();NEON.load(s);return NEON.snap()===s})()'))
    alt = '{"v":1,"app":"neonstadt","n":20,"cells":[[210,3,3,1,2,0],[211,3,4,1,2,1],[212,1,0,0,0,0]]}'
    erg = pg.evaluate(f"(()=>{{NEON.load({alt!r});const G=NEON.G;return[G[210].m,G[211].m,G[211].g,G[212].g]}})()")
    pruefe('Spielstand im alten Format 1 wird umgebaut', erg == [7, 14, 1, 1], str(erg))

    # Überhang: Seitenklick auf Höhe 3 setzt einen frei auskragenden Block, Rechtsklick nimmt eine Etage aus der Mitte
    pg.evaluate(LEER + ";NEON.G[10*20+10]={g:0,m:63,s:1,c:0,sg:[]};NEON.rebuild();NEON.setTool('build')")
    pg.mouse.click(*proj(pg, 1.0, D + 3.5 * H, 0.5))
    m = pg.evaluate('NEON.G[10*20+11].m')
    pruefe('Überhang auf Höhe 3 per Seitenklick', m == 8, f'Maske {m}')
    pg.mouse.click(*proj(pg, 0.5, D + 1.5 * H, 1.0), button='right')
    m = pg.evaluate('NEON.G[10*20+10].m')
    pruefe('Etage aus der Mitte abreißen', m == 61, f'Maske {m}')

    # Innenecke einer L-Form wird gefüllt, Hohlkehle an Außenecken
    n = pg.evaluate(LEER + """;(()=>{const G=NEON.G,s=(n)=>G[n]={g:0,m:15,s:1,c:3,sg:[],cn:[2,2,2,2]};s(210);s(211);s(230);G[250]={g:0,m:15,s:0,c:1,sg:[],cn:[3,3,3,3]};NEON.rebuild();return[NEON.B.f12.n,NEON.B.q03.n]})()""")
    pruefe('Innenecke gefüllt und Hohlkehle gebaut', n[0] >= 4 and n[1] >= 4, f'Füllstücke {n[0]}, Hohlkehlen-Viertel {n[1]}')

    # Formen: Fläche, Etage, Reihe, Block
    BLOCK = LEER + ";(()=>{for(let j=8;j<12;j++)for(let i=8;i<12;i++)NEON.G[j*20+i]={g:0,m:7,s:1,c:0,sg:[]};NEON.rebuild();NEON.setTool('shape')})()"
    seite_p, raus = proj(pg, 1.97, D + 1.5 * H, -0.5), proj(pg, 3.4, D + 1.5 * H, -0.5)
    def ziehen(a, b):
        pg.mouse.move(*a)
        pg.mouse.down()
        for t in range(1, 11):
            pg.mouse.move(a[0] + (b[0] - a[0]) * t / 10, a[1] + (b[1] - a[1]) * t / 10)
        pg.mouse.up()
    erg = {}
    for modus in ['flaeche', 'etage', 'reihe', 'block']:
        pg.evaluate(BLOCK + f";NEON.setPullMode('{modus}')")
        pg.mouse.move(*seite_p)
        pg.wait_for_timeout(150)
        anz = pg.evaluate('NEON.hl.count')
        ziehen(seite_p, raus)
        erg[modus] = (anz, pg.evaluate('[8,9,10,11].map(j=>NEON.G[j*20+12].m)'))
    pruefe('Formen „Fläche“: ganze Fassade raus', erg['flaeche'] == (4, [7, 7, 7, 7]), str(erg['flaeche']))
    pruefe('Formen „Etage“: nur diese Etage raus (Überhang)', erg['etage'] == (4, [2, 2, 2, 2]), str(erg['etage']))
    pruefe('Formen „Reihe“: ein senkrechter Streifen raus', erg['reihe'] == (1, [0, 7, 0, 0]), str(erg['reihe']))
    pruefe('Formen „Block“: ein einzelnes Feld raus', erg['block'] == (1, [0, 2, 0, 0]), str(erg['block']))
    pg.evaluate(BLOCK + ";NEON.setPullMode('reihe')")
    dach = proj(pg, 0.5, D + 3 * H, 0.5)
    pg.mouse.move(*dach)
    pg.wait_for_timeout(150)
    pruefe('Formen „Reihe“ auf dem Dach markiert 4 Felder', pg.evaluate('NEON.hl.count') == 4)
    pg.evaluate("NEON.setPullMode('block')")
    ziehen(dach, (dach[0], dach[1] - 120))
    hs = pg.evaluate('[...new Set(NEON.G.filter(c=>c.m).map(c=>NEON.topOf(c.m)))].sort()')
    pruefe('Formen „Block“ auf dem Dach hebt nur ein Feld', len(hs) == 2 and hs[0] == 3 and pg.evaluate('NEON.G.filter(c=>c.m&&NEON.topOf(c.m)>3).length') == 1, str(hs))
    pg.evaluate("NEON.setPullMode('flaeche')")

    # Stützen für Überhänge: 1 Feld = L-Verbinder, sonst alle zwei Felder vom Ende gezählt; über Straßen ein Portal
    def stuetzen(n, strasse=False):
        js = LEER + f""";(()=>{{const G=NEON.G;G[10*20+3]={{g:0,m:31,s:1,c:2,sg:[]}};for(let t=1;t<={n};t++)G[10*20+3+t]={{g:{1 if strasse else 0},m:16,s:1,c:2,sg:[]}};
          NEON.rebuild();const M=NEON.B.conc.M,xs=[];for(let q=0;q<NEON.B.conc.n;q++)if(M[q*16+5]>1)xs.push(+(M[q*16+12]+9.5).toFixed(2));return[NEON.B.wedgeC.n,xs]}})()"""
        return pg.evaluate(js)
    w, xs = stuetzen(1)
    pruefe('Überhang 1 Feld: L-Verbinder', w == 2 and not xs, f'{w} Keile')
    # Park-Ebenen: 0 Wiese, 1-2 Bäume, 3 Statue, 4 Brunnen, 5 Monument; unter einem Überhang wird abgestuft
    def park(pk, m=0):
        return pg.evaluate(LEER + f""";(()=>{{NEON.G[210]={{g:2,m:{m},s:1,c:0,sg:[],pk:{pk}}};NEON.rebuild();const B=NEON.B;return[B.tree.n,B.ring.n,B.roof.n]}})()""")
    ebenen = [park(k) for k in range(6)]
    pruefe('Park-Ebenen: Wiese, Bäume, Statue, Brunnen, Monument',
           ebenen[0][0] == 0 and ebenen[1][0] >= 1 and ebenen[2][0] >= 2 and ebenen[3][1] >= 1 and ebenen[4][1] >= 1 and ebenen[5][2] >= 1, str(ebenen))
    unter, frei = park(5, 2), park(0, 2)
    pruefe('Monument unter Überhang wird zum Brunnen', unter[2] == frei[2] and unter[1] > frei[1], f'{unter} gegen {frei}')
    pg.evaluate(LEER + ";NEON.G[210]={g:2,m:0,s:0,c:0,sg:[],pk:0};NEON.rebuild();NEON.setTool('park')")
    mitte = proj(pg, 0.5, D + .02, 0.5)
    pg.mouse.click(*mitte)
    nach_klick = pg.evaluate('NEON.G[210].pk')
    oben = proj(pg, 0.5, D + .02 + 3 * H, 0.5)
    pg.mouse.move(*mitte)
    pg.mouse.down()
    for t in range(1, 11):
        pg.mouse.move(mitte[0] + (oben[0] - mitte[0]) * t / 10, mitte[1] + (oben[1] - mitte[1]) * t / 10)
    pg.mouse.up()
    nach_ziehen = pg.evaluate('NEON.G[210].pk')
    pruefe('Park: Klick hebt eine Ebene, Hochziehen mehrere', nach_klick == 1 and nach_ziehen == 4, f'Klick {nach_klick}, Ziehen {nach_ziehen}')
    neu = pg.evaluate(LEER + ";(()=>{NEON.setTool('park');return 0})()")
    pg.mouse.click(*proj(pg, 2.5, D + .02, 0.5))
    pruefe('Neuer Park startet als Wiese', pg.evaluate('NEON.G[212].g===2&&NEON.G[212].pk===0'))
    pruefe('Park-Ebene bleibt im Stadt-Code', pg.evaluate("(()=>{NEON.G[212].pk=4;const s=NEON.snap();NEON.load(s);return NEON.G[212].pk})()") == 4)
    pg.evaluate("NEON.setTool('build')")
    # Eckmodifikation an der tragenden Wand: an dieser Ecke kein L-Verbinder
    def keile(cn):
        return pg.evaluate(LEER + f""";(()=>{{const G=NEON.G;G[10*20+3]={{g:0,m:31,s:1,c:2,sg:[],cn:{cn}}};G[10*20+4]={{g:0,m:16,s:1,c:2,sg:[]}};
          NEON.rebuild();const M=NEON.B.wedgeC.M,zs=[];for(let q=0;q<NEON.B.wedgeC.n;q++)zs.push(+(M[q*16+14]+9.5).toFixed(2));return zs}})()""")
    alle, eine = keile('[2,2,2,2]'), keile('[2,0,0,0]')
    pruefe('Abgerundete Ecken: kein L-Verbinder an diesen Ecken', alle == [] and len(eine) == 1 and eine[0] < 10, f'alle rund {alle}, eine Ecke rund {eine}')
    erg = {n: sorted(stuetzen(n)[1]) for n in [2, 3, 4, 5, 6]}
    soll = {2: [5.0], 3: [6.0], 4: [5.0, 7.0], 5: [6.0, 8.0], 6: [5.0, 7.0, 9.0]}
    pruefe('Stützen alle zwei Felder: 2, 3, 2-4, 3-5, 2-4-6', erg == soll, str(erg))
    port = pg.evaluate(LEER + """;(()=>{const G=NEON.G;for(let i=2;i<18;i++){G[9*20+i]={g:1,m:0,s:0,c:0,sg:[]};G[10*20+i]={g:1,m:0,s:0,c:0,sg:[]}}
      G[8*20+9]={g:0,m:31,s:1,c:2,sg:[]};G[9*20+9].m=16;G[9*20+9].s=1;G[10*20+9].m=16;G[10*20+9].s=1;NEON.rebuild();
      const M=NEON.B.conc.M,zs=[];for(let q=0;q<NEON.B.conc.n;q++)if(M[q*16+5]>1)zs.push(+(M[q*16+14]).toFixed(2));return zs.sort()})()""")
    pruefe('Portal über breiter Straße: Pfosten an beiden Rändern', port == [-0.96, 0.96], str(port))
    ax = pg.evaluate(LEER + """;(()=>{const G=NEON.G;for(let i=2;i<18;i++){G[9*20+i]={g:1,m:0,s:0,c:0,sg:[]};G[10*20+i]={g:1,m:0,s:0,c:0,sg:[]}}G[11*20+6]={g:3,m:0,s:0,c:0,sg:[]};NEON.rebuild();return NEON.roadAxis(6,10)})()""")
    pruefe('Straße neben einem Platz bleibt gerade (keine falsche Kreuzung)', ax == 1, f'Einordnung {ax}')

    # Breite Straßen: T-Einmündung über beide Spuren, Kurve, Ende, Abzweig am Ende
    STR = "NEON.G=Array.from({length:400},()=>({g:0,m:0,s:0,c:0,sg:[]}));const S=(i,j)=>NEON.G[j*20+i]={g:1,m:0,s:0,c:0,sg:[]};"
    def art(bau, frage):
        return pg.evaluate(f"(()=>{{{STR}{bau};NEON.rebuild();return {frage}}})()")
    t = art("for(let i=0;i<9;i++){S(i,2);S(i,3)}for(let j=4;j<8;j++)S(3,j)", "[NEON.roadKind(3,3),NEON.roadKind(3,2),NEON.roadKind(5,2)]")
    pruefe('Breite Straße: T-Einmündung gilt für beide Spuren', t == [3, 3, 1], str(t))
    k = art("for(let i=2;i<9;i++){S(i,2);S(i,3)}for(let j=4;j<9;j++){S(7,j);S(8,j)}", "[7,8].flatMap(i=>[2,3].map(j=>NEON.roadKind(i,j)))")
    pruefe('Breite Kurve: kein Kreuzungsfeld', k == [5, 5, 5, 5], str(k))
    e = art("for(let i=2;i<9;i++){S(i,5);S(i,6)}", "[NEON.roadKind(2,5),NEON.roadKind(8,6)]")
    pruefe('Ende einer breiten Straße bleibt gerade', e == [1, 1], str(e))
    h = art("for(let i=10;i<18;i++)S(i,10);for(let j=11;j<16;j++){S(15,j);S(16,j)}", "[NEON.roadKind(15,10),NEON.roadKind(16,10)]")
    pruefe('Schmale Querstraße am Ende einer breiten: Kreuzung über beide Spuren', h == [3, 3], str(h))

    # Abriss-Rechteck schneidet auf Höhe 2
    erg = pg.evaluate("""(()=>{NEON.generate(7);NEON.rebuild();NEON.rectPlan({tool:'erase',i0:0,j0:0,i1:19,j1:19,Lb:2}).run();return Math.max(...NEON.G.filter(c=>c.m).map(c=>NEON.topOf(c.m)))})()""")
    pruefe('Abriss-Rechteck schneidet auf Höhe 2', erg == 2, f'höchstes Gebäude {erg}')

    # Tastatur: gedrückt halten gleitet und rollt nach dem Loslassen aus
    pg.evaluate('NEON.generate(7);NEON.rebuild()')
    z0 = pg.evaluate('NEON.controls.target.z')
    pg.keyboard.down('w')
    pg.wait_for_timeout(300)
    z1 = pg.evaluate('NEON.controls.target.z')
    pg.wait_for_timeout(700)
    z2 = pg.evaluate('NEON.controls.target.z')
    pg.keyboard.up('w')
    pg.wait_for_timeout(500)
    z3 = pg.evaluate('NEON.controls.target.z')
    weich = abs(z1 - z0) < abs(z2 - z1) and abs(z3 - z2) > 0.001
    pruefe('Tastatur gleitet weich (anfahren und ausrollen)', weich, f'{z0:.2f} → {z1:.2f} → {z2:.2f} → {z3:.2f}')

    pg.evaluate('NEON.setTilt(false)')
    aus = pg.evaluate('NEON.tiltOn')
    pg.evaluate('NEON.setTilt(true)')
    pruefe('Tilt-Shift schaltbar', aus is False and pg.evaluate('NEON.tiltOn') is True)

    # Ruhemodus: ohne Mausbewegung blendet die Oberfläche aus; der erste Klick auf die leere Stelle der Leiste holt sie zurück, ohne zu bauen
    pg.mouse.move(700, 300)
    pg.wait_for_timeout(4300)
    weg = pg.evaluate("document.body.classList.contains('idle')")
    vorher = pg.evaluate('NEON.snap()')
    mitte = pg.evaluate("(()=>{const r=document.querySelector('.dock').getBoundingClientRect();return [r.left+r.width/2,r.top+r.height/2]})()")
    pg.mouse.click(*mitte)
    pg.wait_for_timeout(200)
    da = not pg.evaluate("document.body.classList.contains('idle')")
    pruefe('Oberfläche blendet ohne Mausbewegung aus, Klick holt sie zurück', weg and da and pg.evaluate('NEON.snap()') == vorher, f'aus {weg}, zurück {da}')
    pg.wait_for_timeout(4300)
    pruefe('Maus über der Leiste hält die Oberfläche sichtbar', not pg.evaluate("document.body.classList.contains('idle')"))
    pruefe('Titel „Neon City“', pg.title() == 'Neon City' and pg.evaluate("document.querySelector('.brand h1').textContent") == 'Neon City', pg.title())
    # Neon-Werkzeug: Kontur auf der Fläche unter dem Zeiger und Etikett neben dem Zeiger
    pg.evaluate(LEER + ";NEON.G[10*20+10]={g:0,m:63,s:1,c:0,sg:[]};NEON.rebuild();NEON.setTool('neon')")
    def zielen(x, y, z):
        q = proj(pg, x, y, z)
        pg.mouse.move(q[0] - 3, q[1] - 3)
        pg.mouse.move(*q)
        pg.wait_for_timeout(250)
        return pg.evaluate("[NEON.faceHL.visible, document.getElementById('lbl').style.display==='block'?document.getElementById('lbl').textContent:'']"), q
    (sichtbar_w, wand), q = zielen(1.0, D + 2.5 * H, 0.5)
    pg.mouse.click(*q)
    pg.wait_for_timeout(250)
    (_, wand2), _ = zielen(1.0, D + 2.5 * H, 0.45)
    (sichtbar_d, dach), _ = zielen(0.5, D + 6 * H, 0.5)
    pruefe('Neon zielt sichtbar: Wandschild, nach dem Setzen „entfernen“, Dach-Werbetafel',
           sichtbar_w and sichtbar_d and wand in ('Wandschild', 'Wall sign') and wand2 in ('Wandschild entfernen', 'Remove wall sign') and dach in ('Werbetafel aufs Dach', 'Roof billboard'),
           f'{wand} / {wand2} / {dach}')
    pg.evaluate("NEON.setTool('build')")

    # Schilder ziehen: zwei Etagen = Doppelschild, drei Felder = Leinwand; Dach über zwei Felder = doppelte Werbetafel
    pg.evaluate(LEER + ";for(const n of [210,211,212])NEON.G[n]={g:0,m:63,s:1,c:0,sg:[]};for(const n of [214,215,216])NEON.G[n]={g:0,m:15,s:1,c:2,sg:[]};NEON.rebuild();NEON.setTool('neon')")
    ziehen(proj(pg, 0.5, D + 1.5 * H, 1.0), proj(pg, 0.5, D + 2.5 * H, 1.0))
    ziehen(proj(pg, 0.5, D + 3.5 * H, 1.0), proj(pg, 2.5, D + 4.5 * H, 1.0))
    ziehen(proj(pg, 0.5, D + 6 * H, 0.5), proj(pg, 1.5, D + 6 * H, 0.5))
    sg, bb = pg.evaluate('JSON.stringify(NEON.G[210].sg.map(q=>[q[0],q[1],q[3],q[4]]))'), pg.evaluate('[NEON.G[210].bb,NEON.G[211].bb]')
    pruefe('Schilder ziehen: Doppelschild, Leinwand 3 × 2, doppelte Werbetafel', sg == '[[1,1,1,2],[1,3,3,2]]' and bb == [2, 0], f'{sg} {bb}')
    # Dachgarten per Klick, Magnetbahn über drei Dächer gezogen
    pg.evaluate("NEON.setTool('park')")
    pg.mouse.click(*proj(pg, 2.5, D + 6 * H, 0.5))
    pg.evaluate("NEON.setTool('street')")
    ziehen(proj(pg, 4.5, D + 4 * H, 0.5), proj(pg, 6.5, D + 4 * H, 0.5))
    rt = pg.evaluate('[NEON.G[212].rt,NEON.G[214].rt,NEON.G[215].rt,NEON.G[216].rt,NEON.trains.length]')
    pruefe('Dachgarten und Magnetbahn mit Zug', rt == [1, 2, 2, 2, 1], str(rt))
    pruefe('Schilder, Dachgarten und Bahn überstehen den Stadt-Code', pg.evaluate('(()=>{const s=NEON.snap();NEON.load(s);NEON.rebuild();return NEON.snap()===s&&NEON.G[212].rt===1&&NEON.G[210].sg[1].length===5})()'))
    br = pg.evaluate(LEER + ";(()=>{const G=NEON.G;G[202]={g:0,m:15,s:1,c:2,sg:[],rt:2};G[206]={g:0,m:15,s:1,c:2,sg:[],rt:2};G[204]={g:0,m:3,s:0,c:1,sg:[]};G[230]={g:0,m:15,s:1,c:2,sg:[],rt:2};G[250]={g:0,m:31,s:1,c:2,sg:[],rt:2};G[240]={g:0,m:255,s:1,c:2,sg:[],rt:2};NEON.rebuild();return [NEON.trains.length,+NEON.trains[0].len.toFixed(2)]})()")
    pruefe('Magnetbahn: Brücke über drei Felder Lücke (auch über ein niedriges Haus), nur auf einer Ebene', br[0] == 1 and 3.99 < br[1] < 4.01, str(br))
    pg.evaluate("NEON.setTool('build')")

    # Tageszeit-Regler und Wetter-Auswahl mit Mehrfachauswahl
    regler = pg.evaluate("(()=>{const r=document.getElementById('tday').getBoundingClientRect();return [r.left,r.top+r.height/2,r.width]})()")
    pg.mouse.click(regler[0] + regler[2] * 0.5, regler[1])
    pg.wait_for_timeout(300)
    stunde, anzeige = pg.evaluate('NEON.hour'), pg.evaluate("document.getElementById('tdayLbl').textContent")
    pruefe('Zeitregler stellt die Tageszeit (Mitte = Mittag)', 11.5 <= stunde <= 12.5 and anzeige.startswith('12:'), f'{stunde:.2f} h, Anzeige {anzeige}')
    pruefe('Tageslicht am Mittag', pg.evaluate('NEON.AP.day') > 0.9)
    alte = pg.evaluate("[!!document.getElementById('bRain'),!!document.getElementById('bAtmo')]")
    pg.click('#bWx')
    offen = pg.evaluate("!document.getElementById('wxMenu').hidden")
    for k in ['snow', 'fog']:
        pg.click(f'.wxi[data-wx="{k}"]')
    an = pg.evaluate("Object.entries(NEON.wth).filter(([k,v])=>v.on).map(([k])=>k).sort().join(',')")
    pg.keyboard.press('Escape')
    zu = pg.evaluate("document.getElementById('wxMenu').hidden")
    pruefe('Wetter-Menü: mehrere gleichzeitig wählbar', offen and zu and an == 'fog,rain,snow', an)
    pruefe('Knöpfe für Regen und Stimmung sind weg', alte == [False, False], str(alte))
    pg.evaluate("['snow','fog'].forEach(k=>NEON.setWeather(k,false,true,true))")
    pruefe('Keine Seitenfehler (Desktop)', not meldungen, '; '.join(meldungen[:3]))
    browser.close()


def handy(p):
    browser, pg, meldungen = seite(p, 390, 844, touch=True)
    pg.wait_for_timeout(5000)
    pg.evaluate('NEON.killIntro()')
    pg.evaluate(LEER)
    pg.touchscreen.tap(*proj(pg, 0.5, 0, 0.5))
    pg.wait_for_timeout(300)
    pg.touchscreen.tap(*proj(pg, 0.5, D + H, 0.5))
    pg.wait_for_timeout(300)
    hs = pg.evaluate("NEON.G.filter(c=>c.m).map(c=>NEON.topOf(c.m)).join(',')")
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
