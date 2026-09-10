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
      ["COMMAND CENTER", `${base}command-center.html`],
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
    nav.id = "siteMenu";
    nav.innerHTML = items.map(([label, href]) => {
      const resolvedPath = new URL(href, location.href).pathname;
      const isCurrent = (label === "ガイド" && inGuides) || resolvedPath === location.pathname;
      return `<a href="${href}"${isCurrent ? ' aria-current="page"' : ""}>${label}</a>`;
    }).join("");

    let toggle = topbar.querySelector(".nav-toggle");
    if (!toggle) {
      toggle = document.createElement("button");
      toggle.type = "button";
      toggle.className = "nav-toggle";
      toggle.innerHTML = '<span></span><span></span><span></span>';
      topbar.insertBefore(toggle, nav);
    }
    toggle.setAttribute("aria-controls", "siteMenu");
    toggle.setAttribute("aria-expanded", "false");
    toggle.setAttribute("aria-label", "メニューを開く");

    let backdrop = document.querySelector(".nav-backdrop");
    if (!backdrop) {
      backdrop = document.createElement("button");
      backdrop.type = "button";
      backdrop.className = "nav-backdrop";
      backdrop.setAttribute("aria-label", "メニューを閉じる");
      document.body.appendChild(backdrop);
    }

    if (!document.getElementById("shared-site-nav-style")) {
      const style = document.createElement("style");
      style.id = "shared-site-nav-style";
      style.textContent = `
        .topbar{position:sticky;top:0;z-index:60;display:flex;align-items:center;gap:12px;padding:calc(10px + env(safe-area-inset-top)) max(16px,env(safe-area-inset-right)) 10px max(16px,env(safe-area-inset-left));background:rgba(5,7,15,.94);backdrop-filter:blur(12px);border-bottom:1px solid rgba(255,255,255,.1)}
        .topbar-brand{flex:none;display:inline-flex;align-items:center;min-height:44px;text-decoration:none;font-size:13px;font-weight:800;letter-spacing:.04em;white-space:nowrap}.topbar-brand span{color:#a78bfa}
        .topbar-nav{display:flex;gap:12px;align-items:center;margin-left:auto}.topbar-nav a{font-size:.78rem;color:#a4adc4;text-decoration:none;white-space:nowrap}.topbar-nav a:hover,.topbar-nav a[aria-current="page"]{color:#fff}.topbar-nav a[aria-current="page"]{font-weight:800}
        .nav-toggle{display:none;flex:none;width:46px;height:46px;margin-left:auto;padding:0;align-items:center;justify-content:center;flex-direction:column;gap:4px;background:#111a31;border:1px solid rgba(255,255,255,.2);border-radius:12px;color:#fff;cursor:pointer;position:relative;z-index:72}
        .nav-toggle span{display:block;width:20px;height:2px;background:currentColor;border-radius:2px}.nav-toggle[aria-expanded="true"] span:nth-child(1){transform:translateY(6px) rotate(45deg)}.nav-toggle[aria-expanded="true"] span:nth-child(2){opacity:0}.nav-toggle[aria-expanded="true"] span:nth-child(3){transform:translateY(-6px) rotate(-45deg)}
        .nav-toggle:focus-visible,.topbar-nav a:focus-visible,.topbar-brand:focus-visible{outline:2px solid #60a5fa;outline-offset:3px}
        .nav-backdrop{display:none;position:fixed;inset:0;z-index:55;border:0;background:rgba(2,3,8,.72);padding:0;cursor:pointer}.nav-backdrop.is-open{display:block}body.nav-open-lock{overflow:hidden}
        @media(max-width:640px){
          .topbar{flex-wrap:wrap}.nav-toggle{display:inline-flex}.topbar .search-box{order:3;flex-basis:100%;width:100%}
          .topbar-nav{display:none;position:fixed;top:calc(12px + env(safe-area-inset-top));right:max(12px,env(safe-area-inset-right));bottom:auto;z-index:70;width:min(86vw,320px);max-height:calc(100dvh - 24px - env(safe-area-inset-top));margin:0;padding:62px 14px 18px;flex-direction:column;align-items:stretch;gap:4px;background:#0c1224;border:1px solid rgba(255,255,255,.15);border-radius:18px;box-shadow:0 24px 80px rgba(0,0,0,.58);overflow-y:auto}
          .topbar-nav.is-open{display:flex}.topbar-nav a{display:flex;align-items:center;min-height:48px;padding:12px;border-radius:11px;font-size:15px}.topbar-nav a:hover,.topbar-nav a:focus-visible,.topbar-nav a[aria-current="page"]{background:rgba(255,255,255,.07)}
        }
        @media(prefers-reduced-motion:reduce){.nav-toggle span{transition:none!important}}
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
      const firstLink = nav.querySelector("a");
      if (firstLink) requestAnimationFrame(() => firstLink.focus());
    };

    toggle.addEventListener("click", () => {
      toggle.getAttribute("aria-expanded") === "true" ? closeNav() : openNav();
    });
    backdrop.addEventListener("click", () => closeNav(true));
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

  function initSkipLink() {
    if (document.getElementById("skipToMainLink")) return;
    const skip = document.createElement("a");
    skip.id = "skipToMainLink";
    skip.className = "skip-link";
    skip.href = "#main";
    skip.textContent = "メインコンテンツへスキップ";
    document.body.insertAdjacentElement("afterbegin", skip);
  }

  function initReducedMotionGuard() {
    const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    const guard = () => {
      if (!reduceMotion.matches) return;
      document.querySelectorAll("video[autoplay]").forEach((v) => {
        v.pause();
        v.removeAttribute("autoplay");
      });
    };
    guard();
    reduceMotion.addEventListener ? reduceMotion.addEventListener("change", guard) : reduceMotion.addListener(guard);
  }

  function initPageBase() {
    initSkipLink();
    initSiteNav();
    initReducedMotionGuard();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initPageBase, { once: true });
  } else {
    initPageBase();
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
