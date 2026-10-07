/* 读契 · Reading the Deed
 * Loads deed annotations from data/*.json and renders them over an
 * OpenSeadragon zoomable image. No build step; serve the repo root over HTTP.
 */
(() => {
  const IMG_BASE = "../images/";
  const OSD_IMAGES = "https://cdnjs.cloudflare.com/ajax/libs/openseadragon/4.1.0/images/";

  const CATEGORIES = {
    title:     { zh: "契名",   en: "Title" },
    seller:    { zh: "卖主",   en: "Seller" },
    buyer:     { zh: "买主",   en: "Buyer" },
    property:  { zh: "标的",   en: "Property" },
    boundary:  { zh: "四至",   en: "Boundaries" },
    price:     { zh: "价银",   en: "Price" },
    reason:    { zh: "缘由",   en: "Reason" },
    clause:    { zh: "条款",   en: "Clauses" },
    date:      { zh: "日期",   en: "Date" },
    middleman: { zh: "中人",   en: "Middlemen" },
    scribe:    { zh: "代笔",   en: "Scribe" },
    seal:      { zh: "官印",   en: "Seals" },
    tax:       { zh: "税契",   en: "Tax" },
    official:  { zh: "官方文字", en: "Official text" },
    other:     { zh: "其他",   en: "Other" },
  };

  const FLOW = [
    { key: "draft", icon: "✍️", cats: ["title", "seller", "reason", "property", "boundary", "scribe", "date"],
      name: { zh: "立契", en: "Drafting" }, who: { zh: "卖主 · 代笔", en: "Seller · scribe" },
      text: { zh: "卖主请代笔人按固定格式写契：谁卖、为什么卖、卖什么、坐落和四至、价钱多少。",
              en: "The seller has a scribe write the deed in a set formula: who sells, why, what, where and its boundaries, and for how much." } },
    { key: "witness", icon: "🤝", cats: ["middleman", "scribe"],
      name: { zh: "中人见证", en: "Witnessing" }, who: { zh: "中人 · 亲属", en: "Middlemen · kin" },
      text: { zh: "中人说合、作证，卖主、亲属、中人、代笔在契末画押。没有中人的契约，在纠纷中很难作数。",
              en: "Middlemen broker and witness the deal; the seller, relatives, middlemen and scribe sign or mark the end of the deed. Without them a deed carried little weight in a dispute." } },
    { key: "payment", icon: "💰", cats: ["price", "clause", "buyer"],
      name: { zh: "交银交业", en: "Payment" }, who: { zh: "买主", en: "Buyer" },
      text: { zh: "买主当场交银（「即日收足」），卖主交出田屋，连同上手老契一起交付，并写明日后不得反悔。",
              en: "The buyer pays on the spot (“received in full that day”); the seller hands over the property and any earlier deeds, and promises not to go back on the sale." } },
    { key: "tax", icon: "🏛️", cats: ["tax", "seal", "official"],
      name: { zh: "投税", en: "Tax" }, who: { zh: "县衙", en: "County yamen" },
      text: { zh: "买主拿契到县衙缴纳契税，官府粘上「契尾」并盖官印——白契变成红契，打官司时更有凭据。",
              en: "The buyer takes the deed to the county office and pays deed tax; officials attach a tax receipt (qiwei) and stamp it, turning a “white deed” into a “red deed” that courts trusted more." } },
    { key: "verify", icon: "📋", cats: ["official", "tax", "seal"],
      name: { zh: "民国验契", en: "Verification" }, who: { zh: "民国税务机关", en: "Republican tax office" },
      text: { zh: "民国政府要求旧契重新验契登记、缴纸价，换发印刷的契单；后来又发放统一格式的土地管业执照。",
              en: "Republican governments required old deeds to be re-verified for a fee and issued printed forms, and later standardized land ownership certificates." } },
    { key: "keep", icon: "🏠", cats: ["buyer", "other"],
      name: { zh: "收执", en: "Kept" }, who: { zh: "买主家族", en: "Buyer’s family" },
      text: { zh: "契纸交买主收执，作为产权凭证世代保存；日后再转卖时，它又成了下一张契的「上手契」。",
              en: "The buyer keeps the deed as proof of title for generations; when the property is sold again, it becomes the “prior deed” handed to the next buyer." } },
  ];

  const state = {
    index: null,
    deeds: {},          // id -> deed json (or null if missing)
    current: null,      // deed id
    regionIdx: -1,
    hidden: new Set(),
    showBoxes: true,
    overlays: [],       // [{region, el}]
    playing: false,
  };

  const $ = (sel) => document.querySelector(sel);
  const esc = (s) => String(s ?? "").replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const bi = (o, tag = "span") => o ? `<${tag} data-zh>${esc(o.zh)}</${tag}><${tag} data-en>${esc(o.en)}</${tag}>` : "";
  const catVar = (cat) => `--c: var(--c-${CATEGORIES[cat] ? cat : "other"})`;

  /* ---------- language ---------- */
  function setLang(lang) {
    document.body.dataset.lang = lang;
    document.querySelectorAll(".lang-switch button").forEach((b) => b.classList.toggle("active", b.dataset.lang === lang));
    try { localStorage.setItem("reader-lang", lang); } catch (e) {}
  }

  /* ---------- viewer ---------- */
  const viewer = OpenSeadragon({
    id: "viewer",
    prefixUrl: OSD_IMAGES,
    showNavigationControl: false,
    showNavigator: true,
    navigatorPosition: "BOTTOM_RIGHT",
    navigatorSizeRatio: 0.14,
    maxZoomPixelRatio: 3,
    visibilityRatio: 0.6,
    gestureSettingsMouse: { clickToZoom: false, dblClickToZoom: true },
    animationTime: 0.7,
  });

  viewer.addHandler("open", () => {
    const deed = state.deeds[state.current];
    if (deed) drawOverlays(deed);
    const m = location.hash.match(/#[^/]+\/(.+)/);
    if (m && deed) {
      const i = deed.regions.findIndex((r) => r.id === m[1]);
      if (i >= 0) selectRegion(i, { zoom: true });
    }
  });

  function regionRect(deed, r) {
    const [x, y, w, h] = r.bbox;
    return viewer.viewport.imageToViewportRectangle(x * deed.width, y * deed.height, w * deed.width, h * deed.height);
  }

  function drawOverlays(deed) {
    viewer.clearOverlays();
    // Large boxes first so smaller ones sit on top and stay clickable.
    const area = (r) => r.bbox[2] * r.bbox[3];
    const order = deed.regions.map((r, i) => i).sort((a, b) => area(deed.regions[b]) - area(deed.regions[a]));
    const made = order.map((i) => {
      const r = deed.regions[i];
      const el = document.createElement("div");
      el.className = "region-box" + (r.confidence === "low" ? " low" : "");
      el.style.cssText = catVar(r.category);
      el.title = `${r.label?.zh || ""} ${r.label?.en || ""}`;
      el.innerHTML = `<span class="tag">${esc(r.label?.zh || CATEGORIES[r.category]?.zh || "")}</span>`;
      el.hidden = state.hidden.has(r.category);
      viewer.addOverlay({ element: el, location: regionRect(deed, r) });
      new OpenSeadragon.MouseTracker({
        element: el,
        clickHandler: (e) => { if (e.quick) selectRegion(i, { zoom: false }); },
      });
      return { i, region: r, el };
    });
    state.overlays = made.sort((a, b) => a.i - b.i);
  }

  function zoomTo(deed, r) {
    const rect = regionRect(deed, r);
    const pad = Math.max(rect.width, rect.height) * 0.35;
    viewer.viewport.fitBoundsWithConstraints(new OpenSeadragon.Rect(rect.x - pad, rect.y - pad, rect.width + pad * 2, rect.height + pad * 2));
  }

  /* ---------- deed loading ---------- */
  async function loadJSON(url) {
    const res = await fetch(url, { cache: "no-cache" });
    if (!res.ok) throw new Error(`${url}: ${res.status}`);
    return res.json();
  }

  async function init() {
    let lang = "zh";
    try { lang = localStorage.getItem("reader-lang") || "zh"; } catch (e) {}
    setLang(lang);
    document.querySelectorAll(".lang-switch button").forEach((b) => b.addEventListener("click", () => setLang(b.dataset.lang)));

    state.index = await loadJSON("data/index.json");
    await Promise.all(state.index.deeds.map(async (id) => {
      try { state.deeds[id] = await loadJSON(`data/${id}.json`); }
      catch (e) { state.deeds[id] = null; console.warn(e); }
    }));

    renderTimeline();
    renderFlowSteps();
    bindControls();

    const fromHash = location.hash.slice(1).split("/")[0];
    const first = state.index.deeds.find((id) => id === fromHash && state.deeds[id])
      || state.index.deeds.find((id) => state.deeds[id]);
    if (first) openDeed(first, { keepHash: true });
  }

  function deedYear(d) { return d?.date?.western || "?"; }

  function renderTimeline() {
    const storyDeeds = new Set(state.index.stories.flatMap((s) => s.deeds));
    $("#timeline").innerHTML = state.index.deeds.map((id) => {
      const d = state.deeds[id];
      const img = d ? d.image : `${id}_001.jpg`;
      return `<button class="deed-tab" data-id="${id}" ${d ? "" : "disabled"}>
        <img src="${IMG_BASE}${img}" alt="" loading="lazy">
        <span>
          <span class="yr">${esc(deedYear(d))}</span><br>
          <span class="ty">${d ? bi(d.type) : "<span data-zh>标注中…</span><span data-en>Annotating…</span>"}</span>
          ${storyDeeds.has(id) ? `<br><span class="link-badge">⛓ <span data-zh>关联契约</span><span data-en>Linked deeds</span></span>` : ""}
        </span>
      </button>`;
    }).join("");
    $("#timeline").querySelectorAll(".deed-tab").forEach((b) => b.addEventListener("click", () => openDeed(b.dataset.id)));
  }

  function openDeed(id, { keepHash = false } = {}) {
    const deed = state.deeds[id];
    if (!deed) return;
    state.current = id;
    state.regionIdx = -1;
    if (!keepHash) history.replaceState(null, "", `#${id}`);

    document.querySelectorAll(".deed-tab").forEach((b) => b.classList.toggle("active", b.dataset.id === id));
    $(`.deed-tab[data-id="${id}"]`)?.scrollIntoView({ behavior: "smooth", inline: "nearest", block: "nearest" });

    viewer.open({ type: "image", url: IMG_BASE + deed.image, buildPyramid: false });
    $("#src-link").href = deed.source_url;

    const reviewed = deed.review?.status === "reviewed";
    const banner = $("#draft-banner");
    banner.classList.toggle("reviewed", reviewed);
    banner.innerHTML = reviewed
      ? `<span data-zh>已人工校对</span><span data-en>Human-reviewed</span>`
      : `<span data-zh>AI 初稿 · 待人工校对：转录和解释可能有误</span><span data-en>AI draft · awaiting human review: transcription and notes may contain errors</span>`;

    renderInfo(deed);
    renderLegend(deed);
    renderRegionList(deed);
    renderStory(id);
    $("#full-text").textContent = (deed.full_text || "").split(" / ").join("\n");
    renderCard(null);
    updateFlowPresence(deed);
  }

  function renderInfo(d) {
    $("#deed-info").innerHTML = `
      <h2>${esc(d.title.zh)}<br><span data-en>${esc(d.title.en)}</span></h2>
      <dl class="meta">
        <dt>${bi({ zh: "日期", en: "Date" })}</dt><dd>${esc(d.date.original)}<br><span data-zh>${esc(d.date.zh)}</span><span data-en>${esc(d.date.en)}</span></dd>
        <dt>${bi({ zh: "类型", en: "Type" })}</dt><dd>${bi(d.type)}</dd>
        <dt>${bi({ zh: "地点", en: "Place" })}</dt><dd>${bi(d.place)}</dd>
      </dl>
      <div class="summary">${bi(d.summary, "p")}</div>`;
  }

  function renderLegend(d) {
    const cats = [...new Set(d.regions.map((r) => r.category))];
    $("#legend").innerHTML = cats.map((c) => `
      <button data-cat="${c}" style="${catVar(c)}" class="${state.hidden.has(c) ? "off" : ""}">
        <span class="dot"></span>${bi(CATEGORIES[c] || CATEGORIES.other)}
      </button>`).join("");
    $("#legend").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => {
      const c = b.dataset.cat;
      state.hidden.has(c) ? state.hidden.delete(c) : state.hidden.add(c);
      b.classList.toggle("off");
      state.overlays.forEach((o) => { o.el.hidden = state.hidden.has(o.region.category); });
    }));
  }

  function renderRegionList(d) {
    $("#region-list").innerHTML = d.regions.map((r, i) => `
      <li><button data-i="${i}" style="${catVar(r.category)}">
        <span class="dot"></span><span>${bi(r.label)}</span>
      </button></li>`).join("");
    $("#region-list").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => selectRegion(+b.dataset.i, { zoom: true })));
  }

  function renderStory(id) {
    const story = state.index.stories.find((s) => s.deeds.includes(id));
    const el = $("#story");
    if (!story) { el.hidden = true; return; }
    const other = story.deeds.find((x) => x !== id);
    const od = state.deeds[other];
    el.hidden = false;
    el.innerHTML = `<h3>⛓ ${bi(story.title)}</h3>${bi(story.text, "p")}
      ${od ? `<button data-go="${other}">→ <span data-zh>看另一张：${esc(od.date.western)} ${esc(od.type.zh)}</span><span data-en>See the other: ${esc(od.date.western)} ${esc(od.type.en)}</span></button>` : ""}`;
    el.querySelector("[data-go]")?.addEventListener("click", (e) => openDeed(e.currentTarget.dataset.go));
  }

  /* ---------- regions ---------- */
  function selectRegion(i, { zoom = true } = {}) {
    const deed = state.deeds[state.current];
    if (!deed || i < 0 || i >= deed.regions.length) return;
    state.regionIdx = i;
    const r = deed.regions[i];
    state.overlays.forEach((o, j) => o.el.classList.toggle("active", j === i));
    $("#region-list").querySelectorAll("button").forEach((b) => b.classList.toggle("active", +b.dataset.i === i));
    if (zoom) zoomTo(deed, r);
    renderCard(r, i, deed.regions.length);
    history.replaceState(null, "", `#${state.current}/${r.id}`);
  }

  function renderCard(r, i, n) {
    const card = $("#region-card");
    if (!r) {
      card.style.cssText = "";
      card.innerHTML = `<p class="empty">${bi({ zh: "点击图上的彩色方框，或用 ← → 键逐个浏览。", en: "Click a coloured box on the image, or use ← → to step through." }, "span")}</p>`;
      return;
    }
    const conf = { high: { zh: "把握高", en: "high confidence" }, medium: { zh: "把握中", en: "medium confidence" }, low: { zh: "把握低", en: "low confidence" } }[r.confidence] || null;
    card.style.cssText = catVar(r.category);
    card.innerHTML = `
      <span class="cat">● ${bi(CATEGORIES[r.category] || CATEGORIES.other)}</span>
      <h3>${bi(r.label)}${conf ? `<span class="conf ${r.confidence}">${bi(conf)}</span>` : ""}</h3>
      <div class="original">${esc(r.original)}</div>
      <div data-zh><div class="lbl">白话</div><p>${esc(r.modern_zh)}</p></div>
      <div data-en><div class="lbl">English</div><p>${esc(r.english)}</p></div>
      ${r.note ? `<div class="note">${esc(r.note)}</div>` : ""}
      <div class="card-nav"><span>${i + 1} / ${n}</span><span>← →</span></div>`;
  }

  function step(delta) {
    const deed = state.deeds[state.current];
    if (!deed) return;
    const visible = deed.regions.map((r, i) => i).filter((i) => !state.hidden.has(deed.regions[i].category));
    if (!visible.length) return;
    const pos = visible.indexOf(state.regionIdx);
    const next = pos < 0 ? (delta > 0 ? 0 : visible.length - 1) : (pos + delta + visible.length) % visible.length;
    selectRegion(visible[next], { zoom: true });
  }

  /* ---------- flow animation ---------- */
  function renderFlowSteps() {
    const track = $("#flow-track");
    FLOW.forEach((s, i) => {
      const b = document.createElement("button");
      b.className = "flow-step";
      b.dataset.i = i;
      b.innerHTML = `<span class="icon">${s.icon}</span><span class="name">${bi(s.name)}</span><span class="who">${bi(s.who)}</span><span class="absent"></span>`;
      b.addEventListener("click", () => { stopPlay(); showStep(i); });
      track.appendChild(b);
    });
  }

  function updateFlowPresence(deed) {
    const flow = new Set(deed.flow || []);
    document.querySelectorAll(".flow-step").forEach((b) => {
      const present = flow.has(FLOW[b.dataset.i].key);
      b.classList.toggle("present", present);
      b.classList.remove("current");
      b.querySelector(".absent").innerHTML = present ? "" : bi({ zh: "本契未体现", en: "not on this deed" });
    });
    $("#flow-paper").style.opacity = 0;
    $("#flow-paper").classList.remove("stamped");
    $("#flow-caption").innerHTML = bi({ zh: "点「播放」看一张契纸从立契到收执的旅程；亮着的步骤在这张契纸上留下了痕迹。", en: "Press Play to follow a deed from drafting to safekeeping; highlighted steps left traces on this deed." }, "div");
  }

  function showStep(i) {
    const s = FLOW[i];
    const deed = state.deeds[state.current];
    const steps = document.querySelectorAll(".flow-step");
    steps.forEach((b, j) => b.classList.toggle("current", j === i));

    const paper = $("#flow-paper");
    const track = $("#flow-track").getBoundingClientRect();
    const icon = steps[i].querySelector(".icon").getBoundingClientRect();
    paper.style.left = `${icon.left - track.left + icon.width / 2 - 17}px`;
    paper.style.opacity = 1;
    if (s.key === "tax" || s.key === "verify") paper.classList.add("stamped");
    if (i === 0) paper.classList.remove("stamped");

    const present = deed && (deed.flow || []).includes(s.key);
    const related = present ? deed.regions.filter((r) => s.cats.includes(r.category)) : [];
    const evidence = related.slice(0, 4).map((r) => esc(r.original).slice(0, 18)).join("　·　");
    $("#flow-caption").innerHTML = `
      <div data-zh>${esc(s.text.zh)}${present && evidence ? `<br><strong>本契：</strong>${evidence}` : present ? "" : "<br><em>这张契纸上没有这一步的痕迹。</em>"}</div>
      <div data-en>${esc(s.text.en)}${present ? "" : " <em>This deed shows no trace of this step.</em>"}</div>`;

    related.forEach((r) => {
      const o = state.overlays.find((x) => x.region === r);
      if (o) { o.el.classList.remove("flash"); void o.el.offsetWidth; o.el.classList.add("flash"); }
    });
  }

  let playTimer = null;
  function play() {
    if (state.playing) return stopPlay();
    state.playing = true;
    $("#btn-play").innerHTML = `■ <span data-zh>停止</span><span data-en>Stop</span>`;
    viewer.viewport.goHome();
    let i = 0;
    showStep(i);
    playTimer = setInterval(() => {
      i += 1;
      if (i >= FLOW.length) return stopPlay();
      showStep(i);
    }, 2600);
  }
  function stopPlay() {
    state.playing = false;
    clearInterval(playTimer);
    $("#btn-play").innerHTML = `▶ <span data-zh>播放</span><span data-en>Play</span>`;
  }

  /* ---------- controls ---------- */
  function bindControls() {
    $("#btn-home").addEventListener("click", () => viewer.viewport.goHome());
    $("#btn-prev").addEventListener("click", () => step(-1));
    $("#btn-next").addEventListener("click", () => step(1));
    $("#btn-play").addEventListener("click", play);
    $("#btn-boxes").addEventListener("click", (e) => {
      state.showBoxes = !state.showBoxes;
      e.currentTarget.setAttribute("aria-pressed", state.showBoxes);
      $("#viewer").classList.toggle("hide-boxes", !state.showBoxes);
    });
    document.addEventListener("keydown", (e) => {
      if (e.target.closest("input, textarea")) return;
      if (e.key === "ArrowRight") step(1);
      else if (e.key === "ArrowLeft") step(-1);
      else if (e.key === "Escape") { viewer.viewport.goHome(); renderCard(null); state.overlays.forEach((o) => o.el.classList.remove("active")); state.regionIdx = -1; }
    });
  }

  init().catch((e) => {
    console.error(e);
    $("#deed-info").innerHTML = `<p>${esc(e.message)}</p><p>请用本地服务器打开（例如在仓库根目录运行 <code>python3 -m http.server</code>，再访问 /reader/）。</p>`;
  });
})();
