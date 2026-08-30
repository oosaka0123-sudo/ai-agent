// 開発記録詳細ページ（devlog.html?id=xxx）の制御スクリプト。

(async function () {
  const { loadData, escapeHTML, formatDateJa, projectBySlug } = ArchiveData;
  const { badge, emptyStateHTML, initLightbox } = ArchiveRender;

  const root = document.getElementById("devlogDetail");
  const id = new URLSearchParams(location.search).get("id");

  let projects = [];
  let devlog = [];

  try {
    ({ projects, devlog } = await loadData());
  } catch (err) {
    root.innerHTML = emptyStateHTML("開発記録データを読み込めませんでした。");
    console.error(err);
    return;
  }

  initLightbox();

  const entry = devlog.find((d) => d.id === id);
  if (!entry) {
    root.innerHTML = emptyStateHTML("指定された開発記録が見つかりませんでした。");
    return;
  }

  document.title = `${entry.title} | MY DEVELOPMENT ARCHIVE`;
  const project = projectBySlug(projects, entry.project);

  function field(title, value) {
    if (!value) return "";
    return `<div class="detail-field"><h2>${title}</h2><p>${escapeHTML(value)}</p></div>`;
  }

  function listField(title, items) {
    if (!items || !items.length) return "";
    return `<div class="detail-field"><h2>${title}</h2><ul>${items.map((i) => `<li>${escapeHTML(i)}</li>`).join("")}</ul></div>`;
  }

  function linkListField(title, items, icon) {
    if (!items || !items.length) return "";
    return `<div class="detail-field"><h2>${title}</h2><ul class="link-list">${items
      .map((i) => `<li><a href="${escapeHTML(i.url)}" target="_blank" rel="noopener">${icon} ${escapeHTML(i.label)}</a></li>`)
      .join("")}</ul></div>`;
  }

  root.innerHTML = `
    <p class="detail-eyebrow">${formatDateJa(entry.date)}${project ? " ・ " + project.emoji + " " + escapeHTML(project.name) : ""}</p>
    <h1 class="detail-title">${escapeHTML(entry.title)}</h1>
    <div class="detail-badges">
      ${(entry.aiUsed || []).map((a) => badge(a)).join("")}
      ${(entry.tags || []).map((t) => badge(t)).join("")}
    </div>

    <div class="detail-panel">
      ${field("目的", entry.purpose)}
      ${field("何を作ったか", entry.whatMade)}
      ${listField("どこを変更したか", entry.changes)}
    </div>

    <div class="detail-panel">
      <h2>使ったAI・サービス・技術</h2>
      <p>
        ${(entry.aiUsed || []).map((a) => badge(a)).join(" ") || "未入力"}
        ${(entry.services || []).map((s) => badge(s)).join(" ")}
        ${(entry.tech || []).map((t) => badge(t)).join(" ")}
      </p>
    </div>

    ${(entry.problems || entry.solutions || entry.learnings) ? `
      <div class="detail-panel">
        ${field("困ったこと", entry.problems)}
        ${field("解決方法", entry.solutions)}
        ${field("学んだこと", entry.learnings)}
      </div>` : ""}

    ${(entry.images || []).length ? `
      <div class="detail-panel">
        <h2>完成画像</h2>
        <div class="shot-grid">
          ${entry.images.map((src) => `<img src="${escapeHTML(src)}" alt="${escapeHTML(entry.title)}の画像" data-lightbox="${escapeHTML(src)}">`).join("")}
        </div>
      </div>` : ""}

    ${(entry.githubCommits || []).length || (entry.pullRequests || []).length || (entry.relatedUrls || []).length ? `
      <div class="detail-panel">
        ${linkListField("GitHubコミット", entry.githubCommits, "🔗")}
        ${linkListField("Pull Request", entry.pullRequests, "🔀")}
        ${linkListField("関連URL", entry.relatedUrls, "🌐")}
      </div>` : ""}

    ${field("次にやること", entry.nextSteps) ? `<div class="detail-panel">${field("次にやること", entry.nextSteps)}</div>` : ""}
  `;
})();
