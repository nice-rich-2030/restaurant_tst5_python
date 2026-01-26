"""
Search service for restaurant search business logic
"""
import re
import time
from typing import List
from app.services.gemini_service import GeminiService
from app.schemas.search import (
    InitialSearchResponse,
    ShopListData,
    ShopListSchema,
    ShopDetailSearchResponse,
    SummaryData,
    JudgementData,
    JudgementSchema,
    SourceCitation,
)
from app.config import get_settings
from app.logger import logger


class SearchService:
    """Service for restaurant search operations"""

    def __init__(self):
        """Initialize search service"""
        self.gemini_service = GeminiService()
        self.settings = get_settings()
        logger.info("SearchService initialized")

    def initial_search(self, input_text: str) -> InitialSearchResponse:
        """
        Perform initial Grounding Search and extract shop names

        Args:
            input_text: User's search query

        Returns:
            InitialSearchResponse: Response with shop list

        Raises:
            Exception: If search or extraction fails
        """
        logger.info("=" * 80)
        logger.info(f"[Initial Search] Starting for input: {input_text}")
        logger.info("=" * 80)

        # Step 1: Build prompt for Grounding Search
        prompt = self._build_initial_search_prompt(input_text)
        logger.info(f"[Step 1] Prompt built: {len(prompt)} chars")

        # Step 2: Perform Grounding Search
        logger.info("[Step 2] Performing Grounding Search...")
        search_result = self.gemini_service.grounding_search(prompt)
        raw_response = search_result["text"]
        logger.info(f"[Step 2] Grounding Search completed: {len(raw_response)} chars")

        # Step 3: Extract shop names using structured output
        logger.info("[Step 3] Extracting shop names...")
        shop_list = self._extract_shop_names(raw_response)
        logger.info(f"[Step 3] Extracted {len(shop_list.shops)} shops")

        # Build response
        response = InitialSearchResponse(
            input_text=input_text,
            prompt_used=prompt,
            model_name=self.settings.gemini_model,
            raw_response=raw_response,
            grounding_metadata={
                "search_enabled": True,
                "model": self.settings.gemini_model
            },
            shop_list=shop_list
        )

        logger.info("=" * 80)
        logger.info("[Initial Search] Completed successfully")
        logger.info("=" * 80)

        return response

    def _build_initial_search_prompt(self, input_text: str) -> str:
        """
        Build prompt for initial Grounding Search

        Args:
            input_text: User's search query

        Returns:
            str: Formatted prompt
        """
        prompt = f"""「{input_text}」に合う飲食店を10件リストアップしてください。

以下の条件を満たす飲食店を検索してください:
- 検索条件に合致する飲食店
- 実在する店舗
- できるだけ具体的な店舗名(支店名も含む)

各店舗について、簡潔な説明を添えて回答してください。"""

        return prompt

    def _extract_shop_names(self, search_result: str) -> ShopListData:
        """
        Extract shop names from Grounding Search result using structured output

        Args:
            search_result: Raw search result text

        Returns:
            ShopListData: Extracted shop names

        Raises:
            Exception: If extraction fails
        """
        # Build extraction prompt
        extraction_prompt = f"""以下のテキストから、飲食店の店舗名を抽出してください。
最大10件まで抽出してください。

テキスト:
{search_result}

注意:
- 店舗名のみを抽出(説明文は含めない)
- 「〇〇店」のように店舗を特定できる形式で
- 重複がある場合は除去"""

        try:
            # Use structured output with Pydantic schema
            result = self.gemini_service.structured_response(
                prompt=extraction_prompt,
                schema=ShopListSchema
            )

            # Clean shop names
            cleaned_shops = []
            for shop in result.shops[:10]:
                # Remove leading numbers/symbols
                shop = re.sub(r'^[\d\.\)\-\s]+', '', shop)
                shop = shop.strip()
                if shop and shop not in cleaned_shops:
                    cleaned_shops.append(shop)

            logger.info(f"[Extract Shop Names] Cleaned: {len(cleaned_shops)} shops")

            return ShopListData(shops=cleaned_shops[:10])

        except Exception as e:
            logger.error(f"[Extract Shop Names] Structured extraction failed: {e}")
            # Fallback: simple line-based extraction
            logger.warning("[Extract Shop Names] Using fallback extraction")
            return self._fallback_extraction(search_result)

    def _fallback_extraction(self, text: str) -> ShopListData:
        """
        Fallback shop name extraction using regex

        Args:
            text: Search result text

        Returns:
            ShopListData: Extracted shop names
        """
        shops = []
        lines = text.split('\n')

        for line in lines:
            # Pattern: "1. Shop Name - description"
            match = re.match(r'^\d+\.\s*([^-:：]+)', line)
            if match:
                shop = match.group(1).strip()
                shops.append(shop)
            # Pattern: "・Shop Name"
            elif line.strip().startswith('・'):
                shop = line.strip()[1:].split(':')[0].split('：')[0]
                shops.append(shop.strip())

        logger.info(f"[Fallback Extraction] Found {len(shops)} shops")
        return ShopListData(shops=shops[:10])

    def detail_search(self, input_text: str, shop_names: List[str]) -> ShopDetailSearchResponse:
        """
        Perform detail search for selected shops with match judgement

        Args:
            input_text: Original user's search query
            shop_names: List of shop names to search

        Returns:
            ShopDetailSearchResponse: Response with summaries for each shop

        Raises:
            Exception: If search or judgement fails
        """
        logger.info("=" * 80)
        logger.info(f"[Detail Search] Starting for {len(shop_names)} shops")
        logger.info(f"[Detail Search] Input text: {input_text}")
        logger.info("=" * 80)

        summaries = []

        for i, shop_name in enumerate(shop_names, 1):
            logger.info(f"[Detail Search] Processing shop {i}/{len(shop_names)}: {shop_name}")

            try:
                # Step 4: Individual shop Grounding Search
                logger.info(f"[Step 4-{i}] Performing Grounding Search for: {shop_name}")
                detail_data = self._shop_detail_search(shop_name, input_text)
                detail_result = detail_data["text"]
                detail_sources = detail_data["sources"]
                logger.info(f"[Step 4-{i}] Grounding Search completed: {len(detail_result)} chars, {len(detail_sources)} sources")

                # Step 5: Match judgement
                logger.info(f"[Step 5-{i}] Judging match for: {shop_name}")
                judgement = self._judge_match(input_text, shop_name, detail_result)
                logger.info(f"[Step 5-{i}] Judgement: score={judgement.score}")

                # Build summary with sources
                summary = SummaryData(
                    shop_name=shop_name,
                    detail_search_result=detail_result,
                    judgement=JudgementData(
                        shop_name=shop_name,
                        score=judgement.score,
                        reason=judgement.reason,
                        search_result=detail_result
                    ),
                    sources=[
                        SourceCitation(url=s["url"], title=s.get("title"))
                        for s in detail_sources
                    ]
                )
                summaries.append(summary)

                # Rate limiting: wait 500ms between API calls
                if i < len(shop_names):
                    logger.debug(f"[Rate Limit] Waiting 500ms before next shop...")
                    time.sleep(0.5)

            except Exception as e:
                logger.error(f"[Detail Search] Error for shop '{shop_name}': {e}")
                # Add error summary
                error_summary = SummaryData(
                    shop_name=shop_name,
                    detail_search_result=f"検索エラー: {str(e)}",
                    judgement=JudgementData(
                        shop_name=shop_name,
                        score=1,
                        reason=f"検索中にエラーが発生しました: {str(e)[:50]}",
                        search_result=""
                    )
                )
                summaries.append(error_summary)

        response = ShopDetailSearchResponse(
            input_text=input_text,
            shop_names=shop_names,
            summaries=summaries
        )

        logger.info("=" * 80)
        logger.info(f"[Detail Search] Completed: {len(summaries)} summaries")
        logger.info("=" * 80)

        return response

    def _shop_detail_search(self, shop_name: str, input_text: str) -> dict:
        """
        Perform Grounding Search for a specific shop

        Args:
            shop_name: Shop name to search
            input_text: Original user's search query

        Returns:
            dict: {
                "text": str,  # Search result text
                "sources": List[dict]  # Source citations
            }
        """
        prompt = f"""「{shop_name}」について、以下の情報を検索してください。

【ユーザーの検索条件】
{input_text}

【検索項目】
- 店舗の基本情報(住所、営業時間、定休日など) 出典URL
- 料理のジャンルや特徴
- アクセス方法
- 評判や口コミ 出典URL
- 上記の検索条件との関連性

【回答形式】
- 検索項目の各情報の根拠となるURL（公式サイト、食べログ、Rettyなど）を必ず記載してください
- 情報の出典元がわかるよう「参照: [URL]」の形式で明記してください
- 丁寧かつ簡潔にまとめてください"""

        return self.gemini_service.grounding_search(prompt)

    def _judge_match(self, input_text: str, shop_name: str, shop_detail: str) -> JudgementSchema:
        """
        Judge how well the shop matches the search criteria

        Args:
            input_text: Original search query
            shop_name: Shop name
            shop_detail: Shop detail search result

        Returns:
            JudgementSchema: Match judgement with score and reason
        """
        prompt = f"""以下の検索条件と店舗情報を比較して、合致度を5段階で判定してください。

【検索条件】
{input_text}

【店舗名】
{shop_name}

【店舗情報】
{shop_detail}

【判定基準】
5: 完全に合致 - 検索条件のすべての要素を満たしている
4: ほぼ合致も一部相違あり - 主要な条件を満たすが、一部不明または相違がある
3: 半分程度合致 - 条件の約半分を満たす
2: 一部合致もほぼ相違 - 一部のみ該当し、多くの条件を満たさない
1: まったく合致しない - 検索条件とほぼ無関係

判定結果をスコアと理由(100文字以内)で回答してください。"""

        return self.gemini_service.structured_response(
            prompt=prompt,
            schema=JudgementSchema
        )
