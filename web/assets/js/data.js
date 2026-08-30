// 開発記録データの読み込みと共通の定数・ユーティリティ関数。
// data/projects.json と data/devlog.json（公開時は web/data/ にコピーされたもの）を読み込む。

const ArchiveData = (() => {
  const AI_LIST = ["Claude Code", "ChatGPT", "Codex", "Gemini", "その他"];

  const TECH_LIST = [
    "HTML", "CSS", "JavaScript", "Python", "GitHub", "GitHub Actions",
    "PWA", "Android", "API", "Cloudflare", "Vercel", "AI Agent",
  ];

  async function loadData() {
    const [projectsRes, devlogRes] = await Promise.all([
      fetch("data/projects.json"),
      fetch("data/devlog.json"),
    ]);

    if (!projectsRes.ok || !devlogRes.ok) {
      throw new Error("開発記録データの読み込みに失敗しました。");
    }

    const projects = await projectsRes.json();
    const devlog = await devlogRes.json();

    devlog.sort((a, b) => (b.date + b.id).localeCompare(a.date + a.id));

    return { projects, devlog };
  }

  function projectBySlug(projects, slug) {
    return projects.find((p) => p.slug === slug) || null;
  }

  function formatDateJa(dateStr) {
    const parts = String(dateStr || "").split("-").map(Number);
    if (parts.length !== 3 || parts.some(Number.isNaN)) return "日付未設定";
    const [y, m, d] = parts;
    return `${y}年${m}月${d}日`;
  }

  function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[ch]));
  }

  function searchTextForDevlog(d) {
    return [
      d.title, d.purpose, d.whatMade, d.problems, d.solutions, d.learnings, d.nextSteps,
      ...(d.tags || []), ...(d.tech || []), ...(d.aiUsed || []), ...(d.services || []),
    ].join(" ").toLowerCase();
  }

  function searchTextForProject(p) {
    return [
      p.name, p.summary, p.status,
      ...(p.tech || []), ...(p.aiUsed || []),
    ].join(" ").toLowerCase();
  }

  function matchesDevlog(d, state) {
    if (state.ai && !(d.aiUsed || []).includes(state.ai)) return false;
    if (state.tech && !(d.tech || []).includes(state.tech)) return false;
    if (state.query && !searchTextForDevlog(d).includes(state.query)) return false;
    return true;
  }

  function matchesProject(p, state) {
    if (state.ai && !(p.aiUsed || []).includes(state.ai)) return false;
    if (state.tech && !(p.tech || []).includes(state.tech)) return false;
    if (state.query && !searchTextForProject(p).includes(state.query)) return false;
    return true;
  }

  function groupByDate(devlogList) {
    const map = new Map();
    devlogList.forEach((d) => {
      if (!map.has(d.date)) map.set(d.date, []);
      map.get(d.date).push(d);
    });
    return Array.from(map.entries()).sort((a, b) => b[0].localeCompare(a[0]));
  }

  return {
    AI_LIST,
    TECH_LIST,
    loadData,
    projectBySlug,
    formatDateJa,
    escapeHTML,
    matchesDevlog,
    matchesProject,
    groupByDate,
  };
})();
