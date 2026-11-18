# Versión «estilo consultora» del boletín

Rediseño de las 14 láminas con una idea por lámina, títulos que dicen la conclusión, gráficos grandes y recuadro de ideas clave.

- `boletin_estilo_consultora.html`: archivo autocontenido (tipografías y logo incrustados). Se abre en cualquier navegador y se imprime a PDF (A4, sin márgenes).
- `gen.js`: generador. `node gen.js` reescribe el HTML a partir de `datos/` (tablas ya calculadas, sin nombres de empresa).
- No sustituye al PDF principal; es una propuesta de formato para comparar.
