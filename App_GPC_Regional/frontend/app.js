const API = "/api";

const state = {
  codigo: null,
  apiKey: null,
  paises: [],
  paisElegido: null,
  columnas: [],
};

const PASOS_ORDEN = [
  "inicio", "pais", "apikey", "subir", "mapear", "estimar",
  "esperar-haiku", "procesar-haiku", "rescate", "esperar-sonnet",
  "procesar-sonnet", "final",
];

function $(id) { return document.getElementById(id); }

function mostrarPaso(id) {
  document.querySelectorAll(".paso").forEach((s) => s.classList.add("oculto"));
  $(`paso-${id}`).classList.remove("oculto");
  const idx = PASOS_ORDEN.indexOf(id);
  $("progreso-barra").style.width = `${(idx / (PASOS_ORDEN.length - 1)) * 100}%`;
  window.scrollTo({ top: 0, behavior: "smooth" });
}

function toast(msg, esError = false) {
  const t = $("toast");
  t.textContent = msg;
  t.classList.toggle("error", esError);
  t.classList.remove("oculto");
  setTimeout(() => t.classList.add("oculto"), 4000);
}

function mostrarChipProyecto() {
  const chip = $("chip-proyecto");
  chip.textContent = `Proyecto ${state.codigo}`;
  chip.classList.remove("chip-hidden");
}

async function api(path, opciones = {}) {
  const headers = { "Content-Type": "application/json", ...(opciones.headers || {}) };
  if (state.apiKey && !headers["X-Api-Key"]) headers["X-Api-Key"] = state.apiKey;
  const resp = await fetch(`${API}${path}`, { ...opciones, headers });
  if (!resp.ok) {
    const detalle = await resp.json().catch(() => ({ detail: resp.statusText }));
    throw new Error(detalle.detail || "Error de red");
  }
  return resp.json();
}

// ------------------------------------------------------------------ init
async function cargarPaises() {
  state.paises = await api("/paises");
  const grid = $("grid-paises");
  grid.innerHTML = "";
  state.paises.forEach((p) => {
    const div = document.createElement("div");
    div.className = "pais-tarjeta";
    div.textContent = p.nombre;
    div.onclick = () => elegirPais(p, div);
    grid.appendChild(div);
  });
}

function elegirPais(p, el) {
  document.querySelectorAll(".pais-tarjeta").forEach((e) => e.classList.remove("activo"));
  el.classList.add("activo");
  state.paisElegido = p;
  $("tarjeta-pais-detalle").style.display = "block";
  $("info-pais-nombre").textContent = p.nombre;
  $("info-pais-prefijo").textContent = `Prefijo GS1: ${p.prefijo_gs1}${p.prefijo_verificado ? "" : " (revisar)"}`;
  $("info-pais-fiscal").textContent = `ID fiscal: ${p.id_fiscal}`;
}

// --------------------------------------------------------------- flujo
$("btn-crear-proyecto").onclick = async () => {
  const { codigo } = await api("/proyectos", { method: "POST" });
  state.codigo = codigo;
  localStorage.setItem("gpc_codigo", codigo);
  mostrarChipProyecto();
  await cargarPaises();
  mostrarPaso("pais");
};

$("btn-continuar-proyecto").onclick = async () => {
  const codigo = $("input-codigo-continuar").value.trim().toUpperCase();
  if (!codigo) return toast("Ingresa un código de proyecto.", true);
  try {
    const estado = await api(`/proyectos/${codigo}`);
    state.codigo = codigo;
    localStorage.setItem("gpc_codigo", codigo);
    mostrarChipProyecto();
    await retomar(estado);
  } catch (e) {
    toast("No se encontró ese proyecto.", true);
  }
};

async function retomar(estado) {
  if (estado.columnas) state.columnas = estado.columnas;
  await cargarPaises();
  const mapaPasos = {
    subir: "apikey", // siempre repedir la key al volver (nunca se guarda)
    mapear: "apikey",
    estimar: "apikey",
    esperar_haiku: "esperar-haiku",
    ofrecer_rescate: "rescate",
    esperar_sonnet: "esperar-sonnet",
    final: "final",
  };
  if (estado.paso === "final") {
    await mostrarResumenFinal();
    return mostrarPaso("final");
  }
  toast("Vuelve a ingresar tu API key para continuar.");
  mostrarPaso("apikey");
  // guarda a dónde ir después de la key
  state.destinoTrasKey = mapaPasos[estado.paso] || "subir";
  state.estadoResumido = estado;
}

// --------------------------------------------------------------- país
$("btn-guardar-pais").onclick = async () => {
  if (!state.paisElegido) return toast("Elige un país primero.", true);
  await api(`/proyectos/${state.codigo}/pais`, {
    method: "POST",
    body: JSON.stringify({ pais: state.paisElegido.nombre, notas_jerga: $("input-jerga").value }),
  });
  mostrarPaso("apikey");
};

// --------------------------------------------------------------- apikey
$("btn-guardar-apikey").onclick = () => {
  const key = $("input-apikey").value.trim();
  if (!key) return toast("Pega tu API key.", true);
  state.apiKey = key;
  if (state.destinoTrasKey) {
    const destino = state.destinoTrasKey;
    state.destinoTrasKey = null;
    if (destino === "subir" && state.columnas.length) {
      llenarSelectsMapeo();
      return mostrarPaso("mapear");
    }
    return mostrarPaso(destino);
  }
  mostrarPaso("subir");
};

// --------------------------------------------------------------- subir
const inputArchivo = $("input-archivo");
const zonaDrop = $("zona-drop");
inputArchivo.onchange = () => subirArchivo(inputArchivo.files[0]);
zonaDrop.ondragover = (e) => { e.preventDefault(); zonaDrop.classList.add("arrastrando"); };
zonaDrop.ondragleave = () => zonaDrop.classList.remove("arrastrando");
zonaDrop.ondrop = (e) => {
  e.preventDefault();
  zonaDrop.classList.remove("arrastrando");
  if (e.dataTransfer.files.length) subirArchivo(e.dataTransfer.files[0]);
};

async function subirArchivo(archivo) {
  if (!archivo) return;
  $("nombre-archivo").textContent = `Subiendo ${archivo.name}...`;
  const formData = new FormData();
  formData.append("archivo", archivo);
  const resp = await fetch(`${API}/proyectos/${state.codigo}/catalogo`, { method: "POST", body: formData });
  if (!resp.ok) {
    $("nombre-archivo").textContent = "";
    return toast("No se pudo leer el archivo.", true);
  }
  const data = await resp.json();
  state.columnas = data.columnas;
  state.preview = data.preview;
  $("nombre-archivo").textContent = `${archivo.name} — ${data.n_filas} filas`;
  llenarSelectsMapeo();
  renderTablaPreview();
  $("info-filas").textContent = `${data.n_filas} filas, ${data.columnas.length} columnas.`;
  mostrarPaso("mapear");
}

function llenarSelectsMapeo() {
  ["select-marca", "select-descripcion", "select-identificador"].forEach((id, i) => {
    const sel = $(id);
    sel.innerHTML = "";
    state.columnas.forEach((c, j) => {
      const opt = document.createElement("option");
      opt.value = c;
      opt.textContent = c;
      if (j === i) opt.selected = true;
      sel.appendChild(opt);
    });
  });
}

function renderTablaPreview() {
  if (!state.preview) return;
  const tabla = $("tabla-preview");
  const cols = state.columnas;
  let html = "<tr>" + cols.map((c) => `<th>${c}</th>`).join("") + "</tr>";
  state.preview.forEach((fila) => {
    html += "<tr>" + cols.map((c) => `<td>${fila[c] ?? ""}</td>`).join("") + "</tr>";
  });
  tabla.innerHTML = html;
}

// --------------------------------------------------------------- mapeo
$("btn-guardar-mapeo").onclick = async () => {
  const body = {
    marca: $("select-marca").value,
    descripcion: $("select-descripcion").value,
    identificador: $("select-identificador").value,
  };
  const est = await api(`/proyectos/${state.codigo}/mapeo`, { method: "POST", body: JSON.stringify(body) });
  $("stat-total").textContent = est.n_total.toLocaleString();
  $("stat-unicos").textContent = est.n_unicos.toLocaleString();
  $("stat-costo").textContent = `$${est.costo_estimado_usd}`;
  mostrarPaso("estimar");
};

// --------------------------------------------------------------- haiku
$("btn-enviar-haiku").onclick = async () => {
  $("btn-enviar-haiku").disabled = true;
  try {
    await api(`/proyectos/${state.codigo}/batch/haiku`, { method: "POST" });
    mostrarPaso("esperar-haiku");
  } catch (e) {
    toast(e.message, true);
  } finally {
    $("btn-enviar-haiku").disabled = false;
  }
};

$("btn-verificar-haiku").onclick = async () => {
  const r = await api(`/proyectos/${state.codigo}/batch/haiku/estado`);
  $("texto-estado-haiku").textContent = r.status;
  if (r.status === "ended") mostrarPaso("procesar-haiku");
  else toast(`Estado actual: ${r.status}`);
};

$("btn-procesar-haiku").onclick = async () => {
  const estado = await api(`/proyectos/${state.codigo}/batch/haiku/procesar`, { method: "POST" });
  if (estado.paso === "final") {
    await mostrarResumenFinal();
    return mostrarPaso("final");
  }
  $("stat-nomatch").textContent = estado.n_nomatch_haiku.toLocaleString();
  $("stat-costo-sonnet").textContent = `$${estado.estimacion_sonnet.costo_estimado_usd}`;
  mostrarPaso("rescate");
};

// -------------------------------------------------------------- rescate
$("btn-saltar-rescate").onclick = async () => {
  await api(`/proyectos/${state.codigo}/saltar_rescate`, { method: "POST" });
  await mostrarResumenFinal();
  mostrarPaso("final");
};

$("btn-enviar-sonnet").onclick = async () => {
  $("btn-enviar-sonnet").disabled = true;
  try {
    await api(`/proyectos/${state.codigo}/batch/sonnet`, { method: "POST" });
    mostrarPaso("esperar-sonnet");
  } catch (e) {
    toast(e.message, true);
  } finally {
    $("btn-enviar-sonnet").disabled = false;
  }
};

$("btn-verificar-sonnet").onclick = async () => {
  const r = await api(`/proyectos/${state.codigo}/batch/sonnet/estado`);
  $("texto-estado-sonnet").textContent = r.status;
  if (r.status === "ended") mostrarPaso("procesar-sonnet");
  else toast(`Estado actual: ${r.status}`);
};

$("btn-procesar-sonnet").onclick = async () => {
  await api(`/proyectos/${state.codigo}/batch/sonnet/procesar`, { method: "POST" });
  await mostrarResumenFinal();
  mostrarPaso("final");
};

// ----------------------------------------------------------------- final
async function mostrarResumenFinal() {
  const r = await api(`/proyectos/${state.codigo}/resumen`);
  $("final-total").textContent = r.total.toLocaleString();
  $("final-asignados").textContent = r.asignados.toLocaleString();
  $("final-nomatch").textContent = r.no_match.toLocaleString();
  ["completo", "asignados", "nomatch"].forEach((tipo) => {
    $(`descargar-${tipo}`).href = `${API}/proyectos/${state.codigo}/descargar/${tipo}`;
  });
}

$("btn-nuevo-proyecto").onclick = () => {
  localStorage.removeItem("gpc_codigo");
  location.reload();
};

// ------------------------------------------------------------------ boot
(async function init() {
  await cargarPaises();
})();
