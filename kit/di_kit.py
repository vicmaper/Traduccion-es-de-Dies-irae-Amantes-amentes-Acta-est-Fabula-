#!/usr/bin/env python3
"""di_kit.py - Kit de la traducción al español de Dies irae (Steam: Amantes amentes + parche R18 Acta est Fabula).
Funciona con TU copia del juego: lee tus archivos, pone el español encima y guarda respaldo de lo que cambia.
El kit no trae texto del juego (ni japonés ni inglés): solo el español.

Uso en consola (Windows, Linux o Steam Deck):
  python di_kit.py estado    "CARPETA DEL JUEGO"
  python di_kit.py instalar  "CARPETA DEL JUEGO" [--solo acta|amantes]
  python di_kit.py quitar    "CARPETA DEL JUEGO"
  python di_kit.py revisar                         (revisa el formato de los archivos de datos/)
Sin argumentos abre la ventana (di_gui.py)."""
import os, sys, csv, re, json, shutil, hashlib, time

if getattr(sys, 'frozen', False):                 # .exe hecho con PyInstaller
    BASE = sys._MEIPASS; JUNTO = os.path.dirname(sys.executable)
else:
    BASE = os.path.dirname(os.path.abspath(__file__)); JUNTO = os.path.dirname(BASE)
sys.path.insert(0, BASE)
import malie_dat, malie_pack, exectool, opciones_es

VERSION = '1.0'
DISCORD = 'https://discord.gg/NV8TbQQ7B'
CLAVE_ACTA = 'Dies irae ~Acta est Fabula~'
CLAVE_AM = 'Dies irae ~Amantes amentes~'
MD5_EXEC_ACTA = 'cca54ea1e9d2b34dbbbe02487f0c50a2'      # data/system/exec.dat del parche R18 (data4.dat)
MD5_PATCH_EN = '5a10d56489845df66b139e922cb0a1df'       # data/system/patch.en.dat de data4.cn.dat
VIDEO_ACTA = 'data/picture/event/mv_01e.webm'
VIDEO_AM = 'data/picture/event/mv_01.webm'
csv.field_size_limit(min(sys.maxsize, 2 ** 31 - 1))

def log(*a):
    print(*a, flush=True)

def carpeta_datos():
    """datos editables: si existe una carpeta 'datos' junto al kit/.exe se usa esa (cambios del usuario)"""
    for d in (os.path.join(JUNTO, 'datos'), os.path.join(BASE, 'datos')):
        if os.path.isfile(os.path.join(d, 'acta_es.tsv')): return d
    raise SystemExit('No encontré la carpeta datos (acta_es.tsv).')

def leer_es(nombre):
    p = os.path.join(carpeta_datos(), nombre); m = {}
    with open(p, encoding='utf-8-sig', newline='') as f:
        for r in csv.DictReader(f, delimiter='\t'):
            if r.get('id', '').strip().isdigit() and (r.get('espanol') or '').strip():
                m[int(r['id'])] = r['espanol']
    return m

def md5(b): return hashlib.md5(b).hexdigest()

TAGS = re.compile(r'\{(?:end|/v|v:[^}]*|r:[^}|]*\|[^}]*|u[0-9A-Fa-f]{4})\}')
def firma(t):
    if t.count('{u0007}{u000F}') == t.count('{u0007}{u0010}'):
        t = t.replace('{u0007}{u000F}', '').replace('{u0007}{u0010}', '')
    return ['{r}' if m.startswith('{r:') else m for m in TAGS.findall(t)]

def poner_espanol(exec_b, es):
    """mete el español (id -> texto con marcas) en la tabla de mensajes; valida las marcas contra el original"""
    import struct
    TABLE, count = exectool.find_table(exec_b)
    ents = [struct.unpack_from('<II', exec_b, TABLE + 8 * k) for k in range(count)]
    base = TABLE + 8 * count + 4
    msgs = [exec_b[base + o:base + o + l].decode('utf-16le') for o, l in ents]
    malas = []; n = 0
    for k, t in es.items():
        if k >= len(msgs): malas.append(k); continue
        orig = exectool.to_tags(msgs[k])
        if firma(t) != firma(orig): malas.append(k); continue
        if not t.endswith('{end}') and orig.endswith('{end}'): t += '{end}'
        msgs[k] = exectool.from_tags(t); n += 1
    pool = bytearray(); table = bytearray()
    for m in msgs:
        b = m.encode('utf-16le'); table += struct.pack('<II', len(pool), len(b)); pool += b + b'\0\0'
    return bytes(exec_b[:TABLE] + table + struct.pack('<I', len(pool)) + pool), n, malas

def opciones(exec_b, cual):
    p = os.path.join(carpeta_datos(), 'opciones_nombres.tsv')
    if not os.path.isfile(p): return exec_b
    try:
        nuevo, nt, nr = opciones_es.traducir(exec_b, opciones_es.cargar_tsv(p))
        log('   decisiones y nombres en español: %d textos' % nt); return nuevo
    except SystemExit as e:
        log('   AVISO: decisiones sin traducir (%s)' % e); return exec_b

# ---------------------------------------------------------------- detección
def estado(juego):
    e = {'juego': juego, 'ok': os.path.isdir(juego)}
    f = lambda n: os.path.join(juego, n)
    e['amantes'] = os.path.isfile(f('malie.exe')) and (os.path.isfile(f('data4.cn.dat')) or os.path.isfile(f('data4.cn.ORIGINAL.dat')))
    e['acta'] = os.path.isfile(f('malie_fabula.exe')) and os.path.isfile(f('data4.dat'))
    e['acta_es'] = os.path.isfile(f('data5.dat'))
    e['amantes_es'] = os.path.isfile(f('data4.cn.ORIGINAL.dat'))
    return e

def texto_estado(e):
    if not e['ok']: return 'No existe la carpeta.'
    s = []
    s.append('Amantes amentes (malie.exe): ' + ('encontrado' if e['amantes'] else 'NO encontrado') +
             (' — español instalado' if e['amantes_es'] else ''))
    s.append('Acta est Fabula (parche R18: malie_fabula.exe + data4.dat): ' + ('encontrado' if e['acta'] else 'NO encontrado') +
             (' — español instalado' if e['acta_es'] else ''))
    return '\n'.join(s)

# ---------------------------------------------------------------- instalar
def _guardar(ruta, b):
    tmp = ruta + '.nuevo'
    with open(tmp, 'wb') as f: f.write(b)
    os.replace(tmp, ruta)

def instalar_acta(juego):
    log('== Acta est Fabula (parche R18)')
    d4 = os.path.join(juego, 'data4.dat'); d5 = os.path.join(juego, 'data5.dat')
    d = malie_dat.Dat(d4); j = d.find('data/system/exec.dat')
    if j is None: raise RuntimeError('data4.dat no tiene exec.dat: ¿es el parche R18?')
    base = d.data(j); d.f.close()
    if md5(base) != MD5_EXEC_ACTA:
        raise RuntimeError('tu data4.dat es de otra versión del parche R18 (md5 %s). Avísanos en Discord.' % md5(base))
    log('   poniendo el español en el guion...')
    nuevo, n, malas = poner_espanol(base, leer_es('acta_es.tsv'))
    log('   mensajes en español: %d%s' % (n, ('  (con marcas mal, se quedaron en inglés: %d)' % len(malas)) if malas else ''))
    files = {'data/system/exec.dat': opciones(nuevo, 'Acta')}
    if os.path.isfile(d5):                          # conservar un video en español de una instalación anterior
        try:
            v = malie_dat.Dat(d5); jv = v.find(VIDEO_ACTA)
            if jv is not None: files[VIDEO_ACTA] = v.data(jv); log('   se conserva el video del prólogo en español')
            v.f.close()
        except SystemExit: pass
        shutil.copy2(d5, d5 + '.anterior')
    log('   armando data5.dat (cifrado)...')
    tmp = d5 + '.armando'; malie_pack.pack(files, CLAVE_ACTA, tmp); os.replace(tmp, d5)
    log('   LISTO: %s' % d5)

def instalar_amantes(juego):
    log('== Amantes amentes')
    act = os.path.join(juego, 'data4.cn.dat'); orig = os.path.join(juego, 'data4.cn.ORIGINAL.dat')
    src = orig if os.path.isfile(orig) else act
    d = malie_dat.Dat(src); files = {p: d.data(j) for j, p, isdir in d.walk() if not isdir}; d.f.close()
    pen = files.get('data/system/patch.en.dat')
    if pen is None or md5(pen) != MD5_PATCH_EN:
        raise RuntimeError('tu data4.cn.dat no es el original de Steam (¿actualización nueva?). '
                           'Usa «Verificar integridad de archivos» en Steam y vuelve a intentar.')
    vid = None
    if src == orig and os.path.isfile(act):
        try:
            a = malie_dat.Dat(act); jv = a.find(VIDEO_AM)
            if jv is not None: vid = a.data(jv)
            a.f.close()
        except SystemExit: pass
    log('   poniendo el español en el guion...')
    nuevo, n, malas = poner_espanol(pen, leer_es('amantes_es.tsv'))
    log('   mensajes en español: %d%s' % (n, ('  (con marcas mal, se quedaron en inglés: %d)' % len(malas)) if malas else ''))
    files['data/system/patch.en.dat'] = opciones(nuevo, 'Amantes')
    if vid: files[VIDEO_AM] = vid; log('   se conserva el video del prólogo en español')
    if src == act:
        log('   respaldo del original: data4.cn.ORIGINAL.dat'); shutil.copy2(act, orig)
    log('   armando data4.cn.dat (cifrado, ~100 MB)...')
    tmp = act + '.armando'; malie_pack.pack(files, CLAVE_AM, tmp); os.replace(tmp, act)
    log('   LISTO: %s' % act)

def instalar(juego, solo=None):
    e = estado(juego)
    if not e['ok']: raise RuntimeError('no existe la carpeta: %s' % juego)
    try: import numpy  # noqa
    except Exception: log('AVISO: sin numpy el cifrado es lento (puede tardar 10-30 min). En Windows usa el .exe.')
    hecho = False
    if solo in (None, 'amantes'):
        if e['amantes']: instalar_amantes(juego); hecho = True
        else: log('No encontré malie.exe/data4.cn.dat: se salta Amantes.')
    if solo in (None, 'acta'):
        if e['acta']: instalar_acta(juego); hecho = True
        else: log('No encontré malie_fabula.exe/data4.dat (parche R18): se salta Acta est Fabula.')
    if not hecho: raise RuntimeError('no encontré el juego en esa carpeta.')
    log('\nTerminado. El idioma del juego debe estar en INGLÉS (el español va encima del inglés).')

def quitar(juego):
    d5 = os.path.join(juego, 'data5.dat'); act = os.path.join(juego, 'data4.cn.dat'); orig = os.path.join(juego, 'data4.cn.ORIGINAL.dat')
    if os.path.isfile(d5):
        os.replace(d5, d5 + '.desinstalado'); log('Acta: data5.dat renombrado a data5.dat.desinstalado')
    if os.path.isfile(orig):
        os.replace(orig, act); log('Amantes: data4.cn.dat original restaurado')
    log('Listo: el juego quedó como estaba.')

# ---------------------------------------------------------------- revisar datos (para quien edite la traducción)
def revisar():
    malos = 0
    for nombre in ('acta_es.tsv', 'amantes_es.tsv'):
        es = leer_es(nombre)
        for k, t in es.items():
            e = []
            if re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', t): e.append('japonés')
            if '…' in t: e.append('usa «…» (deben ser tres puntos ...)')
            if re.search(r'[«»“”]', t): e.append('comillas « » o “ ”')
            if t.count('"') % 2: e.append('comillas impares')
            if t.count('{') != t.count('}'): e.append('llave sin cerrar')
            if e: malos += 1; log('%s id %d: %s' % (nombre, k, ', '.join(e)))
    log('Revisión: %d con problemas (las marcas {…} se comprueban al instalar, contra tu juego).' % malos)
    return malos

def main(a):
    if not a:
        import di_gui; di_gui.main(); return
    cmd = a[0]
    if cmd == 'revisar': revisar(); return
    if len(a) < 2: print(__doc__); return
    juego = a[1]
    if cmd == 'estado': log(texto_estado(estado(juego)))
    elif cmd == 'instalar':
        solo = a[a.index('--solo') + 1] if '--solo' in a else None
        instalar(juego, solo)
    elif cmd == 'quitar': quitar(juego)
    else: print(__doc__)

if __name__ == '__main__':
    try: main(sys.argv[1:])
    except RuntimeError as e: log('ERROR: %s' % e); sys.exit(1)
