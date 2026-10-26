# Dies irae — Traducción al español

Traducción no oficial al español de **Dies irae ~Amantes amentes~** (Steam), de **Dies irae ~Acta est Fabula~**
(el parche R18 oficial para la versión de Steam) y de **Dies irae ~Interview with Kaziklu Bey~** (Steam).
Hecha por fans; no tiene relación con light ni con JAST.

- Guion completo de las dos versiones, decisiones y nombres de la caja de nombre en español.
- Interview with Kaziklu Bey: guion completo y glosario del menú en español.
- La interfaz (menús, configuración) se queda en inglés.
- El kit **no trae archivos ni texto del juego**: necesitas tu copia de Steam. El kit lee tus archivos,
  pone el español encima y guarda respaldo de lo que cambia.

## Instalación (Windows)

1. Descarga `DiesIrae_ES.exe` de la sección **Releases**.
2. Si quieres Acta est Fabula (versión para adultos), copia antes el parche R18 oficial
   (`malie_fabula.exe` y `data4.dat`) dentro de la carpeta del juego.
3. Abre `DiesIrae_ES.exe`, pulsa **Buscar** (o **Examinar…**) para elegir la carpeta del juego y luego **Instalar todo**.
4. En el juego, deja el idioma en **inglés**.

Carpeta del juego: en Steam, clic derecho en Dies irae → **Administrar → Ver archivos locales**.

| Qué | Cómo se abre | Qué archivo cambia el kit |
|---|---|---|
| Amantes amentes | botón **Jugar** de Steam | `data4.cn.dat` (el original queda como `data4.cn.ORIGINAL.dat`) |
| Acta est Fabula | `malie_fabula.exe` | agrega `data5.dat` (no toca nada más) |

| Interview with Kaziklu Bey | botón **Jugar** de Steam | agrega `data2.dat` (no toca nada más) |

Para **Kaziklu Bey** (es otro juego de Steam): pulsa **Buscar Kaziklu Bey** (o **Examinar…** y elige su carpeta)
y luego **Instalar todo**. El glosario se abre desde el menú del juego (clic derecho o Esc).

Acta est Fabula exige tener **al menos una ruta terminada en Amantes amentes** (lo comprueba el propio juego).

**Quitar traducción** deja todo como estaba. Si Steam actualiza el juego o usas «Verificar integridad de archivos»,
Amantes vuelve al inglés: pulsa **Instalar** otra vez.

## Con Python (Windows, Linux, Steam Deck)

```
python kit/di_kit.py                         # abre la ventana
python kit/di_kit.py instalar "CARPETA"      # en consola
python kit/di_kit.py quitar   "CARPETA"
```
`numpy` es opcional (sin él, el cifrado tarda mucho más). En la Steam Deck: `./abrir_kit.sh`.

## Steam Deck

Amantes y Kaziklu Bey funcionan normal (para Kaziklu Bey basta con copiar el `data2.dat` instalado a la carpeta del
juego en la Deck, o usar el kit desde la Deck). Para Acta est Fabula hay que usar una carpeta aparte y un acceso «que no es de Steam»;
los pasos están en [docs/STEAM_DECK.md](docs/STEAM_DECK.md).

## Corregir la traducción

La pestaña **Editar traducción** muestra el español y, si quieres, el inglés de tu propio juego para comparar.
Los cambios se guardan en una carpeta `datos` junto al kit; después vuelve a pulsar **Instalar**.
Los textos están en `kit/datos/` (`acta_es.tsv`, `amantes_es.tsv`, `opciones_nombres.tsv`, `kb_es.tsv`, `kb_glos_es.tsv`). Respeta las marcas
`{end}`, `{v:…}{/v}`, `{u000A}`…: el kit no mete los mensajes cuyas marcas no coincidan con el original.

## Comunidad

Discord del grupo: https://discord.gg/NV8TbQQ7B

## Licencia

Código: MIT. Traducción: CC BY-NC-SA 4.0 (uso no comercial, citando al grupo). Dies irae es propiedad de sus autores;
compra el juego.
