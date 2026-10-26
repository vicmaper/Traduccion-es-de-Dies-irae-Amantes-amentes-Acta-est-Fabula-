# Acta est Fabula en la Steam Deck

Steam abre siempre `malie.exe` (Amantes). Además, `malie_fabula.exe` busca la partida de Amantes con un nombre
de carpeta que lleva «～» japonesas, y en Proton se leen distinto. Lo que funcionó:

1. En la PC instala el español en la carpeta del juego con el kit. Copia **toda** la carpeta a la Deck,
   por ejemplo a `/home/deck/Games/ACTA`.
2. En esa copia abre `malie.ini` y cambia la línea `TITLE=` por:
   ```
   TITLE=Dies irae ~Amantes amentes~
   ```
   (con «~» normales). Guarda.
3. En Steam (modo escritorio): **Juegos → Agregar un juego que no es de Steam** → `malie_fabula.exe`.
   En sus propiedades: **Iniciar en** = `"/home/deck/Games/ACTA/"`, **Compatibilidad** = Proton, opciones de lanzamiento vacías.
4. Pulsa **Jugar** una vez (se cerrará): así la Deck crea su carpeta `compatdata/<número>`.
   El número aparece en el registro si usas `PROTON_LOG=1 %command%`, o busca la carpeta más reciente en
   `/home/deck/.local/share/Steam/steamapps/compatdata/`.
5. Copia tu partida de Amantes: la carpeta que está en
   `compatdata/644540/pfx/drive_c/users/steamuser/AppData/Roaming/light/` (nombre parecido a «Dies irae …Amantes amentes…»)
   pégala en `compatdata/<número>/pfx/drive_c/users/steamuser/AppData/Roaming/light/` y renómbrala a
   `Dies irae ~Amantes amentes~`. Dentro debe quedar `save/global.dat`.
6. Pulsa **Jugar**.

Para ver carpetas ocultas en Dolphin: **Ctrl + H**. Para escribir una ruta: **Ctrl + L**.

# Interview with Kaziklu Bey en la Steam Deck

No hace falta nada especial: el español va en un archivo nuevo, `data2.dat`.
1. Instálalo con el kit en la PC (o en la Deck, modo escritorio, con `./abrir_kit.sh`).
2. Si lo instalaste en la PC, copia `data2.dat` a la carpeta del juego en la Deck
   (`/home/deck/.local/share/Steam/steamapps/common/<carpeta de Kaziklu Bey>/`).
3. Juega con el botón **Jugar** de Steam. Para volver al inglés, borra o renombra `data2.dat`.
