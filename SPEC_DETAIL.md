# 飲食店検索Webアプリ 詳細設計書 (SPEC_DETAIL.md)

## 2.1 ファイルごとの実装概要

---

### main.py

**役割**: FastAPIアプリケーションのエントリーポイント

**処理フロー**:
```
アプリ起動
    ↓
FastAPIインスタンス生成
    ↓
CORS設定
    ↓
ルーター登録 (/api/search)
    ↓
静的ファイル配信設定 (/static)
    ↓
ルートパス → index.html返却
```

**主要な関数/メソッド**:
| 関数名 | 説明 |
|--------|------|
| `create_app()` | FastAPIアプリ生成・設定 |
| `root()` | GET / → index.htmlを返却 |

**他ファイルとの連携**:
```
main.py
    ├── app/routers/search.py (ルーター登録)
    ├── app/config.py (設定読み込み)
    └── static/ (静的ファイル配信)
```

**実装時の注意点**:
- CORSはlocalhost:8000のみ許可
- 静的ファイルは/staticパスでマウント

---

### app/config.py

**役割**: アプリケーション設定・環境変数管理

**処理フロー**:
```
モジュール読み込み
    ↓
.envファイル読み込み (python-dotenv)
    ↓
Settings クラス定義 (pydantic-settings)
    ↓
設定値をクラス属性として公開
```

**主要な関数/メソッド**:
| クラス/関数名 | 説明 |
|--------------|------|
| `Settings` | 設定値を保持するPydanticモデル |
| `get_settings()` | Settingsインスタンスを返却（キャッシュ） |

**設定項目**:
| 項目 | 環境変数名 | デフォルト値 |
|------|-----------|-------------|
| Google APIキー | `GOOGLE_API_KEY` | （必須） |
| Geminiモデル名 | `GEMINI_MODEL` | `gemini-2.5-flash` |
| ログレベル | `LOG_LEVEL` | `DEBUG` |

**実装時の注意点**:
- APIキーが未設定の場合は起動時エラー
- pydantic-settingsでバリデーション

---

### app/logger.py

**役割**: ロギング設定

**処理フロー**:
```
setup_logger() 呼び出し
    ↓
ログフォーマット定義
    ↓
コンソールハンドラ設定 (StreamHandler)
    ↓
ファイルハンドラ設定 (FileHandler → logs/app.log)
    ↓
ルートロガーに両ハンドラ追加
```

**主要な関数/メソッド**:
| 関数名 | 説明 |
|--------|------|
| `setup_logger()` | ロガー初期化 |
| `get_logger(name)` | 名前付きロガー取得 |

**ログフォーマット**:
```
[2024-01-15 10:30:45,123] DEBUG - app.services.search - 処理名: 変数情報
```

**実装時の注意点**:
- logs/ディレクトリが存在しない場合は自動作成
- ファイルハンドラはRotatingFileHandler推奨（将来拡張）

---

### app/routers/search.py

**役割**: 検索APIエンドポイント定義

**処理フロー**:
```
POST /api/search リクエスト受信
    ↓
リクエストボディ検証 (SearchRequest)
    ↓
search_service.initial_search() 呼び出し
    ↓
InitialSearchResponseを返却

POST /api/search/detail リクエスト受信
    ↓
リクエストボディ検証 (ShopDetailRequest)
    ↓
search_service.detail_search() 呼び出し
    ↓
DetailSearchResponseを返却
```

**主要な関数/メソッド**:
| 関数名 | HTTPメソッド | パス | 説明 |
|--------|-------------|------|------|
| `initial_search()` | POST | /api/search | 初回検索（Step1-3） |
| `detail_search()` | POST | /api/search/detail | 個別店舗検索（Step4-5） |

**他ファイルとの連携**:
```
routers/search.py
    ├── services/search_service.py (ビジネスロジック)
    └── schemas/search.py (リクエスト/レスポンス型)
```

**実装時の注意点**:
- 例外発生時はHTTPException返却
- 処理時間をレスポンスヘッダに含める（任意）

---

### app/services/gemini_service.py

**役割**: Google AI (Gemini) API呼び出し

**処理フロー**:
```
[Grounding Search]
grounding_search(prompt) 呼び出し
    ↓
ログ出力: 処理開始、プロンプト、モデル名
    ↓
Gemini API呼び出し (google.search_retrieval ツール使用)
    ↓
レスポンス解析 (テキスト + grounding_metadata)
    ↓
結果返却

[AI判定（店舗名抽出・合致度判定）]
generate_content(prompt) 呼び出し
    ↓
ログ出力: 処理開始、プロンプト
    ↓
Gemini API呼び出し (ツールなし)
    ↓
レスポンス解析
    ↓
結果返却
```

**主要な関数/メソッド**:
| 関数名 | 説明 |
|--------|------|
| `__init__()` | Geminiクライアント初期化 |
| `grounding_search(prompt)` | Grounding Search実行（v1.1: dict返却に変更、テキスト+ソース） |
| `generate_content(prompt)` | 通常のAI生成（抽出・判定用） |
| `_parse_grounding_metadata(response)` | メタデータ解析 |

**Grounding Search設定**:
```python
tools = [
    Tool(google_search_retrieval=GoogleSearchRetrieval(
        dynamic_retrieval_config=DynamicRetrievalConfig(
            mode="MODE_DYNAMIC",
            dynamic_threshold=0.3
        )
    ))
]
```

**実装時の注意点**:
- APIキーはconfig.pyから取得
- レート制限対応（リトライロジック）
- タイムアウト設定（30秒目安）

**v1.1 変更内容**:
- `grounding_search()` の返却値を `str` から `dict` に変更
  - `{"text": str, "sources": List[dict]}` 形式で返却
  - `response.candidates[0].groundingMetadata.groundingChunks` から抽出
  - 各chunk.webから `uri` と `title` を取得
  - 防御的コーディング（hasattr チェック）でオプショナルフィールドに対応

---

### app/services/search_service.py

**役割**: 検索ビジネスロジック（全体フロー制御）

**処理フロー（初回検索）**:
```
initial_search(input_text) 呼び出し
    ↓
[Step1] 入力テキスト・プロンプト・モデル名を構造化
    ↓
[Step2] 初回グラウンディングサーチ
    - プロンプト生成: 「{input_text} に合う飲食店を10件教えてください」
    - gemini_service.grounding_search() 呼び出し
    ↓
[Step3] 店舗名抽出
    - 抽出プロンプト生成
    - gemini_service.generate_content() 呼び出し
    - JSON解析して店舗リスト取得
    ↓
InitialSearchResponse返却
```

**処理フロー（個別店舗検索）**:
```
detail_search(input_text, selected_shops) 呼び出し
    ↓
選択店舗を順次処理（並列ではなく順次）
    ↓
[Step4] 各店舗のグラウンディングサーチ
    - プロンプト生成: 「{shop_name} は {input_text} に合うお店ですか？詳細を教えてください」
    - gemini_service.grounding_search() 呼び出し
    ↓
[Step5] 合致度判定
    - 判定プロンプト生成
    - gemini_service.generate_content() 呼び出し
    - スコア(1-5)と理由を解析
    ↓
次の店舗へ（繰り返し）
    ↓
サマリー集計（平均スコア、最高/最低）
    ↓
DetailSearchResponse返却
```

**主要な関数/メソッド**:
| 関数名 | 説明 |
|--------|------|
| `initial_search(input_text)` | 初回検索（Step1-3） |
| `detail_search(input_text, selected_shops)` | 個別店舗検索（Step4-5） |
| `_build_initial_prompt(input_text)` | 初回検索プロンプト生成 |
| `_build_extraction_prompt(search_result)` | 店舗名抽出プロンプト生成 |
| `_build_shop_search_prompt(input_text, shop_name)` | 個別店舗検索プロンプト生成 |
| `_build_judgement_prompt(input_text, shop_result)` | 合致度判定プロンプト生成 |
| `_parse_shop_list(ai_response)` | 店舗リストJSON解析 |
| `_parse_judgement(ai_response)` | 判定結果解析 |
| `_calculate_summary(judgements)` | サマリー計算 |

**実装時の注意点**:
- 各処理開始時にログ出力（処理名、主要変数）
- 店舗検索は順次実行（並列不可）
- JSONパースエラー時のフォールバック処理

---

### app/schemas/search.py

**役割**: Pydanticスキーマ定義（リクエスト/レスポンス型）

**スキーマ一覧**:

```
SearchRequest
├── input_text: str

InitialSearchResponse
├── input_text: str
├── prompt: str
├── model_name: str
├── raw_response: str
├── grounding_metadata: dict | None
├── shop_list: ShopListData

ShopListData
├── prompt: str
├── shops: list[str]
├── raw_response: str

ShopDetailRequest
├── input_text: str
├── selected_shops: list[str]

DetailSearchResponse
├── shop_details: list[ShopDetailData]
├── judgements: list[JudgementData]
├── summary: SummaryData

ShopDetailData
├── shop_name: str
├── prompt: str
├── raw_response: str
├── grounding_metadata: dict | None
├── sources: list[SourceCitation]  # v1.1追加

JudgementData
├── shop_name: str
├── prompt: str
├── score: int  # 1-5
├── reason: str
├── raw_response: str

SummaryData
├── average_score: float
├── max_score_shop: str
├── min_score_shop: str
├── total_shops: int
├── sources: list[SourceCitation]  # v1.1追加（各店舗の詳細に含まれる）

SourceCitation (v1.1追加)
├── url: str                # 参照元URL
├── title: str | None       # ページタイトル（オプショナル）
```

**実装時の注意点**:
- scoreは1-5の範囲でバリデーション
- raw_responseは長文になる可能性（表示時に考慮）

---

### static/index.html

**役割**: フロントエンドUI構造

**HTML構造**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>飲食店検索 検証アプリ</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <header>
        <h1>飲食店検索 検証アプリ</h1>
    </header>

    <main>
        <!-- 入力セクション -->
        <section id="input-section">
            <textarea id="input-text" placeholder="検索条件を入力..."></textarea>
            <button id="search-btn">検索開始</button>
        </section>

        <!-- Step 1: 入力詳細 -->
        <section id="step1" class="step hidden">
            <h2>▼ Step 1: 入力詳細</h2>
            <div class="step-content">...</div>
        </section>

        <!-- Step 2: 初回サーチ結果 -->
        <section id="step2" class="step hidden">
            <h2>▼ Step 2: 初回サーチ結果</h2>
            <div class="step-content collapsible">...</div>
        </section>

        <!-- Step 3: 店舗リスト -->
        <section id="step3" class="step hidden">
            <h2>▼ Step 3: 店舗リスト</h2>
            <div class="step-content">
                <div id="shop-list"></div>
                <div class="selection-controls">
                    <button id="select-all">全選択</button>
                    <button id="deselect-all">全解除</button>
                </div>
            </div>
        </section>

        <!-- 個別店舗サーチボタン -->
        <section id="detail-search-section" class="hidden">
            <button id="detail-search-btn" disabled>個別店舗サーチ開始</button>
        </section>

        <!-- Step 4: 個別店舗サーチ -->
        <section id="step4" class="step hidden">
            <h2>▼ Step 4: 個別店舗サーチ</h2>
            <div class="step-content" id="shop-details"></div>
        </section>

        <!-- Step 5: 合致度判定 -->
        <section id="step5" class="step hidden">
            <h2>▼ Step 5: 合致度判定</h2>
            <div class="step-content" id="judgements"></div>
        </section>

        <!-- サマリー -->
        <section id="summary" class="step hidden">
            <h2>▼ サマリー</h2>
            <div class="step-content" id="summary-content"></div>
        </section>
    </main>

    <script src="/static/app.js"></script>
</body>
</html>
```

**実装時の注意点**:
- セマンティックHTML使用
- 初期状態で結果セクションは非表示（hidden）

---

### static/style.css

**役割**: スタイルシート

**主要スタイル**:
```css
/* レイアウト */
body { max-width: 900px; margin: 0 auto; padding: 20px; }
header h1 { text-align: center; }

/* 入力セクション */
#input-text { width: 100%; height: 100px; }
#search-btn { width: 100%; padding: 10px; }

/* ステップセクション */
.step { margin: 20px 0; border: 1px solid #ddd; }
.step h2 { cursor: pointer; padding: 10px; background: #f5f5f5; }
.step-content { padding: 15px; }
.hidden { display: none; }

/* 展開/折りたたみ */
.collapsible { max-height: 300px; overflow: hidden; }
.collapsible.expanded { max-height: none; }

/* 店舗リスト */
.shop-item { display: flex; align-items: center; padding: 8px; }
.shop-item input[type="checkbox"] { margin-right: 10px; }

/* 選択コントロール */
.selection-controls { margin-top: 10px; }
.selection-controls button { margin-right: 10px; }

/* 個別店舗サーチボタン */
#detail-search-btn { width: 100%; padding: 15px; font-size: 16px; }
#detail-search-btn:disabled { background: #ccc; cursor: not-allowed; }

/* 判定スコア表示 */
.score { font-size: 24px; font-weight: bold; }
.score-1 { color: #e74c3c; }
.score-2 { color: #e67e22; }
.score-3 { color: #f1c40f; }
.score-4 { color: #2ecc71; }
.score-5 { color: #27ae60; }

/* ローディング */
.loading { text-align: center; padding: 20px; }
.loading::after { content: "処理中..."; }

/* エラー表示 */
.error { color: #e74c3c; background: #ffeaea; padding: 10px; }

/* デバッグ情報 */
.debug-info { background: #f9f9f9; font-family: monospace; font-size: 12px; }
```

**実装時の注意点**:
- モバイル対応は不要（検証用途）
- スコアに応じた色分け表示

---

### static/app.js

**役割**: フロントエンドロジック

**処理フロー**:
```
[初回検索]
「検索開始」ボタンクリック
    ↓
debugLog("初回検索開始", { inputText })
    ↓
POST /api/search 呼び出し
    ↓
debugLog("初回検索結果取得", { status, responseSize })
    ↓
Step1 表示（入力詳細）
    ↓
Step2 表示（初回サーチ結果）
    ↓
Step3 表示（店舗リスト + チェックボックス）
    ↓
「個別店舗サーチ開始」ボタン有効化

[個別店舗検索]
「個別店舗サーチ開始」ボタンクリック
    ↓
選択された店舗リスト取得
    ↓
debugLog("個別店舗検索開始", { selectedShops })
    ↓
POST /api/search/detail 呼び出し
    ↓
debugLog("個別店舗検索結果取得", { status, responseSize })
    ↓
Step4 表示（各店舗のサーチ結果）
    ↓
Step5 表示（合致度判定）
    ↓
サマリー表示
```

**主要な関数**:
| 関数名 | 説明 |
|--------|------|
| `debugLog(processName, data)` | デバッグログ出力 |
| `initialSearch()` | 初回検索API呼び出し |
| `detailSearch()` | 個別店舗検索API呼び出し |
| `renderStep1(data)` | Step1表示 |
| `renderStep2(data)` | Step2表示 |
| `renderStep3(shops)` | Step3表示（チェックボックス生成） |
| `renderStep4(details)` | Step4表示（v1.1: ソースURL表示追加） |
| `renderStep5(judgements)` | Step5表示 |
| `renderSummary(summary)` | サマリー表示 |
| `renderSources(sources, containerId)` | ソースURL一覧表示（v1.1追加） |
| `getSelectedShops()` | 選択された店舗リスト取得 |
| `selectAll()` | 全選択 |
| `deselectAll()` | 全解除 |
| `toggleCollapsible(element)` | 展開/折りたたみ切り替え |
| `showLoading(sectionId)` | ローディング表示 |
| `showError(sectionId, message)` | エラー表示 |

**デバッグログ形式**:
```javascript
function debugLog(processName, data) {
    const timestamp = new Date().toISOString();
    console.log(`[${timestamp}] [${processName}]`, data);
}
```

**実装時の注意点**:
- fetch APIでバックエンド通信
- async/awaitで非同期処理
- エラー時も処理継続可能な設計

**v1.1 変更内容**:
- `renderSources()` 関数追加: ソースURL一覧を表示
  - 各ソースをリンクとして表示（新しいタブで開く）
  - タイトルが利用可能な場合は表示、なければURLを表示
  - ソースがない場合は「参照元URLなし」を表示
- `renderStep4()` 関数を拡張: 各店舗の詳細サーチ結果の下にソースURL表示

---

## 2.2 ソフトウェア画面構成の概要

---

### 画面1: メイン画面（単一ページ）

**目的**: 飲食店検索の全機能を提供する検証用画面

**レイアウト**:
```
+------------------------------------------------------------------+
|                    飲食店検索 検証アプリ                           |
+------------------------------------------------------------------+
|                                                                  |
| +--------------------------------------------------------------+ |
| | 検索条件を入力してください                                      | |
| | +----------------------------------------------------------+ | |
| | |                                                          | | |
| | |  [テキストエリア: 複数行入力可能]                          | | |
| | |                                                          | | |
| | +----------------------------------------------------------+ | |
| |                                                              | |
| | +----------------------------------------------------------+ | |
| | |                    [ 検索開始 ]                           | | |
| | +----------------------------------------------------------+ | |
| +--------------------------------------------------------------+ |
|                                                                  |
+------------------------------------------------------------------+
|  ▼ Step 1: 入力詳細                               [展開/折りたたみ]|
| +--------------------------------------------------------------+ |
| |  入力テキスト:                                                 | |
| |  「渋谷駅周辺でラーメンが美味しい店」                           | |
| |                                                              | |
| |  使用プロンプト:                                               | |
| |  「渋谷駅周辺でラーメンが美味しい店 に合う飲食店を10件...」      | |
| |                                                              | |
| |  モデル名: gemini-2.5-flash                               | |
| +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
|  ▼ Step 2: 初回サーチ結果                         [展開/折りたたみ]|
| +--------------------------------------------------------------+ |
| |  [Gemini生レスポンス]                                         | |
| |  渋谷駅周辺でラーメンが美味しいお店を10件ご紹介します...        | |
| |                                                              | |
| |  [グラウンディング情報]                                        | |
| |  - 検索クエリ: ...                                            | |
| |  - 参照URL: ...                                               | |
| +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
|  ▼ Step 3: 店舗リスト（詳細検索対象を選択）                       |
| +--------------------------------------------------------------+ |
| |  [✓] 1. 麺屋武蔵 渋谷店                                       | |
| |  [✓] 2. 一蘭 渋谷店                                           | |
| |  [✓] 3. 博多風龍 渋谷店                                        | |
| |  [✓] 4. 渋谷三丁目らーめん                                     | |
| |  [ ] 5. 天下一品 渋谷店  ← ユーザーが解除                      | |
| |  ...                                                          | |
| |                                                              | |
| |  [全選択] [全解除]                     選択中: 9件 / 10件      | |
| +--------------------------------------------------------------+ |
|                                                                  |
| +--------------------------------------------------------------+ |
| |              [ 個別店舗サーチ開始 ]                            | |
| +--------------------------------------------------------------+ |
|                                                                  |
+------------------------------------------------------------------+
|  ▼ Step 4: 個別店舗サーチ                         [展開/折りたたみ]|
| +--------------------------------------------------------------+ |
| |  [1/9] 麺屋武蔵 渋谷店                            処理中...    | |
| |  プロンプト: 「麺屋武蔵 渋谷店 は 渋谷駅周辺で...」             | |
| |  結果: ...                                                    | |
| |  グラウンディング情報: ...                                     | |
| |  ------------------------------------------------------------ | |
| |  [2/9] 一蘭 渋谷店                                 完了 ✓     | |
| |  ...                                                          | |
| +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
|  ▼ Step 5: 合致度判定                                            |
| +--------------------------------------------------------------+ |
| |  [1] 麺屋武蔵 渋谷店                                          | |
| |      スコア: [4] ████████░░ ほぼ合致も一部相違あり             | |
| |      理由: ラーメン店として条件を満たしているが、               | |
| |            「美味しい」の主観評価に依存...                      | |
| |  ------------------------------------------------------------ | |
| |  [2] 一蘭 渋谷店                                              | |
| |      スコア: [5] ██████████ 完全に合致                        | |
| |      理由: 渋谷駅徒歩3分、ラーメン専門店、                      | |
| |            口コミ評価も高く条件を完全に満たす                   | |
| |  ...                                                          | |
| +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
|  ▼ サマリー                                                      |
| +--------------------------------------------------------------+ |
| |  検索条件: 「渋谷駅周辺でラーメンが美味しい店」                  | |
| |  対象店舗数: 9件                                               | |
| |                                                              | |
| |  平均スコア: 3.8 / 5                                          | |
| |  最高評価: 一蘭 渋谷店 (5/5)                                   | |
| |  最低評価: ○○○○ (2/5)                                        | |
| |                                                              | |
| |  スコア分布:                                                   | |
| |  5: ██████ 2件                                                | |
| |  4: ████████████ 4件                                          | |
| |  3: ██████ 2件                                                | |
| |  2: ███ 1件                                                   | |
| |  1: 0件                                                       | |
| +--------------------------------------------------------------+ |
+------------------------------------------------------------------+
```

**各要素の説明**:

| 要素 | 説明 |
|------|------|
| テキストエリア | 飲食店検索条件の自由入力（複数行対応） |
| 検索開始ボタン | Step1-3を実行、結果表示後は「個別店舗サーチ開始」が有効化 |
| Step 1-5 | 各ステップの詳細表示エリア（展開/折りたたみ可能） |
| チェックボックス | 詳細検索対象の店舗を選択/解除 |
| 全選択/全解除 | 一括選択操作 |
| 個別店舗サーチ開始ボタン | 選択店舗のStep4-5を実行 |
| サマリー | 全体の統計情報（平均スコア、分布など） |

**ナビゲーション**:
- 単一ページ構成のため、ページ遷移なし
- 各ステップのヘッダークリックで展開/折りたたみ
- スクロールで各セクションを確認

**状態遷移**:
```
[初期状態]
    ↓ 「検索開始」クリック
[Step1-3 表示、個別店舗サーチボタン有効化]
    ↓ 店舗選択 → 「個別店舗サーチ開始」クリック
[Step4-5 表示、サマリー表示]
    ↓ 新しい検索条件入力 → 「検索開始」クリック
[リセット、新しいStep1-3 表示]
```
