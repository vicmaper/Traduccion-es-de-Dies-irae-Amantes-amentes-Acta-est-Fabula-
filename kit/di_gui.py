#!/usr/bin/env python3
"""di_gui.py - Ventana del kit de traducción al español de Dies irae.
Windows: DiesIrae_ES.exe (o ABRIR_KIT.bat). Linux / Steam Deck: ./abrir_kit.sh"""
import os, sys, io, csv, re, queue, threading, traceback, webbrowser, subprocess, shutil
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import di_kit as K

TITULO = 'Dies irae — Traducción al español  v' + K.VERSION
NOMBRE_JUEGO = 'Dies irae ~Amantes amentes~'

def candidatos():
    """carpetas típicas de Steam donde puede estar el juego"""
    raices = []
    if sys.platform == 'win32':
        for u in 'CDEFGH':
            raices += [u + r':\Program Files (x86)\Steam', u + r':\Program Files\Steam', u + r':\SteamLibrary', u + r':\Steam']
    else:
        h = os.path.expanduser('~')
        raices += [h + '/.local/share/Steam', h + '/.steam/steam', h + '/.var/app/com.valvesoftware.Steam/.local/share/Steam']
        raices += [os.path.join('/run/media', x) for x in (os.listdir('/run/media') if os.path.isdir('/run/media') else [])]
        for m in list(raices):
            if m.startswith('/run/media/') and os.path.isdir(m):
                raices += [os.path.join(m, x) for x in os.listdir(m)]
    extra = []
    for r in raices:                                   # bibliotecas extra de libraryfolders.vdf
        vdf = os.path.join(r, 'steamapps', 'libraryfolders.vdf')
        if os.path.isfile(vdf):
            try:
                for p in re.findall(r'"path"\s+"([^"]+)"', open(vdf, encoding='utf-8', errors='ignore').read()):
                    extra.append(p.replace('\\\\', '\\'))
            except Exception: pass
    out = []
    for r in raices + extra:
        p = os.path.join(r, 'steamapps', 'common', NOMBRE_JUEGO)
        if os.path.isfile(os.path.join(p, 'malie.exe')) and p not in out: out.append(p)
    return out

class Cola(io.TextIOBase):
    def __init__(self, q): self.q = q
    def write(self, s): self.q.put(s); return len(s)
    def flush(self): pass

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(TITULO); self.geometry('980x700'); self.minsize(820, 560)
        self.q = queue.Queue(); self.ocupado = False
        s = ttk.Style(self)
        try: s.theme_use('vista' if sys.platform == 'win32' else 'clam')
        except tk.TclError: pass
        s.configure('Titulo.TLabel', font=('Segoe UI' if sys.platform == 'win32' else 'Sans', 14, 'bold'))
        s.configure('Nota.TLabel', foreground='#555')
        s.configure('Grande.TButton', padding=(10, 7))
        nb = ttk.Notebook(self); nb.pack(fill='both', expand=True, padx=6, pady=6)
        self.t1 = ttk.Frame(nb); self.t2 = ttk.Frame(nb); self.t3 = ttk.Frame(nb)
        nb.add(self.t1, text='  Instalar  '); nb.add(self.t2, text='  Editar traducción  '); nb.add(self.t3, text='  Ayuda / Steam Deck  ')
        self._instalar(); self._editor(); self._ayuda()
        self.after(100, self._leer_cola)

    # ------------------------------------------------------------ pestaña instalar
    def _instalar(self):
        f = self.t1; f.columnconfigure(0, weight=1)
        ttk.Label(f, text=TITULO, style='Titulo.TLabel').grid(row=0, column=0, columnspan=3, sticky='w', padx=12, pady=(12, 0))
        ttk.Label(f, text='Funciona con TU copia de Steam. El kit no trae texto del juego: solo el español. '
                          'Antes de cambiar algo guarda respaldo.', style='Nota.TLabel', wraplength=900
                  ).grid(row=1, column=0, columnspan=3, sticky='w', padx=12)
        ttk.Label(f, text='Carpeta del juego (donde está malie.exe):').grid(row=2, column=0, sticky='w', padx=12, pady=(14, 2))
        c = candidatos()
        self.v_juego = tk.StringVar(value=c[0] if c else '')
        e = ttk.Entry(f, textvariable=self.v_juego); e.grid(row=3, column=0, sticky='we', padx=(12, 4))
        ttk.Button(f, text='Examinar…', command=self._elegir).grid(row=3, column=1, padx=4)
        ttk.Button(f, text='Buscar', command=self._buscar).grid(row=3, column=2, padx=(4, 12))
        self.v_juego.trace_add('write', lambda *a: self._estado())
        self.l_estado = ttk.Label(f, text='', justify='left'); self.l_estado.grid(row=4, column=0, columnspan=3, sticky='w', padx=12, pady=8)
        b = ttk.Frame(f); b.grid(row=5, column=0, columnspan=3, sticky='w', padx=8)
        ttk.Button(b, text='Instalar todo', style='Grande.TButton', command=lambda: self._correr(None)).pack(side='left', padx=4)
        ttk.Button(b, text='Solo Amantes amentes', command=lambda: self._correr('amantes')).pack(side='left', padx=4)
        ttk.Button(b, text='Solo Acta est Fabula', command=lambda: self._correr('acta')).pack(side='left', padx=4)
        ttk.Button(b, text='Quitar traducción', command=self._quitar).pack(side='left', padx=(24, 4))
        ttk.Button(b, text='Abrir carpeta', command=self._abrir).pack(side='left', padx=4)
        ttk.Label(f, text='Registro:').grid(row=6, column=0, sticky='w', padx=12, pady=(10, 0))
        self.txt = tk.Text(f, height=18, wrap='word', state='disabled', font=('Consolas' if sys.platform == 'win32' else 'Monospace', 9))
        self.txt.grid(row=7, column=0, columnspan=3, sticky='nsew', padx=12, pady=(2, 12)); f.rowconfigure(7, weight=1)
        self._estado()

    def _elegir(self):
        d = filedialog.askdirectory(title='Carpeta del juego (donde está malie.exe)')
        if d: self.v_juego.set(os.path.normpath(d))

    def _buscar(self):
        c = candidatos()
        if c: self.v_juego.set(c[0]); self._escribir('Encontrado: %s\n' % c[0])
        else: messagebox.showinfo(TITULO, 'No lo encontré solo. Usa «Examinar…».\nEn Steam: clic derecho en Dies irae → Administrar → Ver archivos locales.')

    def _estado(self):
        j = self.v_juego.get().strip()
        self.l_estado.config(text=K.texto_estado(K.estado(j)) if j else 'Elige la carpeta del juego.')

    def _escribir(self, s):
        self.txt.config(state='normal'); self.txt.insert('end', s); self.txt.see('end'); self.txt.config(state='disabled')

    def _leer_cola(self):
        try:
            while True: self._escribir(self.q.get_nowait())
        except queue.Empty: pass
        self.after(100, self._leer_cola)

    def _hilo(self, fn, fin=None):
        if self.ocupado: return
        self.ocupado = True; self.config(cursor='watch')
        def run():
            viejo = sys.stdout; sys.stdout = Cola(self.q)
            try: fn()
            except Exception as e:
                print('\nERROR: %s' % e)
                if not isinstance(e, RuntimeError): print(traceback.format_exc())
            finally:
                sys.stdout = viejo; self.ocupado = False
                self.after(0, lambda: (self.config(cursor=''), self._estado(), fin and fin()))
        threading.Thread(target=run, daemon=True).start()

    def _correr(self, solo):
        j = self.v_juego.get().strip()
        if not j: return messagebox.showwarning(TITULO, 'Primero elige la carpeta del juego.')
        self._escribir('\n=== Instalando en %s ===\n' % j)
        self._hilo(lambda: K.instalar(j, solo))

    def _quitar(self):
        j = self.v_juego.get().strip()
        if j and messagebox.askyesno(TITULO, '¿Quitar la traducción y dejar el juego como estaba?'):
            self._hilo(lambda: K.quitar(j))

    def _abrir(self):
        j = self.v_juego.get().strip()
        if not os.path.isdir(j): return
        if sys.platform == 'win32': os.startfile(j)
        else: subprocess.Popen(['xdg-open', j])

    # ------------------------------------------------------------ pestaña editar
    def _editor(self):
        f = self.t2; f.columnconfigure(1, weight=1); f.rowconfigure(2, weight=1)
        top = ttk.Frame(f); top.grid(row=0, column=0, columnspan=2, sticky='we', padx=8, pady=8)
        self.v_cual = tk.StringVar(value='acta_es.tsv')
        ttk.Radiobutton(top, text='Acta est Fabula', variable=self.v_cual, value='acta_es.tsv', command=self.ed_cargar).pack(side='left')
        ttk.Radiobutton(top, text='Amantes amentes', variable=self.v_cual, value='amantes_es.tsv', command=self.ed_cargar).pack(side='left', padx=8)
        ttk.Label(top, text='Buscar:').pack(side='left', padx=(16, 2))
        self.v_buscar = tk.StringVar(); eb = ttk.Entry(top, textvariable=self.v_buscar, width=30); eb.pack(side='left')
        eb.bind('<Return>', lambda e: self.ed_filtrar())
        ttk.Button(top, text='Buscar', command=self.ed_filtrar).pack(side='left', padx=4)
        ttk.Button(top, text='Ver inglés de mi juego', command=self.ed_ingles).pack(side='left', padx=(16, 4))
        ttk.Label(f, text='Los cambios se guardan en la carpeta «datos» junto al kit. Después usa «Instalar» otra vez.',
                  style='Nota.TLabel').grid(row=1, column=0, columnspan=2, sticky='w', padx=10)
        self.lista = ttk.Treeview(f, columns=('id', 'es'), show='headings', selectmode='browse')
        self.lista.heading('id', text='id'); self.lista.heading('es', text='Español')
        self.lista.column('id', width=70, stretch=False); self.lista.column('es', width=600)
        self.lista.grid(row=2, column=0, columnspan=2, sticky='nsew', padx=8)
        self.lista.bind('<<TreeviewSelect>>', self.ed_sel)
        self.l_en = ttk.Label(f, text='', wraplength=900, style='Nota.TLabel', justify='left')
        self.l_en.grid(row=3, column=0, columnspan=2, sticky='we', padx=10, pady=(6, 0))
        self.tx = tk.Text(f, height=6, wrap='word'); self.tx.grid(row=4, column=0, columnspan=2, sticky='we', padx=8, pady=4)
        bb = ttk.Frame(f); bb.grid(row=5, column=0, columnspan=2, sticky='w', padx=8, pady=(0, 8))
        ttk.Button(bb, text='Guardar este mensaje', command=self.ed_guardar).pack(side='left')
        self.l_msg = ttk.Label(bb, text=''); self.l_msg.pack(side='left', padx=12)
        self.es = {}; self.en = {}; self.actual = None
        self.after(300, self.ed_cargar)

    def ed_cargar(self):
        try: self.es = K.leer_es(self.v_cual.get())
        except SystemExit as e: self.es = {}; self.l_msg.config(text=str(e))
        self.en = {}; self.ed_filtrar()

    def ed_filtrar(self):
        t = self.v_buscar.get().strip().lower()
        self.lista.delete(*self.lista.get_children()); n = 0
        for k in sorted(self.es):
            s = self.es[k]
            if t and t not in s.lower() and t != str(k): continue
            self.lista.insert('', 'end', iid=str(k), values=(k, re.sub(r'\{[^}]*\}', ' ', s)[:200])); n += 1
            if n >= 3000: break
        self.l_msg.config(text='%d mensajes%s' % (n, ' (se muestran 3000; afina la búsqueda)' if n >= 3000 else ''))

    def ed_ingles(self):
        """lee el inglés de TU juego (solo en memoria, para comparar)"""
        j = self.v_juego.get().strip(); cual = self.v_cual.get()
        try:
            if cual == 'acta_es.tsv':
                d = K.malie_dat.Dat(os.path.join(j, 'data4.dat')); b = d.data(d.find('data/system/exec.dat'))
            else:
                p = os.path.join(j, 'data4.cn.ORIGINAL.dat')
                d = K.malie_dat.Dat(p if os.path.isfile(p) else os.path.join(j, 'data4.cn.dat'))
                b = d.data(d.find('data/system/patch.en.dat'))
            _, msgs, _, _ = self._load(b)
            self.en = {k: K.exectool.to_tags(m) for k, m in enumerate(msgs)}
            self.l_msg.config(text='Inglés cargado de tu juego (%d mensajes).' % len(self.en))
        except Exception as e:
            messagebox.showwarning(TITULO, 'No pude leer el inglés de tu juego.\nRevisa la carpeta en la pestaña Instalar.\n\n%s' % e)

    def _load(self, b):
        import struct
        T, n = K.exectool.find_table(b)
        ents = [struct.unpack_from('<II', b, T + 8 * k) for k in range(n)]
        base = T + 8 * n + 4
        return b, [b[base + o:base + o + l].decode('utf-16le') for o, l in ents], base, T

    def ed_sel(self, ev=None):
        s = self.lista.selection()
        if not s: return
        k = int(s[0]); self.actual = k
        self.tx.delete('1.0', 'end'); self.tx.insert('1.0', self.es.get(k, ''))
        self.l_en.config(text=('Inglés: ' + self.en[k]) if k in self.en else 'Pulsa «Ver inglés de mi juego» para ver el original.')

    def ed_guardar(self):
        if self.actual is None: return
        t = self.tx.get('1.0', 'end-1c').replace('\n', ' ').strip()
        if self.actual in self.en and K.firma(t) != K.firma(self.en[self.actual]):
            return messagebox.showwarning(TITULO, 'Las marcas {…} no coinciden con el original. Revisa {end}, {v:…}{/v}, {u000A}…')
        dst = os.path.join(K.JUNTO, 'datos'); os.makedirs(dst, exist_ok=True)
        src = K.carpeta_datos()
        for n in ('acta_es.tsv', 'amantes_es.tsv', 'opciones_nombres.tsv'):
            if not os.path.isfile(os.path.join(dst, n)): shutil.copy2(os.path.join(src, n), os.path.join(dst, n))
        self.es[self.actual] = t
        p = os.path.join(dst, self.v_cual.get())
        with open(p, 'w', encoding='utf-8', newline='') as fo:
            w = csv.writer(fo, delimiter='\t', lineterminator='\n'); w.writerow(['id', 'espanol'])
            for k in sorted(self.es): w.writerow([k, self.es[k]])
        self.lista.item(str(self.actual), values=(self.actual, re.sub(r'\{[^}]*\}', ' ', t)[:200]))
        self.l_msg.config(text='Guardado mensaje %d en %s' % (self.actual, p))

    # ------------------------------------------------------------ pestaña ayuda
    def _ayuda(self):
        f = self.t3
        t = tk.Text(f, wrap='word', font=('Segoe UI' if sys.platform == 'win32' else 'Sans', 10)); t.pack(fill='both', expand=True, padx=8, pady=8)
        t.insert('1.0', AYUDA); t.config(state='disabled')
        ttk.Button(f, text='Discord del grupo', command=lambda: webbrowser.open(K.DISCORD)).pack(pady=(0, 8))

AYUDA = """CÓMO SE INSTALA
1. Ten Dies irae ~Amantes amentes~ de Steam. Para Acta est Fabula (versión para adultos) copia además el parche R18
   oficial (malie_fabula.exe y data4.dat) en la carpeta del juego.
2. En la pestaña Instalar elige la carpeta del juego y pulsa «Instalar todo».
3. Pon el idioma del juego en INGLÉS (el español va encima del inglés). La interfaz (menús) se queda en inglés.

CÓMO SE JUEGA
- Amantes amentes: botón Jugar de Steam.
- Acta est Fabula: abre malie_fabula.exe. Necesita que tengas al menos una ruta terminada en Amantes (lo exige el juego).

SI STEAM ACTUALIZA EL JUEGO o usas «Verificar integridad», Amantes vuelve al inglés: pulsa «Instalar» otra vez.
«Quitar traducción» deja todo como estaba (renombra data5.dat y restaura data4.cn.dat).

STEAM DECK (Acta est Fabula)
Steam abre malie.exe, no malie_fabula.exe. Lo que funcionó:
1. Copia la carpeta del juego (ya traducida) a /home/deck/Games/ACTA.
2. En esa copia cambia en malie.ini la línea TITLE= por:  TITLE=Dies irae ~Amantes amentes~
   (con «~» normales; las japonesas se leen distinto en la Deck).
3. Agrega malie_fabula.exe como juego que no es de Steam: Iniciar en = la carpeta, Compatibilidad = Proton.
4. Juégalo una vez (se cierra) para que la Deck cree su carpeta en compatdata/<número>.
5. Copia tu partida de Amantes (carpeta de light dentro de compatdata/644540/pfx/drive_c/users/steamuser/AppData/Roaming/light/)
   a compatdata/<número>/pfx/drive_c/users/steamuser/AppData/Roaming/light/ con el nombre «Dies irae ~Amantes amentes~».
   Dentro debe quedar save/global.dat.
6. Jugar.

Kit sin numpy (Linux): funciona, pero el cifrado puede tardar 10-30 minutos.
"""

def main():
    App().mainloop()

if __name__ == '__main__':
    main()
