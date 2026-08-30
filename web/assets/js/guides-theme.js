// テーマ詳細ページ（web/guides/theme.html?theme=xxx）の制御スクリプト。
// 1つのテーマについて、Claude Code / Gemini・Jules / Codex の3枚のカードを表示する。

(async function () {
  const { loadTheme, statusLabel } = GuidesData;
  const { badge, emptyStateHTML } = ArchiveRender;
  const { escapeHTML } = ArchiveData;

  const themeId = new URLSearchParams(location.search).get("theme");
  const headEl = document.getElementById("themeHead");
  const aiListEl = document.getElementById("aiList");
  const backLink = document.getElementById("backLink");

  if (!themeId) {
    headEl.innerHTML = emptyStateHTML("テーマが指定されていません。");
    return;
  }

  let theme;
  try {
    theme = await loadTheme(themeId);
  } catch (err) {
    headEl.innerHTML = emptyStateHTML("このテーマを読み込めませんでした。");
    console.error(err);
    return;
  }

  document.title = `${theme.title} | MY DEVELOPMENT ARCHIVE`;
  backLink.href = "index.html";

  headEl.innerHTML = `
    <p class="detail-eyebrow">ガイド テーマ</p>
    <h1 class="detail-title">${theme.emoji || "📘"} ${escapeHTML(theme.title)}</h1>
    <p class="theme-card-desc" style="font-size:15px">${escapeHTML(theme.description || "")}</p>
  `;

  aiListEl.innerHTML = (theme.ais || [])
    .map(
      (ai) => `
      <a class="ai-choice-card" href="view.html?theme=${encodeURIComponent(themeId)}&ai=${encodeURIComponent(ai.id)}">
        <span class="ai-choice-emoji">${ai.emoji || "🤖"}</span>
        <p class="ai-choice-label">${escapeHTML(ai.label)}の説明を見る</p>
        ${badge(statusLabel(ai.status), `guide-status-${ai.status}`)}
      </a>`
    )
    .join("");
})();
