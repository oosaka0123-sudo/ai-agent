// 独自Markdown用の最小レンダラー。
// guides/ 配下の .md（見出し・箇条書き・太字・インラインコードのみ）をHTMLに変換する。
// 外部ライブラリに依存せず、このリポジトリで定義したテンプレート形式だけをサポートする。

const MarkdownLite = (() => {
  function escapeHTML(value) {
    return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    }[ch]));
  }

  function inline(text) {
    return escapeHTML(text)
      .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
      .replace(/`([^`]+)`/g, "<code>$1</code>");
  }

  function render(markdown) {
    const withoutComments = String(markdown || "").replace(/<!--[\s\S]*?-->/g, "");
    const lines = withoutComments.split(/\r?\n/);
    let html = "";
    let listBuffer = [];

    function flushList() {
      if (listBuffer.length) {
        html += "<ul>" + listBuffer.map((item) => `<li>${inline(item)}</li>`).join("") + "</ul>";
        listBuffer = [];
      }
    }

    lines.forEach((rawLine) => {
      const line = rawLine.trim();
      if (!line) {
        flushList();
        return;
      }

      const heading = line.match(/^(#{1,3})\s+(.*)$/);
      if (heading) {
        flushList();
        const level = Math.min(heading[1].length + 1, 4);
        html += `<h${level}>${inline(heading[2])}</h${level}>`;
        return;
      }

      const listItem = line.match(/^[-*]\s+(.*)$/);
      if (listItem) {
        listBuffer.push(listItem[1]);
        return;
      }

      flushList();
      html += `<p>${inline(line)}</p>`;
    });

    flushList();
    return html || "<p>（まだ本文がありません）</p>";
  }

  return { render };
})();
