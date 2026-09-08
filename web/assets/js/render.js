// カード・チップなどのHTML生成と、画像拡大表示（ライトボックス）の共通処理。

const ArchiveRender = (() => {
  const { escapeHTML, formatDateJa, projectBySlug } = ArchiveData;

  function badge(text, extraClass) {
    return `<span class="badge ${extraClass || ""}">${escapeHTML(text)}</span>`;
  }

  function projectCardHTML(project) {
    const tech = (project.tech || []).slice(0, 3).map((t) => badge(t)).join("");
    return `
      <a class="card" href="project.html?slug=${encodeURIComponent(project.slug)}">
        <span class="card-emoji">${project.emoji || "📁"}</span>
        <p class="card-title">${escapeHTML(project.name)}</p>
        <p class="card-sub">${escapeHTML(project.summary || "")}</p>
        <div class="card-meta">
          ${badge(project.status || "情報未入力", `status-${project.status || "情報未入力"}`)}
          ${tech}
        </div>
      </a>`;
  }

  function devlogCardHTML(entry, projects) {
    const project = projectBySlug(projects, entry.project);
    const aiBadges = (entry.aiUsed || []).map((a) => badge(a)).join("");
    return `
      <a class="timeline-card" href="devlog.html?id=${encodeURIComponent(entry.id)}">
        <p class="timeline-card-title">${project ? project.emoji + " " : ""}${escapeHTML(entry.title)}</p>
        <p class="timeline-card-desc">${escapeHTML(entry.whatMade || entry.purpose || "")}</p>
        <div class="timeline-card-meta">
          ${project ? badge(project.name) : ""}
          ${aiBadges}
        </div>
      </a>`;
  }

  function recentCardHTML(entry, projects) {
    const project = projectBySlug(projects, entry.project);
    return `
      <a class="card" href="devlog.html?id=${encodeURIComponent(entry.id)}">
        <span class="card-emoji">${project ? project.emoji : "📝"}</span>
        <p class="card-title">${formatDateJa(entry.date)}</p>
        <p class="card-sub">${escapeHTML(entry.title)}</p>
      </a>`;
  }

  function chipHTML(label, count, type, isActive) {
    return `
      <button type="button" class="chip${isActive ? " is-active" : ""}" data-chip-type="${type}" data-chip-value="${escapeHTML(label)}">
        ${escapeHTML(label)}<span class="count">${count}</span>
      </button>`;
  }

  function emptyStateHTML(message) {
    return `<div class="empty-state">${escapeHTML(message)}</div>`;
  }

  function initLightbox() {
    let overlay = document.querySelector(".lightbox-overlay");
    if (!overlay) {
      overlay = document.createElement("div");
      overlay.className = "lightbox-overlay";
      overlay.innerHTML = '<img alt="拡大画像">';
      document.body.appendChild(overlay);
      overlay.addEventListener("click", () => overlay.classList.remove("is-open"));
    }
    const img = overlay.querySelector("img");

    document.addEventListener("click", (event) => {
      const target = event.target.closest("[data-lightbox]");
      if (!target) return;
      event.preventDefault();
      img.src = target.getAttribute("data-lightbox");
      img.alt = target.alt || "拡大画像";
      overlay.classList.add("is-open");
    });
  }

  function initSiteNav() {
    if (document.documentElement.dataset.siteNavReady === "1") return;
    document.documentElement.dataset.siteNavReady = "1";

    const inGuides = location.pathname.includes("/guides/");
    const base = inGuides ? "../" : "";
    const items = [
      ["HOME", `${base}index.html`],
      ["REMOTE + GCLOUD", `${base}remote-gcloud.html`],
      ["MEDIA LAB", `${base}media-lab.html`],
      ["ガイド", inGuides ? "index.html" : "guides/index.html"],
      ["構成図", `${base}diagram.html`],
    ];

    let topbar = document.querySelector(".topbar");
    if (!topbar) {
      topbar = document.createElement("header");
      topbar.className = "topbar";
      topbar.innerHTML = `<a class="topbar-brand" href="${base}index.html">MY <span>DEV</span> ARCHIVE</a>`;
      document.body.insertAdjacentElement("afterbegin", topbar);
    }

    let nav = topbar.querySelector(".topbar-nav");
    if (!nav) {
      nav = document.createElement("nav");
      nav.className = "topbar-nav";
      nav.setAttribute("aria-label", "メインメニュー");
      topbar.appendChild(nav);
    }

    const current = location.pathname.split("/").pop() || "index.html";
    nav.innerHTML = items.map(([label, href]) => {
      const hrefFile = href.split("/").pop();
      const isCurrent = (label === "ガイド" && inGuides) || hrefFile === current;
      return `<a href="${href}"${isCurrent ? ' aria-current="page"' : ""}>${label}</a>`;
    }).join("");

    let toggle = topbar.querySelector(".nav-toggle");
    if (!toggle) {
      toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "nav-toggle";
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "メニューを開く");
      toggle.innerHTML = '<span></span><span></span><span></span>';
      topbar.insertBefore(toggle, nav);
    }

    let backdrop = document.querySelector(".nav-backdrop");
    if (!backdrop) {
      backdrop = document.createElement("div");
      backdrop.className = "nav-backdrop";
      document.body.appendChild(backdrop);
    }

    if (!document.getElementById("shared-site-nav-style")) {
      const style = document.createElement("style");
      style.id = "shared-site-nav-style";
      style.textContent = `
        .topbar{position:sticky;top:0;z-index:40;display:flex;align-items:center;gap:12px;padding:10px 16px;background:rgba(5,7,15,.9);backdrop-filter:blur(12px);border-bottom:1px solid rgba(255,255,255,.1)}
        .topbar-brand{flex:none;text-decoration:none;font-size:13px;font-weight:800;letter-spacing:.04em;white-space:nowrap}.topbar-brand span{color:#a78bfa}
        .topbar-nav{display:flex;gap:12px;align-items:center;margin-left:auto}.topbar-nav a{font-size:.78rem;color:#a4adc4;text-decoration:none;white-space:nowrap}.topbar-nav a:hover,.topbar-nav a[aria-current="page"]{color:#fff}.topbar-nav a[aria-current="page"]{font-weight:800}
        .nav-toggle{display:none;width:44px;height:44px;margin-left:auto;padding:0;align-items:center;justify-content:center;flex-direction:column;gap:4px;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);border-radius:10px;color:#fff;cursor:pointer}
        .nav-toggle span{display:block;width:18px;height:2px;background:currentColor;border-radius:2px;transition:transform .2s ease,opacity .2s ease}.nav-toggle[aria-expanded="true"] span:nth-child(1){transform:translateY(6px) rotate(45deg)}.nav-toggle[aria-expanded="true"] span:nth-child(2){opacity:0}.nav-toggle[aria-expanded="true"] span:nth-child(3){transform:translateY(-6px) rotate(-45deg)}
        .nav-toggle:focus-visible,.topbar-nav a:focus-visible,.topbar-brand:focus-visible{outline:2px solid #60a5fa;outline-offset:3px}
        .nav-backdrop{position:fixed;inset:0;z-index:34;background:rgba(2,3,8,.64);opacity:0;pointer-events:none;transition:opacity .2s ease}.nav-backdrop.is-open{opacity:1;pointer-events:auto}body.nav-open-lock{overflow:hidden}
        @media(max-width:640px){.nav-toggle{display:inline-flex}.topbar-nav{position:fixed;top:0;right:0;bottom:0;z-index:35;width:min(82vw,310px);margin:0;padding:72px 18px 26px;display:flex;flex-direction:column;align-items:stretch;gap:4px;background:#0c1224;border-left:1px solid rgba(255,255,255,.12);box-shadow:-24px 0 60px rgba(0,0,0,.45);transform:translateX(100%);transition:transform .24s ease;overflow-y:auto}.topbar-nav.is-open{transform:translateX(0)}.topbar-nav a{display:flex;align-items:center;min-height:46px;padding:12px 10px;border-radius:10px;font-size:15px}.topbar-nav a:hover,.topbar-nav a:focus-visible{background:rgba(255,255,255,.06)}}
        @media(prefers-reduced-motion:reduce){.nav-toggle span,.topbar-nav,.nav-backdrop{transition:none!important}}
      `;
      document.head.appendChild(style);
    }

    const closeNav = (focusToggle = false) => {
      toggle.setAttribute("aria-expanded", "false");
      toggle.setAttribute("aria-label", "メニューを開く");
      nav.classList.remove("is-open");
      backdrop.classList.remove("is-open");
      document.body.classList.remove("nav-open-lock");
      if (focusToggle) toggle.focus();
    };

    const openNav = () => {
      toggle.setAttribute("aria-expanded", "true");
      toggle.setAttribute("aria-label", "メニューを閉じる");
      nav.classList.add("is-open");
      backdrop.classList.add("is-open");
      document.body.classList.add("nav-open-lock");
    };

    toggle.addEventListener("click", () => {
      toggle.getAttribute("aria-expanded") === "true" ? closeNav() : openNav();
    });
    backdrop.addEventListener("click", () => closeNav());
    nav.addEventListener("click", (event) => {
      if (event.target.closest("a")) closeNav();
    });
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && toggle.getAttribute("aria-expanded") === "true") closeNav(true);
    });
    const desktop = window.matchMedia("(min-width:641px)");
    const syncDesktop = (event) => { if (event.matches) closeNav(); };
    desktop.addEventListener ? desktop.addEventListener("change", syncDesktop) : desktop.addListener(syncDesktop);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initSiteNav, { once: true });
  } else {
    initSiteNav();
  }

  return {
    badge,
    projectCardHTML,
    devlogCardHTML,
    recentCardHTML,
    chipHTML,
    emptyStateHTML,
    initLightbox,
    initSiteNav,
  };
})();
