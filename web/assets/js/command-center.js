(() => {
  const esc = (v) => String(v ?? "").replace(/[&<>'"]/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
  const statusLabel = {ok:'OK',warn:'WARN',blocked:'BLOCKED',open:'OPEN',down:'DOWN',unknown:'UNKNOWN'};

  function actionHTML(item) {
    const status = item.status || 'open';
    return `<article class="cc-row" data-status="${esc(status)}">
      <span class="cc-dot" aria-hidden="true"></span>
      <div><p class="cc-title">${esc(item.title)}</p><p class="cc-desc">${esc(item.detail)}</p></div>
      <span class="cc-chip ${esc(item.priority || '')}">${esc(item.owner || '')} · ${esc(item.priority || 'normal')}</span>
    </article>`;
  }

  function healthHTML(item) {
    const status = item.status || 'unknown';
    return `<article class="cc-row" data-status="${esc(status)}">
      <span class="cc-dot" aria-hidden="true"></span>
      <div><p class="cc-title">${esc(item.name)}</p><p class="cc-desc">${esc(item.summary)}</p></div>
      <span class="cc-chip">${esc(statusLabel[status] || status)}</span>
    </article>`;
  }

  function roleHTML(item) {
    return `<article class="cc-role"><strong>${esc(item.name)}</strong><span>${esc(item.tag)}</span><p>${esc(item.scope)}</p></article>`;
  }

  async function init() {
    const actions = document.getElementById('ccActions');
    const health = document.getElementById('ccHealth');
    const roles = document.getElementById('ccRoles');
    try {
      const res = await fetch('data/command-center.json', {cache:'no-store'});
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      actions.innerHTML = (data.nextActions || []).map(actionHTML).join('') || '<p class="cc-desc">次アクションはありません。</p>';
      health.innerHTML = (data.stackHealth || []).map(healthHTML).join('') || '<p class="cc-desc">状態データがありません。</p>';
      roles.innerHTML = (data.agentRoles || []).map(roleHTML).join('') || '<p class="cc-desc">役割データがありません。</p>';
      const total = (data.stackHealth || []).length;
      const ok = (data.stackHealth || []).filter((x) => x.status === 'ok').length;
      document.getElementById('ccHealthScore').textContent = `${ok}/${total}`;
      document.getElementById('ccUpdated').textContent = `Snapshot: ${data.updatedAt || 'unknown'} · ${data.mode || 'manual'}`;
    } catch (error) {
      actions.innerHTML = `<p class="cc-desc">司令塔データを読み込めませんでした: ${esc(error.message)}</p>`;
      health.innerHTML = roles.innerHTML = '<p class="cc-desc">再読み込みしてください。</p>';
      document.getElementById('ccUpdated').textContent = 'data unavailable';
    }
  }

  document.readyState === 'loading' ? document.addEventListener('DOMContentLoaded', init, {once:true}) : init();
})();
