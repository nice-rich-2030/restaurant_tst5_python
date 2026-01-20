"""
Pydantic schemas for restaurant search API
"""
from typing import List, Optional
from pydantic import BaseModel, Field


# AI Response Schemas (for structured output)

class ShopListSchema(BaseModel):
    """Schema for shop name extraction from Gemini"""
    shops: List[str] = Field(
        description="抽出された飲食店の店舗名リスト(最大10件)"
    )


class JudgementSchema(BaseModel):
    """Schema for match judgement from Gemini"""
    score: int = Field(
        ge=1, le=5,
        description="合致度スコア(1:まったく合致しない ～ 5:完全に合致)"
    )
    reason: str = Field(
        description="判定理由(100文字以内)"
    )


# Request Schemas

class SearchRequest(BaseModel):
    """Initial search request"""
    input_text: str = Field(..., min_length=1, description="User's search query")


class ShopDetailRequest(BaseModel):
    """Shop detail search request"""
    input_text: str = Field(..., min_length=1, description="Original user's search query")
    shop_names: List[str] = Field(..., min_items=1, description="List of shop names to search")


# Response Data Models

class SourceCitation(BaseModel):
    """Source citation from grounding search"""
    url: str = Field(..., description="Source URL")
    title: Optional[str] = Field(None, description="Page title if available")


class ShopListData(BaseModel):
    """Extracted shop list data"""
    shops: List[str] = Field(default_factory=list, description="List of shop names (max 10)")


class JudgementData(BaseModel):
    """Match judgement result for a single shop"""
    shop_name: str = Field(..., description="Shop name")
    score: int = Field(..., ge=1, le=5, description="Match score (1-5)")
    reason: str = Field(..., description="Reason for the score")
    search_result: str = Field(..., description="Raw search result text")


class SummaryData(BaseModel):
    """Summary data for individual shop search"""
    shop_name: str = Field(..., description="Shop name")
    detail_search_result: str = Field(..., description="Detail search result text")
    judgement: JudgementData = Field(..., description="Match judgement")
    sources: List[SourceCitation] = Field(default_factory=list, description="Source citations from grounding search")


# Response Schemas

class InitialSearchResponse(BaseModel):
    """Response for initial search (Steps 1-3)"""
    input_text: str = Field(..., description="Original input text")
    prompt_used: str = Field(..., description="Prompt sent to Gemini")
    model_name: str = Field(..., description="Gemini model name used")
    raw_response: str = Field(..., description="Raw Grounding Search response")
    grounding_metadata: Optional[dict] = Field(None, description="Grounding Search metadata")
    shop_list: ShopListData = Field(..., description="Extracted shop list")


class ShopDetailSearchResponse(BaseModel):
    """Response for shop detail search (Steps 4-5)"""
    input_text: str = Field(..., description="Original input text")
    shop_names: List[str] = Field(..., description="Shop names searched")
    summaries: List[SummaryData] = Field(..., description="Summary for each shop")
