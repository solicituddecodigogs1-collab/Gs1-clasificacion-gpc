# Fuente del boletín

`boletin.html` es la fuente editable del boletín (14 páginas, una `<section class="page">` por lámina), con tipografías Barlow, imágenes y logo en esta carpeta, todo con rutas relativas.

Para regenerar el PDF:

```bash
cd insights/_fuente_boletin
node render.js            # escribe ../Boletin_insights_GS1_edicion_revista.pdf
```

Requiere Node con Playwright y Chromium. Para cambiar un texto, editar `boletin.html` y volver a ejecutar el comando. Si cambia el número de láminas, actualizar a mano el índice de la carta del editor (página 2) y los pies de página («n / 14»).
