:::html
<style>
  .jules-guide-container {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    color: #e2e8f0;
    line-height: 1.6;
  }
  .jules-guide-container h2 {
    color: #60a5fa;
    border-bottom: 2px solid #1e3a8a;
    padding-bottom: 0.5rem;
    margin-top: 2rem;
    font-size: 1.25rem;
  }
  .jules-guide-container h3 {
    color: #93c5fd;
    font-size: 1.1rem;
    margin-top: 1.5rem;
  }
  .highlight-card {
    background: linear-gradient(145deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 1.25rem;
    margin: 1.5rem 0;
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
  }
  .highlight-card p { margin-bottom: 0; }

  .feature-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    margin-top: 1rem;
  }
  .feature-tag {
    background: #1e3a8a;
    color: #bfdbfe;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.85rem;
    display: inline-flex;
    align-items: center;
  }

  .concept-card {
    background: #1e293b;
    border-left: 4px solid #60a5fa;
    padding: 1rem;
    margin: 1rem 0;
    border-radius: 0 8px 8px 0;
  }
  .concept-title {
    font-weight: bold;
    color: #60a5fa;
    margin-bottom: 0.5rem;
  }

  .flow-step {
    background: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
    padding: 1rem;
    margin: 0.5rem 0;
    display: flex;
    align-items: center;
    gap: 1rem;
  }
  .step-number {
    background: #3b82f6;
    color: white;
    width: 28px;
    height: 28px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: bold;
    flex-shrink: 0;
  }
  .step-arrow {
    text-align: center;
    color: #64748b;
    margin: 0.25rem 0;
  }

  .detail-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 1.25rem;
    margin: 1.5rem 0;
  }
  .detail-badge {
    background: #8b5cf6;
    color: white;
    padding: 0.25rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.8rem;
    font-weight: bold;
    display: inline-block;
    margin-bottom: 1rem;
  }

  .comparison-table {
    width: 100%;
    border-collapse: collapse;
    margin: 1.5rem 0;
    font-size: 0.9rem;
  }
  .comparison-table th, .comparison-table td {
    padding: 0.75rem;
    border: 1px solid #334155;
    text-align: left;
  }
  .comparison-table th {
    background: #1e293b;
    color: #93c5fd;
  }
  .status-good { color: #4ade80; font-weight: bold; }
  .status-warn { color: #facc15; font-weight: bold; }

  .warning-card {
    background: rgba(127, 29, 29, 0.2);
    border: 1px solid #7f1d1d;
    border-left: 4px solid #ef4444;
    padding: 1rem;
    border-radius: 0 8px 8px 0;
    margin: 1.5rem 0;
  }
  .warning-title {
    color: #f87171;
    font-weight: bold;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
  }

  ul { padding-left: 1.5rem; }
  li { margin-bottom: 0.5rem; }
  code {
    background: #334155;
    color: #e2e8f0;
    padding: 0.2rem 0.4rem;
    border-radius: 4px;
    font-family: monospace;
  }
</style>

<div class="jules-guide-container">

  <div class="highlight-card">
    <p>💡 <b>このガイドについて</b><br>
    このページでは、<b>GoogleのAIエージェント「Jules」</b>を活用し、スマホのブラウザだけで本格的なWebサイトを作って公開するまでの流れを解説します。</p>

    <div style="margin-top:1rem; font-weight:bold; color:#93c5fd;">この方法の特徴</div>
    <div class="feature-tags">
      <span class="feature-tag">✓ PC不要</span>
      <span class="feature-tag">✓ 無料で構築</span>
      <span class="feature-tag">✓ AIが自動でコード作成</span>
      <span class="feature-tag">✓ GitHub連携</span>
    </div>
  </div>

  <p>通常、ホームページを作るにはPCでコードを書き、サーバーを設定する必要があります。<br>
  しかし、<b>Google Jules</b>（非同期で動くAIエージェント）と<b>GitHub</b>を組み合わせれば、スマホからチャットで指示を出すだけで、AIが自動でコードを書き、設定し、公開まで準備してくれます。</p>

  <h2>基本概念と必要なサービス</h2>

  <div class="concept-card">
    <div class="concept-title">🐙 GitHub</div>
    <p>コードを保存する倉庫（<b>リポジトリ</b>）と、Web公開機能（<b>GitHub Pages</b>）を提供します。無料です。</p>
  </div>

  <div class="concept-card">
    <div class="concept-title">🤖 Jules</div>
    <p>GoogleのAIエージェント。あなたの代わりにGitHub内のコードを読み書きします。無料枠があります。</p>
  </div>

  <div class="concept-card">
    <div class="concept-title">Gemini と Jules の違い</div>
    <p><b>Gemini</b>はチャットで質問に答えるAIです。コードの書き方を教えてくれますが、保存するのはあなた自身です。<br>
    <b>Jules</b>は「AIエージェント」です。指示を出すと、クラウド上の環境で実際にコードを書き、GitHubに保存（Pull Request）する作業まで<b>すべて自動で代行</b>してくれます。</p>
  </div>

  <h2>スマホでの手順（全体の流れ）</h2>

  <div class="flow-step">
    <div class="step-number">1</div>
    <div><b>GitHubで空のリポジトリを作る</b></div>
  </div>
  <div class="step-arrow">↓</div>
  <div class="flow-step">
    <div class="step-number">2</div>
    <div><b>Jules.google.comを開いて連携</b></div>
  </div>
  <div class="step-arrow">↓</div>
  <div class="flow-step">
    <div class="step-number">3</div>
    <div><b>スマホからJulesに「サイトを作って」と指示</b></div>
  </div>
  <div class="step-arrow">↓</div>
  <div class="flow-step">
    <div class="step-number">4</div>
    <div><b>Julesがバックグラウンドでコード（HTML/CSS/JS等）を生成</b></div>
  </div>
  <div class="step-arrow">↓</div>
  <div class="flow-step">
    <div class="step-number">5</div>
    <div><b>提案されたPR（Pull Request）をマージする</b></div>
  </div>
  <div class="step-arrow">↓</div>
  <div class="flow-step">
    <div class="step-number">6</div>
    <div><b>GitHub Pagesを設定して公開！</b></div>
  </div>

  <h2>各ステップの詳しい解説</h2>

  <div class="detail-card">
    <div class="detail-badge">Step 1</div>
    <h3>GitHubリポジトリ作成</h3>
    <p>コードを置く場所を作ります。これが「リポジトリ」です。</p>
    <ul>
      <li>スマホのブラウザで<a href="https://github.com" target="_blank" style="color:#60a5fa;">GitHub</a>にアクセスし、アカウントを作成・ログインします。</li>
      <li>「＋」ボタンから「New repository」を選択します。</li>
      <li>名前（例: <code>my-website</code>）を付けます。</li>
      <li><b>Public（公開）</b>を選択します（※後で無料でWeb公開するため）。</li>
      <li>「Add a README file」にチェックを入れて作成します。</li>
    </ul>
  </div>

  <div class="concept-card">
    <div class="concept-title">Privateリポジトリとの接続について</div>
    <p>Julesは、自分だけが見られる<b>Privateリポジトリ</b>にも接続して作業させることができます。<br>
    ただし、今回利用する「GitHub Pages」で無料でWebサイトを公開するには、リポジトリを<b>Public（公開）</b>にする必要があります。見られて困る情報を入れないよう注意しましょう。</p>
  </div>

  <div class="detail-card">
    <div class="detail-badge">Step 2</div>
    <h3>JulesとGitHubを連携</h3>
    <p>AIがあなたのリポジトリを編集できるようにします。</p>
    <ul>
      <li>スマホから<a href="https://jules.google.com" target="_blank" style="color:#60a5fa;">jules.google.com</a>を開きます。</li>
      <li>Googleアカウントでログインします。</li>
      <li>「Connect GitHub」をタップし、先ほど作ったリポジトリ（<code>my-website</code>）へのアクセスを許可します。</li>
    </ul>
  </div>

  <div class="detail-card">
    <div class="detail-badge">Step 3 & 4</div>
    <h3>Julesに指示を出す（HTML/CSSの作成）</h3>
    <p>Julesの画面でリポジトリを選び、プロンプトを入力します。あとはAIにお任せです。</p>
    <div style="background:#1e293b; padding:1rem; border-radius:8px; border-left:3px solid #cbd5e1; font-style:italic; margin-bottom:1rem;">
      「自己紹介のホームページを作りたいです。トップページ(index.html)とスタイル(style.css)を作成し、ダークテーマでおしゃれなデザインにしてください。」
    </div>
    <p>指示を出すと、Julesはクラウド上の仮想マシンでコードを作成し、プレビュー計画（Plan）を提示します。承認すると、GitHubに<b>Pull Request（PR）</b>という形でコードの変更案が送信されます。</p>
  </div>

  <div class="detail-card">
    <div class="detail-badge">Step 5 & 6</div>
    <h3>承認して公開する（GitHubへの保存と公開）</h3>
    <ul>
      <li>GitHubに戻り、Julesから届いた「Pull Request」を開きます。</li>
      <li>内容に問題がなければ「<b>Merge pull request</b>」を押します（これでメインのコードに保存されます）。</li>
      <li>リポジトリの <code>Settings</code> > <code>Pages</code> を開きます。</li>
      <li>Sourceを「Deploy from a branch」にし、Branchを「main」にしてSaveします。</li>
      <li>数分待つと <code>https://[ユーザー名].github.io/my-website/</code> でサイトが公開されます！公開URLをシェアしましょう。</li>
    </ul>
  </div>

  <h2>初心者が迷いやすい点</h2>

  <div class="concept-card">
    <div class="concept-title">ブランチとPull Requestって何？</div>
    <p>Julesは直接本番（mainブランチ）を書き換えず、「こんな変更はどう？」という提案（Pull Request）用の作業場（ブランチ）を作ります。あなたがOKを出して「マージ」するまでは本番に反映されません。安全に確認できる仕組みです。</p>
  </div>

  <div class="concept-card">
    <div class="concept-title">修正・更新方法（指示通りにならない時）</div>
    <p>最初から完璧を目指さず、まずはベースを作り、後から「ここの色をピンクにして」「ここを2カラムにして」と追加でJulesに指示を出す（新しいPRを作ってもらう）のがコツです。ちょっとした文章の修正も、スマホからJulesにお願いするだけです。</p>
  </div>

  <h2>メリット・デメリット・費用</h2>

  <table class="comparison-table">
    <tr>
      <th>項目</th>
      <th>評価</th>
    </tr>
    <tr>
      <td><b>スマホだけで完結</b></td>
      <td><span class="status-good">◎</span> ブラウザだけで操作可能</td>
    </tr>
    <tr>
      <td><b>PCが必要か</b></td>
      <td><span class="status-good">完全に不要</span> （Julesがクラウドで作業するため）</td>
    </tr>
    <tr>
      <td><b>初期設定の簡単さ</b></td>
      <td><span class="status-warn">◯</span> GitHubの概念（リポジトリ等）の理解が少し必要</td>
    </tr>
    <tr>
      <td><b>デザインの自由度</b></td>
      <td><span class="status-good">◎</span> HTML/CSS/JSをフルに使えるため無限大</td>
    </tr>
    <tr>
      <td><b>非同期作業</b></td>
      <td><span class="status-good">◎</span> 指示を出して放置し、後で確認できる</td>
    </tr>
    <tr>
      <td><b>費用（無料/有料）</b></td>
      <td>基本 <b>無料</b>（Julesには無料枠があります。GitHub PagesもPublicなら無料です）</td>
    </tr>
  </table>

  <div class="warning-card">
    <div class="warning-title">
      ⚠️ セキュリティとAPIキー・秘密情報の注意
    </div>
    <p>パスワードやAPIキーなどの「秘密情報」を指示に含めないでください。Publicリポジトリに保存されると、世界中から見えてしまい大変危険です。どうしても必要な場合は、GitHub Secrets等の安全な仕組みを学ぶ必要があります。</p>
  </div>

  <h2>最終的に何ができるか</h2>
  <p>自分だけのオリジナルURL（GitHub Pages）を持った本格的なWebサイトが完成します。<br>
  ブログ、ポートフォリオ、お店の案内ページなど、AIに指示する内容次第でHTML/CSS/JavaScriptを駆使したどんなサイトにも成長させることができます。</p>

</div>
:::
