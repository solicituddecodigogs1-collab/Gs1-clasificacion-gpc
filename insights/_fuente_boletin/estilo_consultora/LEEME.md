# Versión «estilo consultora» del boletín

Rediseño de las 14 láminas con una idea por lámina, títulos que dicen la conclusión, gráficos grandes y recuadro de ideas clave.

- `boletin_estilo_consultora.html`: archivo autocontenido (tipografías y logo incrustados). Se abre en cualquier navegador y se imprime a PDF (A4, sin márgenes).
- `gen.js`: generador. `node gen.js` reescribe el HTML a partir de `datos/` (tablas ya calculadas, sin nombres de empresa).
- No sustituye al PDF principal; es una propuesta de formato para comparar.

## Versión web interactiva

- `boletin_interactivo.html`: experiencia web autocontenida (video, gráficos con cursor, filtros, carrera de sectores, eslabones). Se abre en cualquier navegador sin conexión.
- `gen_web.js`, `web.css`, `web_client.js`: fuente de la página. `node gen_web.js` la regenera.
- `video/make_film.js`: genera `treinta_anos_en_codigos.mp4` (animación de datos, requiere Playwright y ffmpeg).

## Video en la página
La «película» se dibuja en vivo sobre un lienzo (`web_film.js`) para que funcione en cualquier navegador, incluidos los visores integrados de los teléfonos. El MP4 (`video/treinta_anos_en_codigos.mp4`) queda como archivo aparte para compartirlo por chat. La página pasó de 3,7 MB a 0,4 MB.
