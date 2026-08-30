<!-- 執筆者: Gemini / Jules -->
<!-- ステータス: completed -->

<style>
  .guide-container {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #e0e0e0;
    line-height: 1.6;
    max-width: 100%;
    overflow-x: hidden;
  }
  .guide-card {
    background: #1e1e1e;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 20px;
    border: 1px solid #333;
    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
  }
  .guide-card h3 {
    margin-top: 0;
    color: #4CAF50;
    border-bottom: 1px solid #333;
    padding-bottom: 8px;
    font-size: 1.2rem;
  }
  .comparison-table {
    width: 100%;
    border-collapse: collapse;
    margin-top: 12px;
    font-size: 0.9rem;
    overflow-x: auto;
    display: block;
    white-space: nowrap;
  }
  .comparison-table th, .comparison-table td {
    border: 1px solid #444;
    padding: 8px 12px;
    text-align: left;
  }
  .comparison-table th {
    background: #2c2c2c;
    color: #fff;
  }
  .indicator-yes {
    color: #4CAF50;
    font-weight: bold;
  }
  .indicator-no {
    color: #F44336;
    font-weight: bold;
  }
  .indicator-partial {
    color: #FFC107;
    font-weight: bold;
  }
  .flowchart {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin: 16px 0;
  }
  .flow-step {
    background: #252526;
    border: 1px solid #444;
    border-radius: 8px;
    padding: 12px;
    position: relative;
    text-align: center;
  }
  .flow-step::after {
    content: '↓';
    position: absolute;
    bottom: -20px;
    left: 50%;
    transform: translateX(-50%);
    font-size: 1.2rem;
    color: #666;
  }
  .flow-step:last-child::after {
    content: none;
  }
  .arch-diagram {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
    background: #111;
    padding: 16px;
    border-radius: 8px;
    border: 1px dashed #555;
    text-align: center;
  }
  .arch-node {
    background: #333;
    padding: 12px;
    border-radius: 6px;
    font-size: 0.9rem;
  }
  .arch-node-full {
    grid-column: span 2;
    background: #2a2a2a;
    border: 1px solid #666;
  }
  .highlight-box {
    background: rgba(76, 175, 80, 0.1);
    border-left: 4px solid #4CAF50;
    padding: 12px;
    margin: 16px 0;
    border-radius: 0 8px 8px 0;
  }

  /* Mobile prioritization overrides */
  @media (max-width: 480px) {
    .comparison-table {
      font-size: 0.8rem;
    }
    .arch-diagram {
      grid-template-columns: 1fr;
    }
    .arch-node-full {
      grid-column: span 1;
    }
    h2 { font-size: 1.3rem; }
    h3 { font-size: 1.1rem; }
  }
</style>

<div class="guide-container">

## この方法の特徴

<div class="highlight-box">
  <strong>【結論】</strong> PCは一切不要。スマホのブラウザのみで、AIエージェントによる自律的な調査からコーディング、GitHubへの保存、そして世界への公開（GitHub Pages）まで、すべてのAI開発フローを完結させる最先端のアプローチです。
</div>

<div class="guide-card">
  <h3>スマホ完結AI開発の3大特徴</h3>
  <ul>
    <li>🚀 <strong>超軽量スタート:</strong> 専用アプリや重いIDE（開発環境）のインストール不要。必要なのはブラウザだけ。</li>
    <li>🤖 <strong>AIチーム駆動:</strong> Claude Code、Gemini/Jules、OpenAI Codexを並行稼働させ、各AIの強みを活かした共同開発が可能。</li>
    <li>🔄 <strong>完全自律実行:</strong> AIがGitHubを「共通記憶」として扱い、リポジトリの読み書き、ブランチ作成、PR発行までを自律的に行う。</li>
  </ul>
</div>

## 必要なサービス

以下のサービスのアカウント（すべて無料枠あり）を用意するだけです。

<div class="arch-diagram">
  <div class="arch-node arch-node-full"><strong>1. GitHub アカウント</strong><br>コードの保存・バージョン管理・公開基盤</div>
  <div class="arch-node"><strong>2. AIプロバイダ</strong><br>Anthropic, Google, OpenAI等のAPIまたはチャット画面</div>
  <div class="arch-node"><strong>3. GitHub Pages</strong><br>作ったものを無料で即座にWeb公開</div>
</div>

## スマホでの手順

<div class="guide-card">
  <h3>実践フロー：調査から公開まで</h3>
  <div class="flowchart">
    <div class="flow-step"><strong>1. 調査・設計 (AI)</strong><br>AIに作りたいものを伝え、構成を提案させる</div>
    <div class="flow-step"><strong>2. リポジトリ準備 (GitHub)</strong><br>スマホのブラウザでGitHubを開き、空のリポジトリを作成</div>
    <div class="flow-step"><strong>3. 実装依頼 (AI)</strong><br>AIに「専用ブランチを作ってコードを書き、PRを出して」と指示</div>
    <div class="flow-step"><strong>4. レビュー・修正 (AI自律)</strong><br>AIが自分でコードを書き、テストし、修正まで行う</div>
    <div class="flow-step"><strong>5. マージ・公開 (GitHub)</strong><br>スマホでPRを承認・マージし、GitHub Pagesで自動公開</div>
  </div>
</div>

## GitHubリポジトリ作成

<div class="guide-card">
  <h3>スマホ画面での操作</h3>
  <ol>
    <li>スマホのブラウザで <code>github.com</code> にログイン。</li>
    <li>右上の「+」アイコンをタップし、「New repository」を選択。</li>
    <li>Repository name に名前（例: <code>ai-mobile-app</code>）を入力。</li>
    <li>「Add a README file」にチェックを入れる（重要：AIがリポジトリを操作しやすくなる）。</li>
    <li>「Create repository」をタップ。</li>
  </ol>
</div>

## AIとの接続

<div class="guide-card">
  <h3>複数AIを同じGitHubで使う方法</h3>
  <p>AI間で直接の会話履歴は共有できません。そのため、<strong>GitHubリポジトリ自体を記憶装置として使います。</strong></p>
  <ul>
    <li>リポジトリのルートに <code>AGENTS.md</code> を作成し、AI共通のルール（「直接mainにpushしない」「テストしてからPRを出す」等）を記載します。</li>
    <li>各AI（Claude, Gemini, Codex）に「まずリポジトリの <code>AGENTS.md</code> と <code>README.md</code> を読んでから作業して」と指示します。</li>
    <li>これにより、どのAIに頼んでも一貫したルールで開発が継続します。</li>
  </ul>
</div>

## HTML/CSS作成

スマホでのタイピングは苦痛ですが、AIに任せれば問題ありません。

<div class="guide-card">
  <h3>プロンプト例</h3>
  <blockquote>
    「モダンなカードUIを使ったポートフォリオサイトのHTML/CSSを作成し、インラインCSSではなく `style.css` に分けてください。スマホファーストでレスポンシブにし、幅390pxで崩れないか必ず確認してください。完成したら `feature/portfolio-ui` ブランチを切ってPRを作成してください。」
  </blockquote>
</div>

## GitHubへの保存

<div class="guide-card">
  <h3>ブランチ / PR運用</h3>
  <table class="comparison-table">
    <tr>
      <th>操作</th>
      <th>誰がやるか</th>
      <th>スマホでのやりやすさ</th>
    </tr>
    <tr>
      <td>ブランチ作成</td>
      <td>AI（指示による）</td>
      <td><span class="indicator-yes">◎ 自動</span></td>
    </tr>
    <tr>
      <td>ファイル作成/編集</td>
      <td>AI（指示による）</td>
      <td><span class="indicator-yes">◎ 自動</span></td>
    </tr>
    <tr>
      <td>Pull Request作成</td>
      <td>AI（指示による）</td>
      <td><span class="indicator-yes">◎ 自動</span></td>
    </tr>
    <tr>
      <td>PRのレビュー・承認</td>
      <td>人間（スマホブラウザ）</td>
      <td><span class="indicator-partial">△ 画面が狭いが見れる</span></td>
    </tr>
    <tr>
      <td>マージ</td>
      <td>人間（スマホブラウザ）</td>
      <td><span class="indicator-yes">○ ボタンタップのみ</span></td>
    </tr>
  </table>
</div>

## 公開方法

<div class="highlight-box">
  GitHub Pagesを使えば、サーバー構築不要で無料公開できます。
</div>
<ol>
  <li>スマホのブラウザで対象リポジトリを開く。</li>
  <li>「Settings」タブ → 左メニュー「Pages」を開く。</li>
  <li>「Source」を <code>Deploy from a branch</code> にし、ブランチを <code>main</code>（または <code>gh-pages</code>）に設定して「Save」。</li>
  <li>数分後、<code>https://ユーザー名.github.io/リポジトリ名/</code> で公開完了！</li>
</ol>

## 初心者が迷いやすい点

<div class="guide-card">
  <ul>
    <li><strong>Q: エラーが出たらどうする？</strong><br>A: エラー画面をスクショしてAIに貼り付け、「このエラーを直して再度PRを出して」と指示するだけです。自分でコードを直す必要はありません。</li>
    <li><strong>Q: AIが途中で止まったら？</strong><br>A: 「続けて」「次はどうする？」と促します。プロンプトで「途中で確認せず最後まで自律実行して」と事前指示しておくのがコツです。</li>
    <li><strong>Q: 秘密情報（APIキー等）はどうする？</strong><br>A: リポジトリの <code>.env</code> に書き（絶対にコミットしない！）、AIには「APIキーは .env から読み込む実装にして」と指示します。</li>
  </ul>
</div>

## メリット

<div class="guide-card">
  <ul>
    <li>移動中やベッドの上など、<strong>いつでもどこでも開発が進められる</strong>。</li>
    <li>AIが書いたコードを読むことで、<strong>自然とプログラミングの学習になる</strong>。</li>
    <li>環境構築（Node.jsやPythonのインストールなど）で<strong>挫折することがない</strong>。</li>
  </ul>
</div>

## デメリット

<div class="guide-card">
  <ul>
    <li>スマホの画面サイズでは、複雑なコードの全体像や差分（Diff）を俯瞰しづらい。</li>
    <li>ブラウザの「検証ツール（DevTools）」が使えないため、細かなデザイン調整の指示が難しい。</li>
    <li>AIのコンテキスト制限（一度に読めるコード量）を超えると、プロジェクト全体の把握が難しくなる。</li>
  </ul>
</div>

## 費用

<table class="comparison-table">
  <tr>
    <th>ツール/サービス</th>
    <th>無料枠・料金（2026年8月時点）</th>
  </tr>
  <tr>
    <td>GitHub</td>
    <td>パブリック/プライベートリポジトリ無料</td>
  </tr>
  <tr>
    <td>GitHub Pages</td>
    <td>パブリックリポジトリなら完全無料</td>
  </tr>
  <tr>
    <td>Claude (Anthropic)</td>
    <td>無料枠あり / Pro: $20/月</td>
  </tr>
  <tr>
    <td>Gemini (Google)</td>
    <td>無料枠あり / Advanced: 2,900円/月</td>
  </tr>
  <tr>
    <td>ChatGPT / Codex</td>
    <td>無料枠あり / Plus: $20/月</td>
  </tr>
</table>
<p><small>※料金や無料枠は変更される可能性があります。必ず公式の最新情報を確認してください。</small></p>

## 各AIの強み・弱みと最も効率の良い構成

<div class="guide-card">
  <h3>AI比較表（スマホ完結開発の観点）</h3>
  <table class="comparison-table">
    <tr>
      <th>AI</th>
      <th>強み</th>
      <th>弱み</th>
    </tr>
    <tr>
      <td><strong>Claude Code</strong></td>
      <td>圧倒的なコード理解力、自律的なCLI操作、複雑なアーキテクチャ設計に強い。</td>
      <td>利用設定のハードルが少し高い場合がある。</td>
    </tr>
    <tr>
      <td><strong>Gemini / Jules</strong></td>
      <td>最新情報（Google検索）との連携、GCP等インフラ連携、超高速なレスポンス。</td>
      <td>極めて複雑なリファクタリングでたまに文脈を見失う。</td>
    </tr>
    <tr>
      <td><strong>OpenAI Codex</strong></td>
      <td>普及率の高さ、汎用的なスクリプト作成、API連携の確実さ。</td>
      <td>長大なコンテキスト維持がClaudeに劣る場合がある。</td>
    </tr>
  </table>

  <div class="highlight-box">
    <strong>💡 最も効率の良い構成（ベストプラクティス）</strong><br>
    ・<strong>設計と基盤構築:</strong> Claude Code に全体構成と <code>AGENTS.md</code> を作らせる。<br>
    ・<strong>機能追加とリサーチ:</strong> Gemini/Jules を使い、最新APIの調査と実装を高速で回す。<br>
    ・<strong>小規模スクリプト:</strong> Codex（ChatGPT）でサクッと生成する。
  </div>
</div>

## PCが必要になる場面

<div class="guide-card">
  <h3>スマホだけで完結できる範囲（できる / できない）</h3>
  <ul>
    <li><span class="indicator-yes">◎ できる:</span> HTML / CSS / JavaScript開発、静的サイト公開、PWA（Progressive Web App）開発、外部API連携、GitHub Actionsによる自動化、AIエージェントのスクリプト開発</li>
    <li><span class="indicator-partial">△ 難しい:</span> 複雑なデータベース設計の視覚的確認、大量のファイルの同時リファクタリング（画面が狭いため）</li>
    <li><span class="indicator-no">× できない（PC必須）:</span> iOS/Androidのネイティブアプリのローカルビルド（実機転送）、重いローカルDocker環境の立ち上げ、ブラウザのDevToolsを使ったミリ単位のCSSデバッグ</li>
  </ul>
</div>

## 最終的に何ができるか

<div class="guide-card">
  スマホとAIプロバイダ、そしてGitHubさえあれば、<strong>「アイデアを思いついたその日の通勤電車の中で、AIエージェントチームを編成してWebアプリを構築し、全世界にデプロイして公開する」</strong>という魔法のような体験が可能です。
  <br><br>
  コードを書くのはAI、テストするのもAI。あなたの役割は「プログラマー」から「プロダクトマネージャー」兼「AIチームの監督」へと進化します。
</div>

</div>
