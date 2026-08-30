// プロジェクト詳細ページ（project.html?slug=xxx）の制御スクリプト。

(async function () {
  const { loadData, escapeHTML, formatDateJa } = ArchiveData;
  const { badge, emptyStateHTML, initLightbox } = ArchiveRender;

  const root = document.getElementById("projectDetail");
  const slug = new URLSearchParams(location.search).get("slug");

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

  const project = projects.find((p) => p.slug === slug);
  if (!project) {
    root.innerHTML = emptyStateHTML("指定されたプロジェクトが見つかりませんでした。");
    return;
  }

  document.title = `${project.name} | MY DEVELOPMENT ARCHIVE`;

  const relatedLogs = devlog.filter((d) => d.project === project.slug);

  root.innerHTML = `
    <p class="detail-eyebrow">プロジェクト</p>
    <h1 class="detail-title">${project.emoji || "📁"} ${escapeHTML(project.name)}</h1>
    <div class="detail-badges">
      ${badge(project.status || "情報未入力", `status-${project.status || "情報未入力"}`)}
      ${project.startDate ? badge("開始: " + formatDateJa(project.startDate)) : badge("開始日: 未設定")}
    </div>

    <div class="detail-panel">
      <h2>概要</h2>
      <p>${escapeHTML(project.summary || "（概要は未入力です）")}</p>
    </div>

    <div class="detail-panel">
      <h2>使用AI</h2>
      <p>${(project.aiUsed || []).length ? (project.aiUsed || []).map((a) => badge(a)).join(" ") : "未入力"}</p>
      <div class="detail-field">
        <h2 style="margin-top:0">使用技術</h2>
        <p>${(project.tech || []).length ? (project.tech || []).map((t) => badge(t)).join(" ") : "未入力"}</p>
      </div>
    </div>

    <div class="detail-panel">
      <h2>リンク</h2>
      <ul class="link-list">
        ${project.github ? `<li><a href="${escapeHTML(project.github)}" target="_blank" rel="noopener">🔗 GitHubリポジトリ</a></li>` : ""}
        ${project.website ? `<li><a href="${escapeHTML(project.website)}" target="_blank" rel="noopener">🌐 公開サイト</a></li>` : ""}
        ${!project.github && !project.website ? "<li>登録されているリンクはありません。</li>" : ""}
      </ul>
    </div>

    ${(project.screenshots || []).length ? `
      <div class="detail-panel">
        <h2>スクリーンショット</h2>
        <div class="shot-grid">
          ${project.screenshots.map((src) => `<img src="${escapeHTML(src)}" alt="${escapeHTML(project.name)}のスクリーンショット" data-lightbox="${escapeHTML(src)}">`).join("")}
        </div>
      </div>` : ""}

    <div class="detail-panel">
      <h2>開発履歴（${relatedLogs.length}件）</h2>
      ${relatedLogs.length ? `
        <div class="related-devlog-list">
          ${relatedLogs.map((d) => `
            <a class="timeline-card" href="devlog.html?id=${encodeURIComponent(d.id)}">
              <p class="timeline-card-title">${formatDateJa(d.date)}　${escapeHTML(d.title)}</p>
              <p class="timeline-card-desc">${escapeHTML(d.whatMade || d.purpose || "")}</p>
            </a>`).join("")}
        </div>` : "<p>このプロジェクトに紐づく開発記録はまだありません。</p>"}
    </div>
  `;
})();
