import struct
try:
    import numpy as np
except Exception:
    np=None
def rotr(v,s): s&=31; return ((v>>s)|(v<<(32-s)))&0xFFFFFFFF if s else v
def rotl(v,s): s&=31; return ((v<<s)|(v>>(32-s)))&0xFFFFFFFF if s else v
class Cfi:
    def __init__(s,key,rot): s.k=bytes(key); s.r=list(rot)
    def block(s,off,b):
        b=bytearray(b); o=off&0xF; f=b[o]
        for i in range(16):
            if i!=o: b[i]^=f
        n=off>>4; K=s.k; R=s.r
        d=list(struct.unpack('<4I',b))
        k=rotr(R[0],K[n&31]^0xA5); d[0]=rotr(d[0]^k,K[(n+12)&31]^0xA5)
        k=rotl(R[1],K[(n+3)&31]^0xA5); d[1]=rotl(d[1]^k,K[(n+15)&31]^0xA5)
        k=rotr(R[2],K[(n+6)&31]^0xA5); d[2]=rotr(d[2]^k,K[(n-14)&31]^0xA5)
        k=rotl(R[3],K[(n+9)&31]^0xA5); d[3]=rotl(d[3]^k,K[(n-11)&31]^0xA5)
        return struct.pack('<4I',*d)
    def decrypt(s,data,start):
        if np is None:
            out=bytearray()
            for i in range(0,len(data),16): out+=s.block(start+i,data[i:i+16])
            return bytes(out)
        # numpy vectorizado
        a=np.frombuffer(bytes(data),dtype=np.uint8).reshape(-1,16).copy()
        nb=a.shape[0]; offs=np.arange(nb,dtype=np.int64)*16+start
        o=(offs&0xF).astype(np.int64)
        first=a[np.arange(nb),o]
        mask=np.ones((nb,16),dtype=bool); mask[np.arange(nb),o]=False
        a=np.where(mask,a^first[:,None],a)
        w=a.view('<u4').reshape(nb,4).astype(np.uint64)
        n=(offs>>4)
        K=np.frombuffer(s.k,dtype=np.uint8).astype(np.uint64)
        def g(x): return K[(n+x)&31]^0xA5
        def vr(v,sh): sh=sh&31; return ((v>>sh)|(v<<((32-sh)&63)))&0xFFFFFFFF if True else v
        def ROTR(v,sh): sh=(sh&31).astype(np.uint64); return np.where(sh==0,v,((v>>sh)|(v<<(np.uint64(32)-sh)))&0xFFFFFFFF)
        def ROTL(v,sh): sh=(sh&31).astype(np.uint64); return np.where(sh==0,v,((v<<sh)|(v>>(np.uint64(32)-sh)))&0xFFFFFFFF)
        R=[np.uint64(x) for x in s.r]
        out=np.empty_like(w)
        out[:,0]=ROTR(w[:,0]^ROTR(np.full(nb,R[0]),g(0)),g(12))
        out[:,1]=ROTL(w[:,1]^ROTL(np.full(nb,R[1]),g(3)),g(15))
        out[:,2]=ROTR(w[:,2]^ROTR(np.full(nb,R[2]),g(6)),g(-14))
        out[:,3]=ROTL(w[:,3]^ROTL(np.full(nb,R[3]),g(9)),g(-11))
        return out.astype('<u4').tobytes()

def _enc_block(s, off, b):
    K=s.k; R=s.r; n=off>>4
    p=list(struct.unpack('<4I',bytes(b)))
    k=rotr(R[0],K[n&31]^0xA5); w0=rotl(p[0],K[(n+12)&31]^0xA5)^k
    k=rotl(R[1],K[(n+3)&31]^0xA5); w1=rotr(p[1],K[(n+15)&31]^0xA5)^k
    k=rotr(R[2],K[(n+6)&31]^0xA5); w2=rotl(p[2],K[(n-14)&31]^0xA5)^k
    k=rotl(R[3],K[(n+9)&31]^0xA5); w3=rotr(p[3],K[(n-11)&31]^0xA5)^k
    st=bytearray(struct.pack('<4I',w0,w1,w2,w3)); o=off&0xF; f=st[o]
    for i in range(16):
        if i!=o: st[i]^=f
    return bytes(st)
def _encrypt(s, data, start):
    out=bytearray()
    for i in range(0,len(data),16): out+=_enc_block(s,start+i,data[i:i+16])
    return bytes(out)
Cfi.encrypt=_encrypt

def _encrypt_np(s, data, start):
    """Cifrado vectorizado con numpy (mucho más rápido); mismo resultado que _encrypt."""
    if np is None: return _encrypt(s, data, start)
    a=np.frombuffer(bytes(data),dtype=np.uint8).reshape(-1,16)
    nb=a.shape[0]; offs=np.arange(nb,dtype=np.int64)*16+start; n=offs>>4
    w=a.view('<u4').reshape(nb,4).astype(np.uint64)
    K=np.frombuffer(s.k,dtype=np.uint8).astype(np.uint64)
    def g(x): return K[(n+x)&31]^0xA5
    def ROTR(v,sh): sh=(sh&31).astype(np.uint64); return np.where(sh==0,v,((v>>sh)|(v<<(np.uint64(32)-sh)))&0xFFFFFFFF)
    def ROTL(v,sh): sh=(sh&31).astype(np.uint64); return np.where(sh==0,v,((v<<sh)|(v>>(np.uint64(32)-sh)))&0xFFFFFFFF)
    R=[np.full(nb,np.uint64(x)) for x in s.r]
    out=np.empty_like(w)
    out[:,0]=ROTL(w[:,0],g(12))^ROTR(R[0],g(0))
    out[:,1]=ROTR(w[:,1],g(15))^ROTL(R[1],g(3))
    out[:,2]=ROTL(w[:,2],g(-14))^ROTR(R[2],g(6))
    out[:,3]=ROTR(w[:,3],g(-11))^ROTL(R[3],g(9))
    b=out.astype('<u4').view(np.uint8).reshape(nb,16).copy()
    o=(offs&0xF).astype(np.int64); first=b[np.arange(nb),o]
    mask=np.ones((nb,16),dtype=bool); mask[np.arange(nb),o]=False
    b=np.where(mask,b^first[:,None],b).astype(np.uint8)
    return b.tobytes()
Cfi.encrypt=_encrypt_np
