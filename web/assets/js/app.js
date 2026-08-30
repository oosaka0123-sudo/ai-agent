// トップページ（index.html）の制御スクリプト。
// 検索・AIタグ・技術タグの絞り込みを、タイムラインとプロジェクト一覧の両方に反映する。

(async function () {
  const { loadData, AI_LIST, TECH_LIST, matchesDevlog, matchesProject, groupByDate, formatDateJa } = ArchiveData;
  const { projectCardHTML, devlogCardHTML, recentCardHTML, chipHTML, emptyStateHTML, initLightbox } = ArchiveRender;

  const els = {
    searchInput: document.getElementById("searchInput"),
    activeFilters: document.getElementById("activeFilters"),
    statsRow: document.getElementById("statsRow"),
    recentList: document.getElementById("recentList"),
    projectList: document.getElementById("projectList"),
    timelineList: document.getElementById("timelineList"),
    aiChips: document.getElementById("aiChips"),
    techChips: document.getElementById("techChips"),
  };

  const state = { query: "", ai: null, tech: null };
  let projects = [];
  let devlog = [];

  try {
    ({ projects, devlog } = await loadData());
  } catch (err) {
    els.timelineList.innerHTML = emptyStateHTML("開発記録データを読み込めませんでした。scripts/sync-site-data.sh を実行してから開いてください。");
    console.error(err);
    return;
  }

  initLightbox();
  renderStats();
  renderRecent();
  renderChips(els.aiChips, AI_LIST, "ai", devlog.map((d) => d.aiUsed || []));
  renderChips(els.techChips, TECH_LIST, "tech", devlog.map((d) => d.tech || []));
  applyFiltersAndRender();

  els.searchInput.addEventListener("input", (e) => {
    state.query = e.target.value.trim().toLowerCase();
    applyFiltersAndRender();
  });

  document.addEventListener("click", (e) => {
    const chip = e.target.closest("[data-chip-type]");
    if (chip) {
      const type = chip.dataset.chipType;
      const value = chip.dataset.chipValue;
      state[type] = state[type] === value ? null : value;
      renderChips(els.aiChips, AI_LIST, "ai", devlog.map((d) => d.aiUsed || []), state.ai);
      renderChips(els.techChips, TECH_LIST, "tech", devlog.map((d) => d.tech || []), state.tech);
      applyFiltersAndRender();
      return;
    }

    const clearBtn = e.target.closest("[data-clear-filter]");
    if (clearBtn) {
      state[clearBtn.dataset.clearFilter] = null;
      renderChips(els.aiChips, AI_LIST, "ai", devlog.map((d) => d.aiUsed || []), state.ai);
      renderChips(els.techChips, TECH_LIST, "tech", devlog.map((d) => d.tech || []), state.tech);
      applyFiltersAndRender();
    }
  });

  function renderStats() {
    els.statsRow.innerHTML = `
      <div class="stat-tile"><span class="num">${devlog.length}</span><span class="label">開発記録</span></div>
      <div class="stat-tile"><span class="num">${projects.length}</span><span class="label">プロジェクト</span></div>
      <div class="stat-tile"><span class="num">${countUsedAI()}</span><span class="label">使用AI種類</span></div>
    `;
  }

  function countUsedAI() {
    const set = new Set();
    devlog.forEach((d) => (d.aiUsed || []).forEach((a) => set.add(a)));
    return set.size;
  }

  function renderRecent() {
    const recent = devlog.slice(0, 3);
    els.recentList.innerHTML = recent.length
      ? recent.map((d) => recentCardHTML(d, projects)).join("")
      : emptyStateHTML("まだ開発記録がありません。");
  }

  function renderChips(container, list, type, usageLists, activeValue) {
    container.innerHTML = list
      .map((label) => {
        const count = usageLists.reduce((n, arr) => n + (arr.includes(label) ? 1 : 0), 0);
        return chipHTML(label, count, type, activeValue === label || state[type] === label);
      })
      .join("");
  }

  function renderActiveFilters() {
    const pills = [];
    if (state.ai) pills.push(pillHTML("AI", state.ai, "ai"));
    if (state.tech) pills.push(pillHTML("技術", state.tech, "tech"));
    if (state.query) pills.push(pillHTML("検索", state.query, null));
    els.activeFilters.innerHTML = pills.join("");
  }

  function pillHTML(label, value, clearType) {
    const clearBtn = clearType
      ? `<button type="button" data-clear-filter="${clearType}" aria-label="絞り込みを解除">×</button>`
      : "";
    return `<span class="filter-pill">${label}: ${ArchiveData.escapeHTML(value)}${clearBtn}</span>`;
  }

  function applyFiltersAndRender() {
    const filteredDevlog = devlog.filter((d) => matchesDevlog(d, state));
    const filteredProjects = projects.filter((p) => matchesProject(p, state));

    renderTimeline(filteredDevlog);
    renderProjects(filteredProjects);
    renderActiveFilters();
  }

  function renderTimeline(list) {
    if (!list.length) {
      els.timelineList.innerHTML = emptyStateHTML("この条件に一致する開発記録はまだありません。");
      return;
    }
    const groups = groupByDate(list);
    els.timelineList.innerHTML = groups
      .map(
        ([date, items]) => `
        <div class="timeline-date-group">
          <p class="timeline-date">${formatDateJa(date)}</p>
          <div class="timeline-cards">
            ${items.map((d) => devlogCardHTML(d, projects)).join("")}
          </div>
        </div>`
      )
      .join("");
  }

  function renderProjects(list) {
    els.projectList.innerHTML = list.length
      ? list.map((p) => projectCardHTML(p)).join("")
      : emptyStateHTML("この条件に一致するプロジェクトはまだありません。");
  }
})();
