(() => {
  const D = window.APP_DATA;
  const $ = (s) => document.querySelector(s);
  const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const readerIndex = new Map(D.reader.map((d, i) => [d.pid, i]));

  /* ---------- hero stats ---------- */
  const o = D.overview;
  $("#stats").innerHTML = [
    ["文書", o.n_docs, "件"],
    ["圖像", o.n_pages, "頁"],
    ["年代", `${o.year_min}–${String(o.year_max).slice(2)}`, ""],
    ["有官印", Math.round(o.gov_share * 100), "%"],
  ].map(([k, v, u]) => `<div><dt>${k}</dt><dd>${v}<small>${u}</small></dd></div>`).join("");

  /* ---------- findings: period seal shares, same-surname share ---------- */
  const shareOf = (p) => {
    const n = (p.Government || 0) + (p.Personal || 0) + (p.Other || 0);
    return n ? Math.round(((p.Government || 0) / n) * 100) : 0;
  };
  const periodMap = Object.fromEntries(o.by_period.map((p) => [p.period, p]));
  document.querySelectorAll("[data-share]").forEach((el) => {
    const p = periodMap[el.dataset.share];
    if (p) el.textContent = shareOf(p) + "%";
  });
  const ss = o.same_surname;
  $("#same-share").textContent = `${Math.round((ss.same / ss.pairs) * 100)}%（${ss.same}／${ss.pairs} 件）`;
  $("#seal-trend").innerHTML = o.by_period.filter((p) => p.period !== "明").map((p) => {
    const n = (p.Government || 0) + (p.Personal || 0) + (p.Other || 0);
    return `<div class="col"><div class="stack"><div class="fill" style="height:${shareOf(p)}%">${shareOf(p)}%</div></div><div class="lab">${p.period}</div><div class="n">${n} 件</div></div>`;
  }).join("") + `<div class="col"><div class="stack" style="background:none"></div><div class="lab" style="font-size:12px;color:var(--ink-3)">有官印比例</div><div class="n">明代僅 1 件</div></div>`;

  /* ---------- quarter-century chart (vanilla SVG) ---------- */
  (function quarterChart() {
    const have = new Map(o.by_quarter_century.map((r) => [r.start, r]));
    const starts = [...have.keys()];
    const rows = [];
    for (let s = Math.min(...starts); s <= Math.max(...starts); s += 25) rows.push(have.get(s) || { start: s });
    const W = 1000, H = 300, padL = 34, padB = 46, padT = 16;
    const max = Math.max(...rows.map((r) => (r.Government || 0) + (r.Personal || 0) + (r.Other || 0)));
    const step = (W - padL) / rows.length, bw = step * 0.62;
    const y = (v) => (H - padB - padT) * (v / max);
    let g = "";
    for (let t = 0; t <= max; t += 20) {
      const yy = H - padB - y(t);
      g += `<line x1="${padL}" x2="${W}" y1="${yy}" y2="${yy}" stroke="rgba(29,24,19,.12)"/><text x="${padL - 8}" y="${yy + 4}" font-size="12" text-anchor="end">${t}</text>`;
    }
    rows.forEach((r, i) => {
      const x = padL + i * step + (step - bw) / 2;
      let base = H - padB;
      [["Government", "#b02e26"], ["Personal", "#4a4036"], ["Other", "#2e4a5c"]].forEach(([k, c]) => {
        const v = r[k] || 0; if (!v) return;
        const h = y(v); base -= h;
        g += `<rect x="${x}" y="${base}" width="${bw}" height="${h}" fill="${c}"><title>${r.start}–${r.start + 24}：${k === "Government" ? "有官印" : k === "Personal" ? "無官印" : "其他"} ${v} 件</title></rect>`;
      });
      const total = (r.Government || 0) + (r.Personal || 0) + (r.Other || 0);
      if (total) g += `<text x="${x + bw / 2}" y="${base - 6}" font-size="12" text-anchor="middle">${total}</text>`;
      if (i % 2 === 0 || rows.length < 12) g += `<text x="${x + bw / 2}" y="${H - padB + 20}" font-size="13" text-anchor="middle">${r.start}</text>`;
    });
    const events = [[1644, "清"], [1912, "民國"], [1949, "1949"]];
    const x0 = rows[0].start;
    events.forEach(([yr, lab]) => {
      const xx = padL + ((yr - x0) / 25) * step;
      const nearEnd = xx > W - 60;
      g += `<line x1="${xx}" x2="${xx}" y1="${padT}" y2="${H - padB + 30}" stroke="#b02e26" stroke-dasharray="3 4"/><text x="${nearEnd ? xx - 5 : xx + 5}" y="${H - padB + 40}" font-size="13" fill="#b02e26" text-anchor="${nearEnd ? "end" : "start"}">${lab}</text>`;
    });
    $("#chart-quarter").innerHTML =
      `<div class="legend"><span><i style="background:#b02e26"></i>有官印</span><span><i style="background:#4a4036"></i>無官印</span><span><i style="background:#2e4a5c"></i>其他</span></div>` +
      `<svg viewBox="0 0 ${W} ${H}" role="img" aria-label="每二十五年文書件數，按有無官印分色">${g}</svg>`;
  })();

  /* ---------- periods & places ---------- */
  $("#periods").innerHTML = o.by_period.map((p) => {
    const g = p.Government || 0, pe = p.Personal || 0, ot = p.Other || 0, n = g + pe + ot;
    const w = (v) => (n ? (v / n) * 100 : 0);
    return `<div class="period"><b>${p.period}</b><div class="bar" title="有官印 ${g}／無官印 ${pe}${ot ? "／其他 " + ot : ""}"><span class="g" style="width:${w(g)}%"></span><span class="p" style="width:${w(pe)}%"></span><span class="o" style="width:${w(ot)}%"></span></div><span class="n">${n}</span></div>`;
  }).join("") + `<p class="fine">條長＝該時期內有官印與無官印的比例。明代只有一件（萬曆十二年）。</p>`;
  const pmax = o.places[0][1];
  $("#places").innerHTML = o.places.slice(0, 10).map(([k, v]) =>
    `<div class="place"><span>${esc(k)}</span><div class="bar"><span style="width:${(v / pmax) * 100}%"></span></div><span class="n">${v}</span></div>`).join("");

  /* ---------- genealogy strip ---------- */
  $("#strip").innerHTML = D.genealogy.map((g, i) => `
    <article class="gcard" tabindex="0" data-i="${i}" style="animation:rise .6s ${i * 0.06}s both">
      <div class="era">${g.era}</div>
      <div class="yr">${g.year}</div>
      <figure><img src="${g.img}" alt="${esc(g.kind)}：${esc(g.label)}" loading="lazy"></figure>
      <h3><span class="k">${String(i + 1).padStart(2, "0")}</span> ${esc(g.kind)}</h3>
      <p class="lab">${esc(g.label)}</p>
      <p>${esc(g.note)}</p>
    </article>`).join("");
  $("#strip").addEventListener("click", (e) => { const c = e.target.closest(".gcard"); if (c) openGen(+c.dataset.i); });
  $("#strip").addEventListener("keydown", (e) => { const c = e.target.closest(".gcard"); if (c && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); openGen(+c.dataset.i); } });
  function openGen(i) {
    const g = D.genealogy[i];
    if (readerIndex.has(g.pid)) { openReader(g.pid); return; }
    lightbox(g.img, `${g.year}　${g.kind}・${g.label}`);
  }

  /* ---------- households ---------- */
  const tagFor = (t) => ({ 原文: "tag-stated", 推測: "tag-inferred", 推算: "tag-calc" }[t] || "tag-limit");
  const statusLabel = { done: "已核", partial: "部分", unchecked: "待核", inferred: "推測" };
  function relClass(rel) {
    if (!rel) return "";
    if (/推測|推定/.test(rel)) return "inferred";
    if (/原文/.test(rel) && !/未寫|未写/.test(rel)) return "stated";
    return "";
  }
  function renderHH(k) {
    const h = D.households.find((x) => x.key === k);
    document.querySelectorAll("#hh-tabs button").forEach((b) => b.setAttribute("aria-selected", b.dataset.k === k));
    const pts = h.points.map(([t, s]) => `<li><span class="tag ${tagFor(t)}">${t}</span><span>${esc(s)}</span></li>`).join("");
    const evs = h.events.length ? h.events.map((e) => {
      const rc = relClass(e.relation);
      const who = [e.from, e.to].filter(Boolean).map(esc).join('<span class="arrow">→</span>') || "—";
      const ev = (e.evidence || "").match(/pitt:\d+/g) || [];
      return `<li class="${rc}">
        <div class="d">${esc(e.date)}</div>
        <div class="who">${who}</div>
        <div class="m">${esc(e.mode)}</div>
        <div class="meta">${e.price ? `<span class="price">${esc(e.price)}</span>` : ""}
          ${e.relation ? `<span class="tag ${rc === "stated" ? "tag-stated" : rc === "inferred" ? "tag-inferred" : "tag-limit"}">${esc(e.relation)}</span>` : ""}
          ${ev.map((p) => `<span class="ev" data-pid="${p}">${p.replace("pitt:", "")}</span>`).join(" ")}</div>
      </li>`;
    }).join("") : `<li class="empty">此組只有單一時點，沒有可排的產權事件。</li>`;
    $("#hh-panel").innerHTML = `
      <div class="hh-head">
        <h3>${esc(h.title)}</h3>
        <div class="span">${esc(h.span)}　<span class="tag ${h.status === "done" ? "tag-stated" : h.status === "inferred" ? "tag-inferred" : "tag-limit"}">${statusLabel[h.status] || ""}</span></div>
        <p class="lede">${esc(h.lede)}</p>
        <ul class="points">${pts}</ul>
      </div>
      <ol class="events" aria-label="產權事件時間線">${evs}</ol>`;
    $("#hh-panel").style.animation = "none"; void $("#hh-panel").offsetWidth; $("#hh-panel").style.animation = "";
  }
  $("#hh-tabs").innerHTML = D.households.map((h) =>
    `<button role="tab" data-k="${h.key}">${esc(h.title.replace(/\s+/g, " "))}<span class="st">${statusLabel[h.status] || ""}</span></button>`).join("");
  $("#hh-tabs").addEventListener("click", (e) => { const b = e.target.closest("button"); if (b) renderHH(b.dataset.k); });
  $("#hh-panel").addEventListener("click", (e) => {
    const p = e.target.closest(".ev"); if (!p) return;
    if (readerIndex.has(p.dataset.pid)) openReader(p.dataset.pid);
    else lightbox(`../students_documents_export/images/${p.dataset.pid.replace("pitt:", "")}_001.jpg`, p.dataset.pid);
  });
  renderHH(D.households[0].key);

  /* ---------- Lin Xiuzhi parcels ---------- */
  const mix = {};
  D.parcels.forEach((p) => { mix[p.cls] = (mix[p.cls] || 0) + p.mu; });
  const total = Object.values(mix).reduce((a, b) => a + b, 0);
  const mixColor = { 田: "#b02e26", 農地: "#7a4b2a", 基地: "#4a4036", 蕩地: "#2e4a5c" };
  $("#land-mix").innerHTML = Object.entries(mix).sort((a, b) => b[1] - a[1]).map(([k, v]) =>
    `<div style="flex:${v};background:${mixColor[k] || "#666"}" title="${k} ${v.toFixed(2)} 畝">${v / total > 0.08 ? `${k} ${v.toFixed(2)} 畝` : ""}</div>`).join("") ;
  $("#land-mix").setAttribute("aria-label", "地目構成：" + Object.entries(mix).map(([k, v]) => `${k}${v.toFixed(2)}畝`).join("，"));
  const slots = [...D.parcels].sort((a, b) => a.licence - b.licence);
  const gap = slots.findIndex((p) => p.licence > 5592);
  slots.splice(gap, 0, null);
  $("#parcel-grid").innerHTML = slots.map((p) => {
    if (!p) return `<div class="parcel missing"><div class="sk" style="aspect-ratio:1.55">館藏缺</div><div class="no">西字第005592號</div><h4>—</h4><div class="f">不知屬誰</div></div>`;
    const [x1, y1, x2, y2] = p.crop, [iw, ih] = p.size;
    const cw = (x2 - x1) * iw, ch = (y2 - y1) * ih;
    const style = `width:${100 / (x2 - x1)}%;left:${(-x1 / (x2 - x1)) * 100}%;top:${(-y1 * ih / ch) * 100}%`;
    return `<div class="parcel" data-pid="${p.pid}" tabindex="0">
      <div class="sk" style="aspect-ratio:${(cw / ch).toFixed(3)}"><img src="${p.img}" alt="${esc(p.toponym)} 圖略" loading="lazy" style="${style}"></div>
      <div class="no">西字第${String(p.licence).padStart(6, "0")}號　第${esc(p.section)}段${esc(p.lot)}號</div>
      <h4>${esc(p.toponym)}</h4>
      <div class="f">${esc(p.cls)}・${p.mu.toFixed(2)} 畝・賦 ${p.tax.toFixed(2)} 元</div>
    </div>`;
  }).join("");
  $("#parcel-grid").addEventListener("click", (e) => { const c = e.target.closest(".parcel[data-pid]"); if (c) openReader(c.dataset.pid); });
  $("#parcel-grid").addEventListener("keydown", (e) => { const c = e.target.closest(".parcel[data-pid]"); if (c && e.key === "Enter") openReader(c.dataset.pid); });

  /* ---------- reader ---------- */
  const clusterName = { A_yongtai_huang: "永泰黃氏", B_linsen_lin_xiuzhi: "林森林修枝", F_jianyang_liu: "建陽劉氏", C_minhou_lin_wankai: "閩侯林萬開" };
  const groups = {};
  D.reader.forEach((d, i) => { (groups[d.cluster] ||= []).push([d, i]); });
  $("#doc-select").innerHTML = Object.entries(groups).map(([c, arr]) =>
    `<optgroup label="${esc(clusterName[c] || c)}">${arr.sort((a, b) => String(a[0].date).localeCompare(String(b[0].date))).map(([d, i]) =>
      `<option value="${i}">${esc(String(d.date).split(/[（(]/)[0].slice(0, 14))}${esc(d.doc_type)}　${esc(d.title.replace(/ -- Place:.*$/, "").slice(0, 34))}</option>`).join("")}</optgroup>`).join("");
  let cur = 0, page = 0;
  function markup(tx) {
    return esc(tx)
      .replace(/〔([^〕]*)〕/g, '<span class="mark">〔$1〕</span>')
      .replace(/(□+|\[\?\])/g, '<span class="unk">$1</span>');
  }
  function showPage() {
    const d = D.reader[cur], p = d.pages[page];
    $("#page-img").src = p.img;
    $("#page-img").alt = `${d.title} 第 ${page + 1} 頁`;
    $("#transcript").innerHTML = p.tx ? markup(p.tx) : `<span class="empty">此頁沒有單獨的轉錄${d.pages.length > 1 ? "（見第 1 頁）" : ""}。</span>`;
    $("#page-label").textContent = `${page + 1} / ${d.pages.length}`;
    $("#prev").disabled = page === 0; $("#next").disabled = page === d.pages.length - 1;
    $("#viewer").classList.remove("zoomed");
  }
  function selectDoc(i) {
    cur = i; page = 0;
    const d = D.reader[i];
    $("#doc-select").value = String(i);
    $("#doc-meta").innerHTML = `${esc(d.pid)}　${esc(d.date_original || d.date)}　${esc(d.doc_type)}　識讀信心 ${d.confidence ?? "—"}　<a href="${esc(d.url)}" target="_blank" rel="noopener">館方頁面</a>`;
    showPage();
  }
  function openReader(pid) { selectDoc(readerIndex.get(pid)); $("#reader").scrollIntoView({ behavior: "smooth" }); }
  $("#doc-select").addEventListener("change", (e) => selectDoc(+e.target.value));
  $("#prev").addEventListener("click", () => { page--; showPage(); });
  $("#next").addEventListener("click", () => { page++; showPage(); });
  $("#viewer").addEventListener("click", () => $("#viewer").classList.toggle("zoomed"));
  $("#toggle-dir").addEventListener("click", (e) => {
    const v = $("#transcript").classList.toggle("vertical");
    e.currentTarget.textContent = v ? "橫排" : "直排";
  });
  selectDoc(readerIndex.get("pitt:31735066266226") ?? 0);

  /* ---------- lightbox ---------- */
  function lightbox(src, cap) {
    $("#lb-img").src = src; $("#lb-img").alt = cap; $("#lb-cap").textContent = cap;
    $("#lightbox").hidden = false; $("#lb-close").focus();
  }
  const closeLb = () => { $("#lightbox").hidden = true; };
  $("#lb-close").addEventListener("click", closeLb);
  $("#lightbox").addEventListener("click", (e) => { if (e.target.id === "lightbox") closeLb(); });
  document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeLb(); });
})();
