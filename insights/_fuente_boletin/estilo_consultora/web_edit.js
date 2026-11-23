
// ---------- modo edición (solo en boletin_editable.html) ----------
(function () {
  const T = window.GS1TXT; if (!T) return;
  const LS = 'gs1_ediciones_v1';
  const get = () => { try { return JSON.parse(localStorage.getItem(LS) || '{}'); } catch (e) { return {}; } };
  const diff = () => { const d = {}; Object.keys(T.map).forEach((k) => { const cur = T.clean(T.map[k].innerHTML); if (cur !== T.clean(T.orig[k])) d[k] = cur; }); return d; };
  const save = () => { try { localStorage.setItem(LS, JSON.stringify(diff())); } catch (e) {} count(); };
  T.apply(get());
  const st = document.createElement('style');
  st.textContent = '#edbar{position:fixed;right:16px;bottom:16px;z-index:200;background:#002C6C;color:#fff;border-radius:6px;box-shadow:0 6px 24px rgba(0,0,0,.3);font:600 13px Barlow,sans-serif;max-width:310px}#edbar button{font:600 13px Barlow,sans-serif;cursor:pointer;border:0;padding:9px 12px;margin:4px;border-radius:4px}#edbar .main{background:#F26334;color:#fff;margin:8px}#edbar .row{display:none;padding:0 6px 10px}#edbar.on .row{display:block}#edbar .row p{margin:2px 10px 8px;font-weight:400;font-size:12.5px;line-height:1.4;color:#C6D2EE}#edbar .row button{background:#fff;color:#002C6C}body.editing [data-edk]{outline:2px dashed #F26334;outline-offset:3px;cursor:text;background:rgba(242,99,52,.06)}body.editing [data-edk]:focus{outline:2px solid #F26334;background:rgba(242,99,52,.12)}body.editing .rv{opacity:1!important;transform:none!important}';
  document.head.appendChild(st);
  const bar = document.createElement('div'); bar.id = 'edbar';
  bar.innerHTML = '<button class="main" id="edtog">✎ Editar textos</button><div class="row"><p>Haz clic en cualquier texto con borde naranja y escribe. Se guarda solo en este navegador. Negrita: Ctrl+B.</p><button id="eddl">Descargar mis ediciones</button><button id="edrs">Restaurar originales</button><p id="edcnt"></p></div>';
  document.body.appendChild(bar);
  const count = () => { const n = Object.keys(diff()).length; document.getElementById('edcnt').textContent = n ? n + ' texto(s) modificado(s)' : 'Sin cambios todavía'; };
  Object.keys(T.map).forEach((k) => { T.map[k].setAttribute('data-edk', k); });
  const setEdit = (on) => {
    document.body.classList.toggle('editing', on); bar.classList.toggle('on', on);
    document.getElementById('edtog').textContent = on ? '✓ Terminar de editar' : '✎ Editar textos';
    Object.keys(T.map).forEach((k) => { const el = T.map[k]; if (on) { el.setAttribute('contenteditable', 'true'); el.setAttribute('spellcheck', 'true'); } else el.removeAttribute('contenteditable'); });
    count();
  };
  document.getElementById('edtog').onclick = () => setEdit(!document.body.classList.contains('editing'));
  document.addEventListener('input', (e) => { if (e.target && e.target.hasAttribute && e.target.hasAttribute('data-edk')) save(); });
  document.addEventListener('paste', (e) => { if (e.target && e.target.hasAttribute && e.target.hasAttribute('data-edk')) { e.preventDefault(); document.execCommand('insertText', false, (e.clipboardData || window.clipboardData).getData('text')); } });
  document.addEventListener('click', (e) => { if (document.body.classList.contains('editing') && e.target.closest && e.target.closest('[data-edk]')) e.stopPropagation(); }, true);
  document.getElementById('eddl').onclick = () => {
    const d = diff(), blob = new Blob([JSON.stringify(d, null, 2)], { type: 'application/json' }), a = document.createElement('a');
    a.href = URL.createObjectURL(blob); a.download = 'ediciones.json'; document.body.appendChild(a); a.click(); a.remove();
  };
  document.getElementById('edrs').onclick = () => { if (confirm('¿Borrar todas tus ediciones y volver a los textos originales?')) { try { localStorage.removeItem(LS); } catch (e) {} location.reload(); } };
  count();
})();
