// guides-data.json / theme.json / 各AIのMarkdownを読み込む共通処理。
// web/guides/*.html から呼ばれる。データの正本は guides/ にあり、
// scripts/sync-site-data.sh が web/guides-data/ へコピーしたものを読む。

const GuidesData = (() => {
  const STATUS_LABEL = {
    "not-started": "未執筆",
    "in-progress": "執筆中",
    "published": "公開中",
  };

  // index.html（web/直下）から呼ばれる場合と、web/guides/*.html から呼ばれる場合とで
  // guides-data/ までの相対パスが1階層ぶん変わるため、現在のパスから判定する。
  const BASE = /\/guides\/[^/]*$/.test(location.pathname) ? "../guides-data/" : "guides-data/";

  async function loadThemes() {
    const res = await fetch(`${BASE}themes.json`);
    if (!res.ok) throw new Error("themes.json の読み込みに失敗しました。");
    return res.json();
  }

  async function loadTheme(themeId) {
    const res = await fetch(`${BASE}${encodeURIComponent(themeId)}/theme.json`);
    if (!res.ok) throw new Error("theme.json の読み込みに失敗しました。");
    return res.json();
  }

  async function loadGuideMarkdown(themeId, filename) {
    const res = await fetch(`${BASE}${encodeURIComponent(themeId)}/${encodeURIComponent(filename)}`);
    if (!res.ok) throw new Error("説明ファイルの読み込みに失敗しました。");
    return res.text();
  }

  function statusLabel(status) {
    return STATUS_LABEL[status] || "未執筆";
  }

  return { loadThemes, loadTheme, loadGuideMarkdown, statusLabel };
})();
