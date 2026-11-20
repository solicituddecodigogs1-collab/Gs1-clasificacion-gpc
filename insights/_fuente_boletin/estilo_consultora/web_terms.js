  // ---------- términos con explicación (se subrayan con puntos y se explican al pasar el cursor) ----------
  const TERMS = __TERMS__;
  (function () {
    const keys = Object.keys(TERMS).sort((a, b) => b.length - a.length);
    const esc = (s) => s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    const re = new RegExp('(' + keys.map(esc).join('|') + ')', 'i');
    const safe = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
    $$('section.chap').forEach((sec) => {
      const used = {};
      $$('.deck, .prose p, .simple p', sec).forEach((el) => {
        const w = document.createTreeWalker(el, NodeFilter.SHOW_TEXT), nodes = [];
        while (w.nextNode()) nodes.push(w.currentNode);
        nodes.forEach((n) => {
          let txt = n.nodeValue, html = '', changed = false, m;
          while ((m = re.exec(txt))) {
            const k = keys.find((x) => x.toLowerCase() === m[1].toLowerCase());
            const cut = m.index + m[1].length;
            if (used[k]) { html += safe(txt.slice(0, cut)); txt = txt.slice(cut); continue; }
            used[k] = 1; changed = true;
            html += safe(txt.slice(0, m.index)) + '<span class="t" data-k="' + k + '">' + safe(m[1]) + '</span>';
            txt = txt.slice(cut);
          }
          if (changed) { html += safe(txt); const s = document.createElement('span'); s.innerHTML = html; n.replaceWith(...s.childNodes); }
        });
      });
    });
    $$('.t').forEach((e) => {
      const h = () => '<b>' + e.textContent + '</b><br>' + TERMS[e.dataset.k];
      e.onmousemove = (ev) => showTip(ev, h());
      e.onmouseleave = hideTip;
      e.onclick = (ev) => { const r = e.getBoundingClientRect(); showTip({ clientX: r.left, clientY: r.bottom }, h()); setTimeout(hideTip, 3500); };
    });
  })();
