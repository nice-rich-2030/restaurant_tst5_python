# 飲食店検索Webアプリ ロジック・アルゴリズム詳細設計書 (SPEC_LOGIC.md)

本アプリケーションで性能・品質を決める重要なロジックを詳細に設計します。

---

## 3.0 Google AI SDK 基本実装パターン

### Grounding Search（Google検索連携）

Google Grounding Searchを使用する際の基本コードパターン:

```python
from google import genai
from google.genai import types

# クライアント初期化
client = genai.Client()

# Grounding Tool設定
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

# 設定
config = types.GenerateContentConfig(
    tools=[grounding_tool]
)

# API呼び出し
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config=config,
)

# 結果取得
result_text = response.text
```

### JSON形式レスポンス（構造化出力）

AIレスポンスをJSON形式で取得する際の基本コードパターン:

```python
from google import genai
from pydantic import BaseModel, Field
from typing import List, Optional

# レスポンススキーマ定義（Pydantic）
class ShopList(BaseModel):
    shops: List[str] = Field(description="抽出された店舗名のリスト")

class JudgementResult(BaseModel):
    score: int = Field(description="合致度スコア（1-5）")
    reason: str = Field(description="判定理由")

# クライアント初期化
client = genai.Client()

# API呼び出し（JSON出力指定）
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents=prompt,
    config={
        "response_mime_type": "application/json",
        "response_json_schema": ShopList.model_json_schema(),
    },
)

# Pydanticモデルで検証・パース
result = ShopList.model_validate_json(response.text)
```

### 使用モデル
- **モデル名**: `gemini-2.5-flash`
- **選定理由**: Grounding Search対応、高速応答

---

## 3.1 プロンプト設計（Grounding Search用）

### 背景
Google Grounding Searchの検索精度は、プロンプトの設計に大きく依存します。適切なプロンプトにより、関連性の高い飲食店情報を取得できます。

### 提案するアルゴリズム

#### 初回検索プロンプト（10件取得）
```
入力: input_text（ユーザー入力）
出力: prompt（Grounding Search用プロンプト）

アルゴリズム:
1. ベーステンプレートを定義
   template = """
   以下の条件に合う飲食店を10件、具体的な店舗名と簡単な説明とともに教えてください。

   検索条件: {input_text}

   回答形式:
   1. [店舗名]: [簡単な説明（所在地、特徴など）]
   2. [店舗名]: [簡単な説明]
   ...
   """

2. input_textをテンプレートに埋め込み
   prompt = template.format(input_text=input_text)

3. promptを返却
```

#### 個別店舗検索プロンプト
```
入力: input_text, shop_name
出力: prompt（Grounding Search用プロンプト）

アルゴリズム:
1. ベーステンプレートを定義
   template = """
   「{shop_name}」について、以下の観点から詳細情報を教えてください。

   ユーザーの検索条件: {input_text}

   調査項目:
   - 店舗の正式名称と所在地
   - 提供している料理・メニューの特徴
   - 価格帯
   - 営業時間
   - 口コミ・評判
   - 検索条件との関連性
   """

2. パラメータを埋め込み
   prompt = template.format(shop_name=shop_name, input_text=input_text)

3. promptを返却
```

### 特徴（洗練されたポイント）
- **構造化された回答形式の指定**: AIに番号付きリストで回答させることで、後続の店舗名抽出が容易
- **検索条件の明示**: ユーザーの元の要求を明示することで、関連性の高い情報を取得
- **調査項目の具体化**: 合致度判定に必要な情報を網羅的に取得

### パフォーマンス目標
- プロンプト生成: 1ms以下
- Grounding Search応答: 5秒以内（API依存）

---

## 3.2 店舗名抽出アルゴリズム

### 背景
Grounding Searchの結果テキストから、正確に10件の店舗名を抽出する必要があります。Pydanticスキーマを使用した構造化出力により、確実なJSON形式での取得を実現します。

### Pydanticスキーマ定義

```python
from pydantic import BaseModel, Field
from typing import List

class ShopListSchema(BaseModel):
    """店舗名抽出結果のスキーマ"""
    shops: List[str] = Field(
        description="抽出された飲食店の店舗名リスト（最大10件）"
    )
```

### 提案するアルゴリズム

```
入力: search_result（Grounding Search結果テキスト）
出力: shops（店舗名リスト、最大10件）

アルゴリズム:

1. 抽出プロンプトを生成
   extraction_prompt = """
   以下のテキストから、飲食店の店舗名を抽出してください。
   最大10件まで抽出してください。

   テキスト:
   {search_result}

   注意:
   - 店舗名のみを抽出（説明文は含めない）
   - 「〇〇店」のように店舗を特定できる形式で
   - 重複がある場合は除去
   """

2. Gemini API呼び出し（構造化出力）
   response = client.models.generate_content(
       model="gemini-2.5-flash",
       contents=extraction_prompt,
       config={
           "response_mime_type": "application/json",
           "response_json_schema": ShopListSchema.model_json_schema(),
       },
   )

3. Pydanticでパース・検証
   try:
       result = ShopListSchema.model_validate_json(response.text)
       shops = result.shops
   except ValidationError:
       # フォールバック: 行単位で抽出
       shops = _fallback_extraction(response.text)

4. 店舗名のクリーニング
   cleaned_shops = []
   for shop in shops[:10]:
       # 番号・記号の除去
       shop = re.sub(r'^[\d\.\)\-\s]+', '', shop)
       # 前後の空白除去
       shop = shop.strip()
       if shop and shop not in cleaned_shops:
           cleaned_shops.append(shop)

5. cleaned_shopsを返却（最大10件）

フォールバック関数:
def _fallback_extraction(text):
    """行単位で店舗名らしき文字列を抽出"""
    shops = []
    lines = text.split('\n')
    for line in lines:
        # 「1. 店舗名」形式を検出
        match = re.match(r'^[\d]+[\.\)]\s*(.+?)[:：\-]', line)
        if match:
            shops.append(match.group(1).strip())
        # 「・店舗名」形式を検出
        elif line.strip().startswith('・'):
            shop = line.strip()[1:].split(':')[0].split('：')[0]
            shops.append(shop.strip())
    return shops[:10]
```

### 特徴（洗練されたポイント）
- **Pydanticスキーマ指定**: `response_json_schema`で構造化出力を保証
- **型安全なパース**: `model_validate_json`で検証とパースを一括実行
- **フォールバック処理**: スキーマ検証失敗時のリカバリ
- **重複除去・クリーニング**: 同一店舗の重複登録を防止

### パフォーマンス目標
- 抽出処理全体: 3秒以内（API呼び出し含む）
- JSONパース・クリーニング: 10ms以下

---

## 3.3 合致度判定アルゴリズム

### 背景
各店舗のサーチ結果が、ユーザーの検索条件にどの程度合致するかを5段階で判定します。Pydanticスキーマを使用した構造化出力により、判定の一貫性と説明可能性を確保します。

### Pydanticスキーマ定義

```python
from pydantic import BaseModel, Field
from typing import Literal

class JudgementSchema(BaseModel):
    """合致度判定結果のスキーマ"""
    score: Literal[1, 2, 3, 4, 5] = Field(
        description="合致度スコア（1:まったく合致しない ～ 5:完全に合致）"
    )
    reason: str = Field(
        description="判定理由（100文字以内）"
    )
```

### 提案するアルゴリズム

```
入力: input_text, shop_name, shop_search_result
出力: { score: int(1-5), reason: string }

アルゴリズム:

1. 判定プロンプトを生成
   judgement_prompt = """
   以下の店舗情報が、ユーザーの検索条件にどの程度合致するか判定してください。

   【検索条件】
   {input_text}

   【店舗名】
   {shop_name}

   【店舗情報】
   {shop_search_result}

   【判定基準】
   5: 完全に合致 - 検索条件のすべての要素を満たしている
   4: ほぼ合致も一部相違あり - 主要な条件を満たすが、一部不明または相違がある
   3: 半分程度合致 - 条件の約半分を満たす
   2: 一部合致もほぼ相違 - 一部のみ該当し、多くの条件を満たさない
   1: まったく合致しない - 検索条件とほぼ無関係
   """

2. Gemini API呼び出し（構造化出力）
   response = client.models.generate_content(
       model="gemini-2.5-flash",
       contents=judgement_prompt,
       config={
           "response_mime_type": "application/json",
           "response_json_schema": JudgementSchema.model_json_schema(),
       },
   )

3. Pydanticでパース・検証
   try:
       result = JudgementSchema.model_validate_json(response.text)
       score = result.score
       reason = result.reason
   except ValidationError:
       # フォールバック: デフォルト値
       score = 3
       reason = f"判定結果のパースに失敗しました。生レスポンス: {response.text[:100]}..."

4. { score, reason } を返却
```

### 判定基準の詳細

| スコア | 判定 | 基準例 |
|--------|------|--------|
| 5 | 完全に合致 | 地域、料理ジャンル、特徴すべてが条件と一致 |
| 4 | ほぼ合致 | 主要条件は満たすが、営業時間や一部詳細が不明 |
| 3 | 半分程度 | 料理ジャンルは合うが、地域が若干異なるなど |
| 2 | 一部合致 | 同じ地域だが、料理ジャンルが異なる |
| 1 | まったく合致しない | 地域も料理も検索条件と無関係 |

### 特徴（洗練されたポイント）
- **Pydanticスキーマ指定**: `response_json_schema`で構造化出力を保証
- **Literal型でスコア制限**: 1-5の範囲を型レベルで保証
- **明確な判定基準**: 5段階の基準を具体的に記述し、AIの判定ブレを軽減
- **型安全なパース**: `model_validate_json`で検証とパースを一括実行

### パフォーマンス目標
- 1店舗あたりの判定: 3秒以内
- 10店舗の判定: 30秒以内（順次処理のため）

---

## 3.4 順次処理制御（店舗検索ループ）

### 背景
10件の店舗を並列ではなく順次処理する要件があります。API呼び出し間隔の制御と、進捗表示のための設計が必要です。

### 提案するアルゴリズム

```
入力: input_text, selected_shops（選択された店舗リスト）
出力: { shop_details: [], judgements: [], summary: {} }

アルゴリズム:

1. 結果格納用のリストを初期化
   shop_details = []
   judgements = []

2. 選択店舗を順次処理
   for index, shop_name in enumerate(selected_shops):

       # ログ出力（処理開始）
       logger.debug(f"個別店舗サーチ開始: shop={shop_name}, index={index+1}/{len(selected_shops)}")

       # Step4: 個別店舗のGrounding Search
       shop_prompt = _build_shop_search_prompt(input_text, shop_name)
       shop_result = gemini_service.grounding_search(shop_prompt)

       shop_details.append({
           "shop_name": shop_name,
           "prompt": shop_prompt,
           "raw_response": shop_result.text,
           "grounding_metadata": shop_result.metadata
       })

       # ログ出力（サーチ完了）
       logger.debug(f"個別店舗サーチ完了: shop={shop_name}, response_len={len(shop_result.text)}")

       # Step5: 合致度判定
       judgement = _judge_match(input_text, shop_name, shop_result.text)
       judgements.append(judgement)

       # ログ出力（判定完了）
       logger.debug(f"合致度判定完了: shop={shop_name}, score={judgement['score']}")

       # API呼び出し間隔（レート制限対策）
       if index < len(selected_shops) - 1:
           time.sleep(0.5)  # 500ms待機

3. サマリー計算
   summary = _calculate_summary(judgements)

4. 結果を返却
   return {
       "shop_details": shop_details,
       "judgements": judgements,
       "summary": summary
   }
```

### サマリー計算

```
入力: judgements（判定結果リスト）
出力: summary

アルゴリズム:
1. スコアの集計
   scores = [j["score"] for j in judgements]

2. 統計値計算
   summary = {
       "average_score": round(sum(scores) / len(scores), 2),
       "max_score_shop": max(judgements, key=lambda x: x["score"])["shop_name"],
       "min_score_shop": min(judgements, key=lambda x: x["score"])["shop_name"],
       "total_shops": len(judgements),
       "score_distribution": {
           5: scores.count(5),
           4: scores.count(4),
           3: scores.count(3),
           2: scores.count(2),
           1: scores.count(1)
       }
   }

3. summaryを返却
```

### 特徴（洗練されたポイント）
- **順次処理の明示**: forループで1店舗ずつ処理（並列禁止）
- **API間隔制御**: 500ms待機でレート制限回避
- **詳細ログ**: 各処理開始・完了時にログ出力
- **サマリー計算**: 統計的な概要を提供

### パフォーマンス目標
- 1店舗あたり: 約6-10秒（Search 3秒 + 判定 3秒 + 待機 0.5秒）
- 10店舗: 約60-100秒
- 選択店舗数に応じてスケール

---

## 3.5 エラーハンドリング・リトライ

### 背景
外部API（Gemini）への依存があるため、ネットワークエラーやAPIエラーへの対応が必要です。

### 提案するアルゴリズム

```
リトライ設定:
MAX_RETRIES = 3
RETRY_DELAY = [1, 2, 4]  # 秒（指数バックオフ）

関数: api_call_with_retry(func, *args, **kwargs)

アルゴリズム:
1. リトライループ
   for attempt in range(MAX_RETRIES):
       try:
           result = func(*args, **kwargs)
           return result

       except RateLimitError:
           # レート制限: 長めに待機してリトライ
           if attempt < MAX_RETRIES - 1:
               wait_time = RETRY_DELAY[attempt] * 2
               logger.warning(f"レート制限検出。{wait_time}秒後にリトライ...")
               time.sleep(wait_time)
           else:
               raise

       except (TimeoutError, ConnectionError):
           # 接続エラー: 通常のリトライ
           if attempt < MAX_RETRIES - 1:
               wait_time = RETRY_DELAY[attempt]
               logger.warning(f"接続エラー。{wait_time}秒後にリトライ...")
               time.sleep(wait_time)
           else:
               raise

       except APIError as e:
           # APIエラー: ログ出力して例外を再送出
           logger.error(f"APIエラー: {e}")
           raise

2. 最終的に失敗した場合
   raise MaxRetriesExceededError(f"{MAX_RETRIES}回のリトライ後も失敗")
```

### エラー種別と対応

| エラー種別 | 対応 | リトライ |
|-----------|------|----------|
| RateLimitError | 長時間待機後リトライ | ○ |
| TimeoutError | 短時間待機後リトライ | ○ |
| ConnectionError | 短時間待機後リトライ | ○ |
| APIError (4xx) | エラーログ出力、処理中断 | × |
| JSONパースエラー | フォールバック処理 | × |

### 特徴（洗練されたポイント）
- **指数バックオフ**: リトライ間隔を段階的に延長
- **エラー種別に応じた対応**: レート制限は長時間待機
- **最大リトライ回数制限**: 無限ループ防止

---

## 3.6 フロントエンドデバッグログ

### 背景
検証用途のため、フロントエンドでのAPI呼び出し状況を詳細に確認できる必要があります。

### 提案するアルゴリズム

```javascript
// ログ出力関数
function debugLog(processName, data) {
    const timestamp = new Date().toISOString();
    const logEntry = {
        timestamp,
        process: processName,
        data: summarizeData(data)
    };

    // コンソール出力（色分け）
    console.log(
        `%c[${timestamp}] [${processName}]`,
        'color: #2196F3; font-weight: bold;',
        logEntry.data
    );
}

// データ要約（長文を省略）
function summarizeData(data) {
    if (typeof data === 'string' && data.length > 200) {
        return data.substring(0, 200) + '... (truncated)';
    }
    if (typeof data === 'object') {
        return JSON.stringify(data, (key, value) => {
            if (typeof value === 'string' && value.length > 100) {
                return value.substring(0, 100) + '...';
            }
            return value;
        }, 2);
    }
    return data;
}

// 使用例
debugLog('初回検索API呼び出し', { endpoint: '/api/search', body: requestBody });
debugLog('初回検索API結果取得', { status: response.status, dataSize: JSON.stringify(data).length });
```

### ログ出力タイミング

| タイミング | processName | data例 |
|-----------|-------------|--------|
| 初回検索開始 | `初回検索API呼び出し` | `{ endpoint, body }` |
| 初回検索完了 | `初回検索API結果取得` | `{ status, dataSize }` |
| Step1表示 | `Step1表示開始` | `{ inputText }` |
| Step2表示 | `Step2表示開始` | `{ responseLength }` |
| Step3表示 | `Step3表示開始` | `{ shopCount }` |
| 店舗選択変更 | `店舗選択変更` | `{ selectedCount, totalCount }` |
| 個別検索開始 | `個別検索API呼び出し` | `{ selectedShops }` |
| 個別検索完了 | `個別検索API結果取得` | `{ status, shopCount }` |
| Step4表示 | `Step4表示開始` | `{ shopIndex, shopName }` |
| Step5表示 | `Step5表示開始` | `{ shopName, score }` |
| サマリー表示 | `サマリー表示` | `{ averageScore, totalShops }` |

---

## 洗練度チェックリスト

- [x] プロンプト設計が検索精度向上に寄与
- [x] JSONパースのフォールバック処理が実装
- [x] 合致度判定基準が明確に定義
- [x] 順次処理の制御ロジックが設計
- [x] API間隔制御（レート制限対策）が考慮
- [x] リトライロジック（指数バックオフ）が設計
- [x] 例外処理がすべてのシナリオに対応
- [x] フロントエンドのデバッグログが設計
- [x] パフォーマンス目標が明記
- [x] 監査対応のログが設計（処理開始・完了時）
