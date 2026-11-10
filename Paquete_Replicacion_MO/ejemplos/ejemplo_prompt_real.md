# Ejemplo real de prompt y respuesta

Este es un caso real, tomado tal cual del catálogo 2025 de GS1 Venezuela, mostrando
exactamente lo que el modelo recibe y responde.

## System prompt (fijo, igual para todas las solicitudes)

```
Eres un clasificador de productos bajo el estándar Global Product Classification (GPC) de GS1.

Reglas estrictas:
1. Identidad física únicamente (Regla 1 del GPC): clasifica lo que el producto ES, nunca su uso previsto, canal de venta, promoción o empaque.
2. Cada mensaje trae una lista de CANDIDATOS (códigos Brick/Class/Family/Segment ya preseleccionados del catálogo oficial GPC) seguida de "Marca: ... | Descripción: ...".
3. gpc_code debe ser copiado EXACTAMENTE (8 dígitos) de la lista de candidatos recibida. Tienes PROHIBIDO inventar, truncar, combinar o construir un código que no esté literalmente en esa lista.
4. Escalamiento inverso: si el Brick candidato más específico aplica, úsalo. Si ningún Brick candidato encaja pero sí una Class/Family/Segment candidata, sube a ese nivel. Si NINGÚN candidato de la lista corresponde razonablemente al producto, responde exactamente "NO_MATCH".
5. confidence_score es un entero de 0 a 100 con tu nivel de confianza.

Responde ÚNICAMENTE con este JSON, sin texto adicional:
{"gpc_code": "<código de 8 dígitos tomado de la lista, o NO_MATCH>", "confidence_score": <entero 0-100>}
```

## Producto de ejemplo

- **Marca:** LA GRAN PASTORA
- **Descripción:** YOGURT NATURAL TIPO GRIEGO 500 G. 500 G

## Mensaje de usuario que recibe el modelo (candidatos + producto)

El preclasificador local seleccionó 63 candidatos (25 Bricks más sus padres Class/Family/
Segment desduplicados) por búsqueda léxica, sin llamar a ninguna API. Fragmento relevante:

```
CANDIDATOS:
10000277: Yogur (congelados) [Brick]
10000278: Yogur (perecedero) [Brick]
10000279: Yogur (no necesitan refrigeración) [Brick]
...
50132100: Yogur/sustitutos del yogurt [Class]
...
50130000: Leche/mantequilla/nata/yogures/queso/huevos/sustitutos [Family]
...
50000000: Alimentos/Bebidas [Segment]
...
(63 candidatos en total — ver el archivo completo en este mismo directorio:
 ejemplo_candidatos_completo.txt)

Marca: LA GRAN PASTORA | Descripción: YOGURT NATURAL TIPO GRIEGO 500 G. 500 G
```

## Respuesta real del modelo

```json
{"gpc_code": "50132100", "confidence_score": 92}
```

`50132100` = "Yogur/sustitutos del yogurt" [Class] — el modelo subió de Brick a Class porque
ningún Brick candidato distinguía correctamente "yogur tipo griego" de las demás variantes de
yogur listadas, pero la Class sí aplica con alta confianza. Esto es exactamente el
"escalamiento inverso" descrito en la regla 4 del system prompt.

## Cómo se ve la fila final, ya fusionada

| Campo | Antes (solo datos de catálogo) | Después (fusionado con la respuesta del modelo) |
|---|---|---|
| MARCA | LA GRAN PASTORA | LA GRAN PASTORA |
| DESCRIPCION | YOGURT NATURAL TIPO GRIEGO 500 G. 500 G | YOGURT NATURAL TIPO GRIEGO 500 G. 500 G |
| gpc_code | *(vacío)* | 50132100 |
| nivel_asignado | *(vacío)* | Class |
| gpc_description | *(vacío)* | Yogur/sustitutos del yogurt |
| confidence_score | *(vacío)* | 92 |
