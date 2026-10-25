"""malie_pack.py - arma un .dat LIBP cifrado con CFI (Dies irae 2017+).
Uso: python malie_pack.py SALIDA.dat "NOMBRE_CLAVE" carpeta_raiz
  carpeta_raiz contiene data/... ; se empaqueta todo lo que haya dentro."""
import os, sys, struct, json
AQUI=os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0,AQUI)
import cfi
ALIGN=1024
def pack(files, clave, out):
    """files: dict 'data/system/exec.dat' -> bytes"""
    v=json.load(open(os.path.join(AQUI,'malie_claves_todas.json'),encoding='utf-8'))[clave]
    C=cfi.Cfi(bytes.fromhex(v['key']),v['rot'])
    tree={}
    for p,b in files.items():
        node=tree; parts=p.split('/')
        for d in parts[:-1]: node=node.setdefault(d,{})
        node[parts[-1]]=b
    ents=[['',0,1,1]]; datas=[]
    # Igual que los .dat originales: cada carpeta escribe sus hijos juntos (orden por bytes del nombre)
    # y luego se recorre cada subcarpeta en profundidad (DFS).
    def visit(node,idx):
        names=sorted(node,key=lambda n:n.encode())
        first=len(ents); ents[idx][2]=first; ents[idx][3]=len(names)
        subs=[]
        for n in names:
            if len(n.encode())>22: raise SystemExit('nombre largo: '+n)
            if isinstance(node[n],bytes):
                ents.append([n,0x10000,len(datas),len(node[n])]); datas.append(node[n])
            else:
                ents.append([n,0,0,0]); subs.append((node[n],len(ents)-1))
        for sn,si in subs: visit(sn,si)
    visit(tree,0)
    head=bytearray(b'LIBP'+struct.pack('<III',len(ents),len(datas),0))
    for n,fl,a,b in ents:
        nb=n.encode().ljust(22,b'\0')   # bytes 20-21 del nombre van en la parte baja de flags
        head+=nb[:20]+struct.pack('<III',fl|nb[20]|(nb[21]<<8),a,b)
    offs=[]; body=bytearray(); 
    for b in datas:
        offs.append(len(body)//1024); body+=b; body+=b'\0'*((-len(body))%1024)
    head+=struct.pack('<%dI'%len(offs),*offs)
    head+=b'\0'*((-len(head))%ALIGN)
    plain=bytes(head+body); plain+=b'\0'*((-len(plain))%16)
    open(out,'wb').write(C.encrypt(plain,0))
    return len(plain)
if __name__=='__main__':
    out,clave,root=sys.argv[1:4]; files={}
    for dp,dn,fn in os.walk(root):
        for f in fn:
            full=os.path.join(dp,f); rel=os.path.relpath(full,root).replace(os.sep,'/')
            files[rel]=open(full,'rb').read()
    print('OK', out, pack(files,clave,out),'bytes', len(files),'archivos')
