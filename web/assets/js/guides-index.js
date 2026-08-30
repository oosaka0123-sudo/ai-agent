// ガイド一覧ページ（web/guides/index.html）の制御スクリプト。

(async function () {
  const { loadThemes, statusLabel } = GuidesData;
  const { badge, emptyStateHTML } = ArchiveRender;
  const { escapeHTML } = ArchiveData;
  const list = document.getElementById("themeList");

  let themes = [];
  try {
    themes = await loadThemes();
  } catch (err) {
    list.innerHTML = emptyStateHTML("ガイドのテーマ一覧を読み込めませんでした。scripts/sync-site-data.sh を実行してから開いてください。");
    console.error(err);
    return;
  }

  if (!themes.length) {
    list.innerHTML = emptyStateHTML("まだテーマがありません。");
    return;
  }

  list.innerHTML = themes
    .map(
      (theme) => `
      <a class="theme-card" href="theme.html?theme=${encodeURIComponent(theme.id)}">
        <span class="theme-card-emoji">${theme.emoji || "📘"}</span>
        <p class="theme-card-title">${escapeHTML(theme.title)}</p>
        <p class="theme-card-desc">${escapeHTML(theme.description || "")}</p>
        <div class="card-meta">${badge(statusLabel(theme.status), `guide-status-${theme.status}`)}</div>
      </a>`
    )
    .join("");
})();
