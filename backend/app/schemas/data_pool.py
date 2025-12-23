"""Data Pool Pydantic schemas (request/response models)."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class DataVisibilityEnum(str, Enum):
    """Data visibility options."""

    PRIVATE = "private"
    TENANT_SHARED = "tenant_shared"
    PUBLIC = "public"


class PlatformTypeEnum(str, Enum):
    """Platform types."""

    NEWS = "news"
    TWITTER = "twitter"
    TELEGRAM = "telegram"
    WEIBO = "weibo"


# ============ Response Models ============


class DataPointerResponse(BaseModel):
    """Single data pointer response."""

    id: str
    domain: str
    domain_table: str
    domain_id: str
    visibility: DataVisibilityEnum
    created_by: str | None = None
    tenant_id: int | None = None
    title: str | None = None
    url: str | None = None
    platform: str | None = None
    has_content: bool = False
    has_analysis: bool = False
    extra_metadata: dict | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleContentResponse(BaseModel):
    """Article content response."""

    id: str
    pointer_id: str
    title: str | None = None
    content_text: str | None = None
    summary: str | None = None
    word_count: int = 0
    extraction_method: str | None = None
    version: int = 1
    is_primary: bool = True
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ArticleAnalysisResponse(BaseModel):
    """Article analysis response."""

    id: str
    pointer_id: str
    analysis_type: str
    result: dict | None = None
    model_name: str | None = None
    confidence: float | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DataPointerDetailResponse(DataPointerResponse):
    """Data pointer detail with content and analyses."""

    content: ArticleContentResponse | None = None
    analyses: list[ArticleAnalysisResponse] = []


class DataPointerListResponse(BaseModel):
    """Paginated data pointer list response."""

    data: list[DataPointerResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class UserDataRelationResponse(BaseModel):
    """User data relation response."""

    id: str
    user_id: str
    pointer_id: str
    is_favorited: bool = False
    is_bookmarked: bool = False
    is_read: bool = False
    user_tags: list[str] | None = None
    user_notes: str | None = None
    rating: int | None = None
    read_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class DataPointerWithRelationResponse(DataPointerResponse):
    """Data pointer with user relation."""

    relation: UserDataRelationResponse | None = None


# ============ Request Models ============


class VisibilityUpdateRequest(BaseModel):
    """Request to update visibility."""

    visibility: DataVisibilityEnum


class BatchVisibilityUpdateRequest(BaseModel):
    """Request to batch update visibility."""

    pointer_ids: list[str] = Field(..., min_length=1, max_length=100)
    visibility: DataVisibilityEnum


class BatchVisibilityUpdateResponse(BaseModel):
    """Response for batch visibility update."""

    updated_count: int
    pointer_ids: list[str]


class ToggleFavoriteResponse(BaseModel):
    """Response for toggle favorite."""

    pointer_id: str
    is_favorited: bool


class ToggleBookmarkResponse(BaseModel):
    """Response for toggle bookmark."""

    pointer_id: str
    is_bookmarked: bool


class AddTagRequest(BaseModel):
    """Request to add a tag."""

    tag: str = Field(..., min_length=1, max_length=50)


class TagsResponse(BaseModel):
    """Response with tags list."""

    pointer_id: str
    tags: list[str]


class UpdateNotesRequest(BaseModel):
    """Request to update notes."""

    notes: str = Field(..., max_length=10000)


class NotesResponse(BaseModel):
    """Response with notes."""

    pointer_id: str
    notes: str | None


# ============ Statistics ============


class DomainStats(BaseModel):
    """Statistics for a domain."""

    domain: str
    count: int
    has_content_count: int
    has_analysis_count: int


class DataPoolStatisticsResponse(BaseModel):
    """Data pool statistics response."""

    total_pointers: int
    by_domain: list[DomainStats]
    by_visibility: dict[str, int]
    user_favorites_count: int = 0
    user_bookmarks_count: int = 0
