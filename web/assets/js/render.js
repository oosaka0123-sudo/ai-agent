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

  return {
    badge,
    projectCardHTML,
    devlogCardHTML,
    recentCardHTML,
    chipHTML,
    emptyStateHTML,
    initLightbox,
  };
})();
