"""malie_dat.py - lee .dat LIBP de MALIE con cifrado Camellia (claves GARbro) o CFI (Dies irae 2017+).
Detecta la clave sola. Solo lectura."""
import struct, os, sys, json, pickle
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cfi
CFI_K='a4a7a6a1a0a3a2acafaea9a8abaab4b7b6b1b0b3b2bcbfbeb9b8bbbaa1a9b1b9'
AQUI=os.path.dirname(os.path.abspath(__file__))
def claves():
    S=json.load(open(os.path.join(AQUI,'malie_claves_todas.json'),encoding='utf-8'))
    return S
class Dat:
    def __init__(s,path,forzar=None):
        s.f=open(path,'rb'); raw=s.f.read(16); s.clave=None
        for nombre,v in claves().items():
            if forzar and nombre!=forzar: continue
            if v['tipo']=='cfi':
                dec=cfi.Cfi(bytes.fromhex(v['key']),v['rot']); fn=dec.decrypt
            else:
                import malie_cipher as mc
                kt=list(v['key']); fn=(lambda kt: (lambda d,st: (mc.set_key(kt), mc.crypt(d,mc.decrypt_block,st))[1]))(kt)
            h=fn(raw,0)
            if h[:4]==b'LIBP':
                c,fc=struct.unpack_from('<II',h,4)
                if 0<c<2000000 and 0<fc<2000000: s.clave=nombre; s.fn=fn; s.align=v['align']; break
        if not s.clave:
            # clave CFI desconocida: se reconstruye del bloque 0x10 (nombre de la raiz = ceros)
            s.f.seek(16); c=bytearray(s.f.read(16)); f0=c[0]
            for i in range(1,16): c[i]^=f0
            w=struct.unpack('<4I',c); K=bytes.fromhex(CFI_K)
            rot=[cfi.rotl(w[0],K[1]^0xA5),cfi.rotr(w[1],K[4]^0xA5),cfi.rotl(w[2],K[7]^0xA5),cfi.rotr(w[3],K[10]^0xA5)]
            dec=cfi.Cfi(K,rot); h=dec.decrypt(raw,0)
            if h[:4]==b'LIBP':
                s.clave='RECONSTRUIDA cfi rot=%s'%rot; s.fn=dec.decrypt; s.align=1024
            else: raise SystemExit('ninguna clave abre '+path)
        h=s.read(0,16); s.cnt,s.fcnt=struct.unpack_from('<II',h,4)
        s.tbl=16+32*s.cnt; head=s.read(0,s.tbl+4*s.fcnt); s.ents=[]
        for i in range(s.cnt):
            # el nombre puede tener hasta 22 bytes: los 2 ultimos van en los bytes bajos de flags
            o=16+32*i; name=head[o:o+22].split(b'\0')[0].decode('ascii','replace')
            fl,a,b=struct.unpack_from('<III',head,o+20); fl&=0xFFFF0000; s.ents.append((name,fl,a,b))
        s.offs=struct.unpack_from('<%dI'%s.fcnt,head,s.tbl)
        end=s.tbl+4*s.fcnt; s.base=(end+s.align-1)&~(s.align-1)
    def read(s,pos,size):
        a=pos&~15; b=(pos+size+15)&~15; s.f.seek(a); raw=s.f.read(b-a); raw+=b'\0'*((-len(raw))%16)
        return s.fn(raw,a)[pos-a:pos-a+size]
    def kids(s,i):
        n,fl,a,b=s.ents[i]
        if i==0 and not (fl&0x30000): return list(range(a,a+b)) if a>0 else [0]
        return [] if (fl&0x30000) or a<=i else list(range(a,a+b))
    def walk(s,i=0,pre=''):
        for j in s.kids(i):
            n,fl=s.ents[j][0],s.ents[j][1]; p=pre+'/'+n if pre else n
            yield j,p,not(fl&0x30000)
            if not(fl&0x30000) and j!=i: yield from s.walk(j,p)
    def find(s,path):
        i=0
        for part in [p for p in path.split('/') if p]:
            for j in s.kids(i):
                if s.ents[j][0].lower()==part.lower(): i=j; break
            else: return None
        return i
    def data(s,i):
        n,fl,a,sz=s.ents[i]; return s.read(s.base+s.offs[a]*1024,sz)
