# Cómo editar los textos del boletín

Hay dos archivos casi iguales:

- `boletin_editable.html`: es para **trabajar**. Tiene un botón «✎ Editar textos» abajo a la derecha.
- `boletin_interactivo.html`: es la versión **limpia** (sin botón). Es la que se publica.

## Paso a paso
1. Abre `boletin_editable.html` en el navegador (Chrome o Safari, no desde la vista previa del chat).
2. Pulsa **✎ Editar textos**. Los textos que se pueden cambiar quedan con borde naranja.
3. Haz clic en un texto y escribe. Negrita: Ctrl+B (o Cmd+B). Se guarda solo, en ese navegador, y se conserva si recargas.
4. Cuando termines una ronda, pulsa **Descargar mis ediciones**. Se baja un archivo `ediciones.json`.
5. Envíame ese archivo (o guárdalo en `datos/ediciones.json` del repositorio). Yo lo integro y regenero las dos versiones con `node gen_web.js`; así tus cambios quedan en los archivos del proyecto.

## Qué se puede editar
Títulos de capítulo, bajadas, frases de apertura, párrafos, títulos y notas de los gráficos fijos, y las tarjetas con cifras (el texto, no el número grande).

## Qué todavía no
- Los títulos de gráficos que cambian al pulsar un botón (por ejemplo, en continuidad, consumo y oportunidades).
- Las etiquetas dentro de los gráficos y el video.
Esos los cambio yo cuando me los indiques.

## Reglas para no romper nada
- Cambia la redacción, pero revisa que las cifras sigan siendo las del registro.
- Si borras toda la edición de un texto, escribe algo antes de salir de él.
- «Restaurar originales» borra tus ediciones guardadas en el navegador.
