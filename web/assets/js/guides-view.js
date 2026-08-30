// 説明ページ（web/guides/view.html?theme=xxx&ai=yyy）の制御スクリプト。
// 指定されたテーマ・AIのMarkdownを読み込んで表示する。

(async function () {
  const { loadTheme, loadGuideMarkdown, statusLabel } = GuidesData;
  const { badge, emptyStateHTML } = ArchiveRender;
  const { escapeHTML } = ArchiveData;

  const params = new URLSearchParams(location.search);
  const themeId = params.get("theme");
  const aiId = params.get("ai");

  const headEl = document.getElementById("viewHead");
  const bodyEl = document.getElementById("viewBody");
  const switcherEl = document.getElementById("aiSwitcher");
  const backLink = document.getElementById("backLink");

  if (!themeId || !aiId) {
    headEl.innerHTML = emptyStateHTML("テーマまたはAIが指定されていません。");
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

  backLink.href = `theme.html?theme=${encodeURIComponent(themeId)}`;

  const ai = (theme.ais || []).find((a) => a.id === aiId);
  if (!ai) {
    headEl.innerHTML = emptyStateHTML("指定されたAIの説明が見つかりませんでした。");
    return;
  }

  document.title = `${ai.label}の説明（${theme.title}） | MY DEVELOPMENT ARCHIVE`;

  headEl.innerHTML = `
    <p class="detail-eyebrow">${escapeHTML(theme.title)}</p>
    <h1 class="detail-title">${ai.emoji || "🤖"} ${escapeHTML(ai.label)} の説明</h1>
    <div class="detail-badges">${badge(statusLabel(ai.status), `guide-status-${ai.status}`)}</div>
  `;

  switcherEl.innerHTML = (theme.ais || [])
    .map((other) => {
      const isCurrent = other.id === ai.id;
      return `<a class="chip${isCurrent ? " is-active" : ""}" href="view.html?theme=${encodeURIComponent(themeId)}&ai=${encodeURIComponent(other.id)}">${other.emoji || "🤖"} ${escapeHTML(other.label)}</a>`;
    })
    .join("");

  try {
    const markdown = await loadGuideMarkdown(themeId, ai.file);
    bodyEl.innerHTML = MarkdownLite.render(markdown);
  } catch (err) {
    bodyEl.innerHTML = emptyStateHTML("説明ファイルを読み込めませんでした。");
    console.error(err);
  }
})();
