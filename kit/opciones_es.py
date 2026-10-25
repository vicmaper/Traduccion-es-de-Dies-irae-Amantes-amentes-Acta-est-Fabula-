"""opciones_es.py - traduce las decisiones (opciones) y nombres de la caja de nombre del exec.dat de Dies irae.
Esos textos no están en la tabla de mensajes: están en los textos del código.
  python opciones_es.py exec.dat opciones_nombres.tsv exec_nuevo.dat
TSV: tipo (opcion|nombre), ingles, espanol   (filas con espanol vacío se ignoran)
Referencias en el código: 0A u16 o 0C u32 seguidas de 2D 49 (caja de nombre) o 0F 11 / 11 0x (opción).
El español se escribe en el espacio de los textos de depuración «■…\\n» y en el de los textos reemplazados;
el exec.dat no cambia de tamaño."""
import sys, os, re, struct, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import exectool as pt

def regiones(d):
    T, n = pt.find_table(d)
    ce = T - 4
    for p in range(0, 0x100000):
        ps = struct.unpack_from('<I', d, p)[0]
        if 0 < ps < len(d) and p + 4 + ps + 4 <= ce:
            q = p + 4 + ps
            if struct.unpack_from('<I', d, q)[0] == ce - (q + 4) and d[p+4:p+6] != b'\0\0':
                return p + 4, ps, q + 4, ce
    raise SystemExit('ERROR: no encontré el bloque de textos del código')

def textos(pool):
    out = {}; i = 0
    while i < len(pool):
        j = i
        while j + 1 < len(pool) and pool[j:j+2] != b'\0\0': j += 2
        out[i] = pool[i:j].decode('utf-16le', 'replace'); i = j + 2
    return out

_IDX = {}
def _indice(code):
    """todas las referencias 0C u32 / 0A u16 del código, de una sola pasada"""
    key = id(code)
    if key not in _IDX:
        idx = {}
        for m in re.finditer(rb'(?=\x0c(....))', code, re.S): idx.setdefault(struct.unpack('<I', m.group(1))[0], []).append((m.start() + 1, 4))
        for m in re.finditer(rb'(?=\x0a(..))', code, re.S): idx.setdefault(struct.unpack('<H', m.group(1))[0], []).append((m.start() + 1, 2))
        _IDX.clear(); _IDX[key] = (code, idx)
    return _IDX[key][1]

def refs(code, off):
    r = []
    for p, n in _indice(code).get(off, []):
        if True:
            k = code[p + n:p + n + 3]
            if k[:2] == b'\x2d\x49': t = 'nombre'
            elif k[:2] == b'\x0f\x11' or (k[:1] == b'\x11' and k[1:2] in b'\x01\x02\x03\x04\x05\x06'): t = 'opcion'
            elif k[:3] == b'\x04\x22\x01': t = 'depuracion'
            else: t = 'otro'
            r.append((p, n, t))
    return r

import hashlib
def clave(s): return hashlib.sha1(s.encode('utf-8')).hexdigest()[:16]

class Mapa(dict):
    """busca por texto inglés o por su clave (sha1 corta), para no distribuir el texto del juego"""
    def get(self, k, default=None):
        tipo, s = k
        return dict.get(self, (tipo, s), dict.get(self, (tipo, clave(s)), default))
    def __contains__(self, k):
        return self.get(k) is not None

def cargar_tsv(path):
    m = Mapa()
    for r in csv.DictReader(open(path, encoding='utf-8-sig'), delimiter='\t'):
        es = (r.get('espanol') or r.get('español') or '').strip()
        k = r.get('ingles') or r.get('clave')
        if es and k and es != k: m[(r['tipo'].strip(), k)] = es
    return m

def traducir(data, mapa):
    d = bytearray(data); P, PS, cs, ce = regiones(d)
    pool = bytearray(d[P:P+PS]); code0 = bytes(d[cs:ce]); code = bytearray(code0); tx = textos(bytes(pool))
    trab = []   # (offset_viejo, texto_nuevo, [refs a cambiar])
    for o, s in tx.items():
        rr = refs(code0, o)
        por_tipo = {}
        for x in rr:
            if x[2] in ('nombre', 'opcion'): por_tipo.setdefault(x[2], []).append(x)
        for tipo, lst in por_tipo.items():
            es = mapa.get((tipo, s))
            if es: trab.append((o, es, lst))
        # opciones dentro de XML <select ... text='...'>
        mm = re.search(r"text='([^']*)'", s)
        if s.startswith('<select') and mm and ('opcion', mm.group(1)) in mapa:
            nuevo = s.replace("text='%s'" % mm.group(1), "text='%s'" % mapa.get(('opcion', mm.group(1))).replace("'", '’'))
            trab.append((o, nuevo, [x for x in rr if x[2] != 'depuracion']))
    # huecos libres: textos de depuración usados solo por depuración + textos viejos cuyas refs se cambian todas
    libres = []
    for o, s in tx.items():
        if s.endswith('\n') and '%' not in s:
            r = refs(code0, o)
            if r and all(t == 'depuracion' for _, _, t in r): libres.append([o, o + (len(s) + 1) * 2])
    cambiadas = {}
    for o, es, lst in trab: cambiadas.setdefault(o, set()).update((p for p, _, _ in lst))
    for o, ps in cambiadas.items():
        todas = set(p for p, _, t in refs(code0, o) if t != 'depuracion')
        if todas <= ps: libres.append([o, o + (len(tx[o]) + 1) * 2])
    libres.sort(); m = []
    for a, b in libres:
        if m and a <= m[-1][1]: m[-1][1] = max(m[-1][1], b)
        else: m.append([a, b])
    libres = m
    necesita_bajo = {}
    for o, es, lst in trab:
        necesita_bajo[es] = necesita_bajo.get(es, False) or any(n == 2 for _, n, _ in lst)
    pos = {}
    def colocar(lista, huecos):
        for es in sorted(lista, key=lambda e: -len(e)):
            sz = len(es.encode('utf-16le')) + 2
            for h in sorted(huecos, key=lambda h: h[1] - h[0]):
                if h[1] - h[0] >= sz: pos[es] = h[0]; h[0] += sz; break
            else: raise SystemExit('ERROR: no cabe «%s»; acórtalo' % es)
    bajos = [[a, min(b, 0x10000)] for a, b in libres if a < 0x10000]
    altos = [[max(a, 0x10000), b] for a, b in libres if b > 0x10000]
    colocar([e for e, bj in necesita_bajo.items() if bj], bajos)
    colocar([e for e, bj in necesita_bajo.items() if not bj], altos + bajos)
    n_refs = 0
    for o, es, lst in trab:
        for p, n, t in lst:
            struct.pack_into('<H' if n == 2 else '<I', code, p, pos[es]); n_refs += 1
    for es, no in pos.items():
        b = es.encode('utf-16le') + b'\0\0'; pool[no:no+len(b)] = b
    d[P:P+PS] = pool; d[cs:ce] = code
    return bytes(d), len(trab), n_refs

if __name__ == '__main__':
    src, tsv, dst = sys.argv[1:4]
    out, nt, nr = traducir(open(src, 'rb').read(), cargar_tsv(tsv))
    open(dst, 'wb').write(out)
    print('OK: %d textos, %d referencias cambiadas -> %s' % (nt, nr, dst))
