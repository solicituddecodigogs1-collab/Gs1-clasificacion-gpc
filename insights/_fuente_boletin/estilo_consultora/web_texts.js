
// ---------- textos editables: cada texto fijo recibe una clave estable (capítulo/parte) ----------
(function () {
  const $ = (s, r) => (r || document).querySelector(s), $$ = (s, r) => [...(r || document).querySelectorAll(s)];
  const map = {}, orig = {};
  $$('section.chap').forEach((sec) => {
    const id = sec.id, add = (k, el) => { if (el) map[id + '/' + k] = el; };
    add('titulo', $('h2', sec)); add('bajada', $('.deck', sec)); add('gancho', $('.hook', sec));
    $$('.prose .cols p', sec).forEach((e, i) => add('texto-' + (i + 1), e));
    $$('.ex .ext:not([id])', sec).forEach((e, i) => add('grafico-' + (i + 1) + '-titulo', e));
    $$('.ex .exs:not([id])', sec).forEach((e, i) => add('grafico-' + (i + 1) + '-nota', e));
    $$('.card span', sec).forEach((e, i) => add('tarjeta-' + (i + 1), e));
  });
  Object.keys(map).forEach((k) => { orig[k] = map[k].innerHTML; });
  const clean = (h) => h.replace(/<(?!\/?(b|i|em|strong|br)\b)[^>]*>/gi, '').replace(/&nbsp;/g, ' ').trim();
  const apply = (E) => { Object.keys(E || {}).forEach((k) => { if (map[k]) map[k].innerHTML = clean(E[k]); }); };
  apply(typeof EDITS === 'undefined' ? {} : EDITS);
  window.GS1TXT = { map, orig, clean, apply };
})();
