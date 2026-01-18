# 飲食店検索Webアプリ 仕様書整合性確認 (SPEC_VALIDATION.md)

## 4.1 整合性確認の目的と方法

### 目的
SPEC.md, SPEC_DETAIL.md, SPEC_LOGIC.md の3つの仕様書の整合性を確認し、コーディング前に設計の矛盾を解消する。

### 確認項目
1. 機能整合性
2. データモデル整合性
3. ファイル構成整合性
4. 技術スタック整合性
5. セキュリティ・保守性整合性

---

## 4.2 機能整合性確認表

| # | 機能 | SPEC.md | SPEC_DETAIL.md | SPEC_LOGIC.md | 整合性 | 備考 |
|---|------|---------|----------------|---------------|--------|------|
| 1 | テキスト入力 | ✅ 1.3 主要機能1 | ✅ index.html | - | ✅ | |
| 2 | 初回Grounding Search | ✅ 1.3 主要機能2 | ✅ search_service.py | ✅ 3.0, 3.1 | ✅ | |
| 3 | 店舗名抽出 | ✅ 1.3 主要機能3 | ✅ search_service.py | ✅ 3.2 | ✅ | Pydanticスキーマ使用 |
| 4 | 店舗選択（チェックボックス） | ✅ 1.3 主要機能3 | ✅ index.html, app.js | - | ✅ | |
| 5 | 個別店舗サーチボタン | ✅ 1.6 UI | ✅ index.html | - | ✅ | |
| 6 | 個別店舗サーチ（順次） | ✅ 1.3 主要機能4 | ✅ search_service.py | ✅ 3.4 | ✅ | |
| 7 | 合致度判定（5段階） | ✅ 1.3 主要機能5 | ✅ search_service.py | ✅ 3.3 | ✅ | Pydanticスキーマ使用 |
| 8 | サマリー表示 | ✅ 1.3, 1.6 | ✅ app.js | ✅ 3.4 | ✅ | |
| 9 | ログ出力（バックエンド） | ✅ 1.9 | ✅ logger.py | ✅ 3.4 | ✅ | |
| 10 | ログ出力（フロントエンド） | ✅ 1.9 | ✅ app.js | ✅ 3.6 | ✅ | |

---

## 4.3 データモデル整合性確認表

| # | エンティティ/スキーマ | SPEC.md | SPEC_DETAIL.md | SPEC_LOGIC.md | 整合性 | 備考 |
|---|----------------------|---------|----------------|---------------|--------|------|
| 1 | SearchRequest | ✅ 1.4 | ✅ schemas/search.py | - | ✅ | |
| 2 | InitialSearchResponse | ✅ 1.4 | ✅ schemas/search.py | - | ✅ | |
| 3 | ShopListResponse/ShopListData | ✅ 1.4 | ✅ schemas/search.py | ✅ 3.2 ShopListSchema | ✅ | |
| 4 | ShopDetailRequest | ✅ 1.4 | ✅ schemas/search.py | - | ✅ | |
| 5 | ShopDetailSearchResponse | ✅ 1.4 | ✅ schemas/search.py | - | ✅ | |
| 6 | MatchJudgementResponse/JudgementData | ✅ 1.4 | ✅ schemas/search.py | ✅ 3.3 JudgementSchema | ✅ | |
| 7 | SummaryData | ✅ 1.4 | ✅ schemas/search.py | ✅ 3.4 | ✅ | |

---

## 4.4 ファイル構成整合性確認表

| # | ファイル | SPEC.md | SPEC_DETAIL.md | 行数目安 | 800行制約 | 整合性 |
|---|---------|---------|----------------|----------|-----------|--------|
| 1 | main.py | ✅ 1.7 | ✅ 2.1 | ~100行 | ✅ | ✅ |
| 2 | app/config.py | ✅ 1.7 | ✅ 2.1 | ~50行 | ✅ | ✅ |
| 3 | app/logger.py | ✅ 1.7 | ✅ 2.1 | ~80行 | ✅ | ✅ |
| 4 | app/routers/search.py | ✅ 1.7 | ✅ 2.1 | ~150行 | ✅ | ✅ |
| 5 | app/services/gemini_service.py | ✅ 1.7 | ✅ 2.1 | ~200行 | ✅ | ✅ |
| 6 | app/services/search_service.py | ✅ 1.7 | ✅ 2.1 | ~250行 | ✅ | ✅ |
| 7 | app/schemas/search.py | ✅ 1.7 | ✅ 2.1 | ~100行 | ✅ | ✅ |
| 8 | static/index.html | ✅ 1.7 | ✅ 2.1, 2.2 | ~150行 | ✅ | ✅ |
| 9 | static/style.css | ✅ 1.7 | ✅ 2.1 | ~150行 | ✅ | ✅ |
| 10 | static/app.js | ✅ 1.7 | ✅ 2.1 | ~300行 | ✅ | ✅ |

---

## 4.5 技術スタック整合性確認表

| # | 技術 | SPEC.md | SPEC_DETAIL.md | SPEC_LOGIC.md | 整合性 | 備考 |
|---|------|---------|----------------|---------------|--------|------|
| 1 | Python 3.11+ | ✅ 1.2 | ✅ 全ファイル | ✅ | ✅ | |
| 2 | FastAPI | ✅ 1.2 | ✅ main.py, routers | - | ✅ | |
| 3 | google-genai | ✅ 1.2 | ✅ gemini_service.py | ✅ 3.0 | ✅ | 新SDK使用 |
| 4 | Pydantic | ✅ 1.2 | ✅ schemas/search.py | ✅ 3.2, 3.3 | ✅ | JSON出力スキーマ |
| 5 | python-dotenv | ✅ 1.2 | ✅ config.py | - | ✅ | |
| 6 | HTML + Vanilla JS | ✅ 1.2 | ✅ static/ | ✅ 3.6 | ✅ | |
| 7 | Python logging | ✅ 1.2 | ✅ logger.py | ✅ 3.4 | ✅ | |

---

## 4.6 セキュリティ・保守性整合性確認表

| # | 項目 | SPEC.md | SPEC_DETAIL.md | SPEC_LOGIC.md | 整合性 | 備考 |
|---|------|---------|----------------|---------------|--------|------|
| 1 | APIキー保護（.env） | ✅ 1.9 | ✅ config.py | - | ✅ | |
| 2 | 入力検証（Pydantic） | ✅ 1.9 | ✅ schemas/search.py | ✅ 3.2, 3.3 | ✅ | |
| 3 | CORS設定 | ✅ 1.9 | ✅ main.py | - | ✅ | |
| 4 | バックエンドログ | ✅ 1.9 | ✅ logger.py | ✅ 3.4 | ✅ | |
| 5 | フロントエンドログ | ✅ 1.9 | ✅ app.js | ✅ 3.6 | ✅ | |
| 6 | エラーハンドリング | ✅ 1.6 | ✅ routers/search.py | ✅ 3.5 | ✅ | リトライ含む |
| 7 | API間隔制御（レート制限） | ✅ 1.1 | ✅ search_service.py | ✅ 3.4 | ✅ | 500ms待機 |

---

## 4.7 API エンドポイント整合性確認表

| # | エンドポイント | SPEC.md | SPEC_DETAIL.md | 整合性 | 備考 |
|---|---------------|---------|----------------|--------|------|
| 1 | POST /api/search | ✅ 1.8 | ✅ routers/search.py | ✅ | 初回検索（Step1-3） |
| 2 | POST /api/search/detail | ✅ 1.8 | ✅ routers/search.py | ✅ | 個別店舗検索（Step4-5） |
| 3 | GET / | - | ✅ main.py | ✅ | index.html返却 |
| 4 | /static/* | ✅ 1.7 | ✅ main.py | ✅ | 静的ファイル配信 |

---

## 4.8 修正サマリー

### 修正済み項目

| # | 修正箇所 | 修正前 | 修正後 | 修正理由 |
|---|---------|--------|--------|----------|
| 1 | SPEC.md 1.2 | google-generativeai | google-genai | 新SDKに統一 |
| 2 | SPEC_LOGIC.md 3.0 | なし | 基本実装パターン追加 | 新SDK使用方法の明示 |
| 3 | SPEC_LOGIC.md 3.2 | 正規表現JSONパース | Pydanticスキーマ使用 | 構造化出力の確実性向上 |
| 4 | SPEC_LOGIC.md 3.3 | 正規表現JSONパース | Pydanticスキーマ使用 | 構造化出力の確実性向上 |

### 不整合なし
- 全機能が3つの仕様書で一致
- データモデルが統一的に定義
- ファイル構成に矛盾なし
- 技術スタックが一貫

---

## 4.9 最終確認チェックリスト

- [x] すべての機能が3つの仕様書で一致
- [x] すべてのエンティティ/スキーマが定義・説明されている
- [x] ファイル構成が800行制約を守っている
- [x] 技術スタックが全ファイルで一貫している
- [x] セキュリティ対策が全フェーズで説明されている
- [x] APIエンドポイントが明確に定義されている
- [x] Google AI SDK（google-genai）の使用方法が明確に記載
- [x] Pydanticスキーマによる構造化出力が設計されている
- [x] ログ出力タイミング・フォーマットが統一されている
- [x] エラーハンドリング・リトライロジックが設計されている

---

## 4.10 コーディング前最終承認

上記の整合性確認により、以下を確認しました：

1. **3つの仕様書間に不整合がない**
2. **Google AI SDK（google-genai）の実装パターンが明確**
3. **Pydanticスキーマによる構造化出力が設計済み**
4. **全ファイル800行制約を満たす設計**

**ステータス**: ✅ コーディング準備完了
