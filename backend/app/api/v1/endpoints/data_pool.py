"""Data Pool API endpoints.

Provides unified access to all platform data through DataPointer abstraction.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import Integer, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.deps import get_current_active_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.domains.data import DataPointer, DataVisibility, get_data_pointer_service
from app.domains.data.models import ArticleAnalysis, ArticleContent
from app.domains.user_data import UserDataRelation, get_user_data_service
from app.models.user import User
from app.schemas.data_pool import (
    AddTagRequest,
    BatchVisibilityUpdateRequest,
    BatchVisibilityUpdateResponse,
    DataPointerDetailResponse,
    DataPointerListResponse,
    DataPointerResponse,
    DataPoolStatisticsResponse,
    DomainStats,
    NotesResponse,
    TagsResponse,
    ToggleBookmarkResponse,
    ToggleFavoriteResponse,
    UpdateNotesRequest,
    UserDataRelationResponse,
    VisibilityUpdateRequest,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/data-pool", tags=["data-pool"])


@router.get("", response_model=DataPointerListResponse)
async def list_data_pointers(
    current_user: Annotated[User, Depends(get_current_active_user)],
    domain: str | None = Query(None, description="Filter by domain (news, twitter, telegram)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """
    List data pointers visible to the current user.

    Visibility rules:
    - Super admin sees all data
    - Regular users see: their own + tenant shared + public
    """
    service = get_data_pointer_service(db)

    pointers, total = await service.list_visible_to_user(
        user_id=str(current_user.id),
        tenant_id=current_user.tenant_id,
        is_super_admin=current_user.role_id == 1,  # role_id 1 = super_admin
        domain=domain,
        page=page,
        per_page=page_size,
    )

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return DataPointerListResponse(
        data=[DataPointerResponse.model_validate(p) for p in pointers],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/statistics", response_model=DataPoolStatisticsResponse)
async def get_statistics(
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Get data pool statistics for the current user.
    """
    user_id = str(current_user.id)
    is_super_admin = current_user.role_id == 1

    # Build visibility condition
    if is_super_admin:
        visibility_filter = True
    else:
        visibility_conditions = [
            DataPointer.created_by == user_id,
            DataPointer.visibility == DataVisibility.PUBLIC,
        ]
        if current_user.tenant_id:
            visibility_conditions.append(
                and_(
                    DataPointer.visibility == DataVisibility.TENANT_SHARED,
                    DataPointer.tenant_id == current_user.tenant_id,
                )
            )
        visibility_filter = or_(*visibility_conditions)

    # Count by domain
    domain_stats_query = (
        select(
            DataPointer.domain,
            func.count(DataPointer.id).label("count"),
            func.sum(DataPointer.has_content.cast(Integer)).label("has_content_count"),
            func.sum(DataPointer.has_analysis.cast(Integer)).label("has_analysis_count"),
        )
        .where(visibility_filter)
        .group_by(DataPointer.domain)
    )

    domain_result = await db.execute(domain_stats_query)
    domain_rows = domain_result.all()

    by_domain = [
        DomainStats(
            domain=row.domain,
            count=row.count,
            has_content_count=int(row.has_content_count or 0),
            has_analysis_count=int(row.has_analysis_count or 0),
        )
        for row in domain_rows
    ]

    # Count by visibility
    visibility_query = (
        select(DataPointer.visibility, func.count(DataPointer.id).label("count"))
        .where(visibility_filter)
        .group_by(DataPointer.visibility)
    )
    visibility_result = await db.execute(visibility_query)
    by_visibility = {row.visibility.value: row.count for row in visibility_result.all()}

    # User favorites/bookmarks count
    favorites_query = select(func.count(UserDataRelation.id)).where(
        and_(
            UserDataRelation.user_id == user_id,
            UserDataRelation.is_favorited == True,  # noqa: E712
        )
    )
    favorites_result = await db.execute(favorites_query)
    favorites_count = favorites_result.scalar() or 0

    bookmarks_query = select(func.count(UserDataRelation.id)).where(
        and_(
            UserDataRelation.user_id == user_id,
            UserDataRelation.is_bookmarked == True,  # noqa: E712
        )
    )
    bookmarks_result = await db.execute(bookmarks_query)
    bookmarks_count = bookmarks_result.scalar() or 0

    # Total count
    total_query = select(func.count(DataPointer.id)).where(visibility_filter)
    total_result = await db.execute(total_query)
    total = total_result.scalar() or 0

    return DataPoolStatisticsResponse(
        total_pointers=total,
        by_domain=by_domain,
        by_visibility=by_visibility,
        user_favorites_count=favorites_count,
        user_bookmarks_count=bookmarks_count,
    )


@router.get("/favorites", response_model=DataPointerListResponse)
async def list_favorites(
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    List user's favorited data pointers.
    """
    user_id = str(current_user.id)
    user_data_service = get_user_data_service(db)

    relations, total = await user_data_service.get_user_favorites(
        user_id=user_id,
        page=page,
        per_page=page_size,
    )

    # Get pointers for these relations
    pointer_ids = [r.pointer_id for r in relations]
    if pointer_ids:
        stmt = select(DataPointer).where(DataPointer.id.in_(pointer_ids))
        result = await db.execute(stmt)
        pointers = result.scalars().all()
    else:
        pointers = []

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return DataPointerListResponse(
        data=[DataPointerResponse.model_validate(p) for p in pointers],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/bookmarks", response_model=DataPointerListResponse)
async def list_bookmarks(
    current_user: Annotated[User, Depends(get_current_active_user)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    List user's bookmarked data pointers.
    """
    user_id = str(current_user.id)
    user_data_service = get_user_data_service(db)

    relations, total = await user_data_service.get_user_bookmarks(
        user_id=user_id,
        page=page,
        per_page=page_size,
    )

    # Get pointers for these relations
    pointer_ids = [r.pointer_id for r in relations]
    if pointer_ids:
        stmt = select(DataPointer).where(DataPointer.id.in_(pointer_ids))
        result = await db.execute(stmt)
        pointers = result.scalars().all()
    else:
        pointers = []

    total_pages = (total + page_size - 1) // page_size if total > 0 else 0

    return DataPointerListResponse(
        data=[DataPointerResponse.model_validate(p) for p in pointers],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/{pointer_id}", response_model=DataPointerDetailResponse)
async def get_data_pointer(
    pointer_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Get a single data pointer with its content and analyses.
    """
    service = get_data_pointer_service(db)
    pointer = await service.get_by_id(pointer_id)

    if not pointer:
        raise HTTPException(status_code=404, detail="Data pointer not found")

    # Check visibility
    user_id = str(current_user.id)
    is_super_admin = current_user.role_id == 1

    if not is_super_admin:
        can_access = (
            pointer.created_by == user_id
            or pointer.visibility == DataVisibility.PUBLIC
            or (
                pointer.visibility == DataVisibility.TENANT_SHARED
                and pointer.tenant_id == current_user.tenant_id
            )
        )
        if not can_access:
            raise HTTPException(status_code=403, detail="Access denied")

    # Get content (primary version)
    content_stmt = select(ArticleContent).where(
        and_(
            ArticleContent.pointer_id == pointer_id,
            ArticleContent.is_primary == True,  # noqa: E712
        )
    )
    content_result = await db.execute(content_stmt)
    content = content_result.scalar_one_or_none()

    # Get analyses
    analyses_stmt = select(ArticleAnalysis).where(ArticleAnalysis.pointer_id == pointer_id)
    analyses_result = await db.execute(analyses_stmt)
    analyses = analyses_result.scalars().all()

    # Build response
    response_data = DataPointerResponse.model_validate(pointer).model_dump()
    response_data["content"] = content
    response_data["analyses"] = list(analyses)

    return DataPointerDetailResponse(**response_data)


@router.get("/{pointer_id}/relation", response_model=UserDataRelationResponse | None)
async def get_user_relation(
    pointer_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Get user's relation to a data pointer (favorites, bookmarks, tags, notes).
    """
    user_id = str(current_user.id)

    stmt = select(UserDataRelation).where(
        and_(
            UserDataRelation.user_id == user_id,
            UserDataRelation.pointer_id == pointer_id,
        )
    )
    result = await db.execute(stmt)
    relation = result.scalar_one_or_none()

    if not relation:
        return None

    return UserDataRelationResponse.model_validate(relation)


@router.post("/{pointer_id}/favorite", response_model=ToggleFavoriteResponse)
async def toggle_favorite(
    pointer_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle favorite status for a data pointer.
    """
    user_id = str(current_user.id)
    service = get_user_data_service(db)

    is_favorited = await service.toggle_favorite(user_id, pointer_id)
    await db.commit()

    return ToggleFavoriteResponse(pointer_id=pointer_id, is_favorited=is_favorited)


@router.post("/{pointer_id}/bookmark", response_model=ToggleBookmarkResponse)
async def toggle_bookmark(
    pointer_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Toggle bookmark status for a data pointer.
    """
    user_id = str(current_user.id)
    service = get_user_data_service(db)

    is_bookmarked = await service.toggle_bookmark(user_id, pointer_id)
    await db.commit()

    return ToggleBookmarkResponse(pointer_id=pointer_id, is_bookmarked=is_bookmarked)


@router.post("/{pointer_id}/read")
async def mark_as_read(
    pointer_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Mark a data pointer as read.
    """
    user_id = str(current_user.id)
    service = get_user_data_service(db)

    await service.mark_as_read(user_id, pointer_id)
    await db.commit()

    return {"pointer_id": pointer_id, "is_read": True}


@router.post("/{pointer_id}/tags", response_model=TagsResponse)
async def add_tag(
    pointer_id: str,
    request: AddTagRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Add a tag to a data pointer.
    """
    user_id = str(current_user.id)
    service = get_user_data_service(db)

    tags = await service.add_tag(user_id, pointer_id, request.tag)
    await db.commit()

    return TagsResponse(pointer_id=pointer_id, tags=tags)


@router.delete("/{pointer_id}/tags/{tag}", response_model=TagsResponse)
async def remove_tag(
    pointer_id: str,
    tag: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Remove a tag from a data pointer.
    """
    user_id = str(current_user.id)
    service = get_user_data_service(db)

    tags = await service.remove_tag(user_id, pointer_id, tag)
    await db.commit()

    return TagsResponse(pointer_id=pointer_id, tags=tags)


@router.put("/{pointer_id}/notes", response_model=NotesResponse)
async def update_notes(
    pointer_id: str,
    request: UpdateNotesRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Update notes for a data pointer.
    """
    user_id = str(current_user.id)
    service = get_user_data_service(db)

    await service.update_notes(user_id, pointer_id, request.notes)
    await db.commit()

    return NotesResponse(pointer_id=pointer_id, notes=request.notes)


# ============ Admin Only Endpoints ============


@router.patch("/{pointer_id}/visibility", response_model=DataPointerResponse)
async def update_visibility(
    pointer_id: str,
    request: VisibilityUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Update visibility of a data pointer.

    Admin only: can change visibility of any pointer.
    Regular users: can only change their own pointers.
    """
    service = get_data_pointer_service(db)
    pointer = await service.get_by_id(pointer_id)

    if not pointer:
        raise HTTPException(status_code=404, detail="Data pointer not found")

    user_id = str(current_user.id)
    is_admin = current_user.is_admin

    # Check permission
    if not is_admin and pointer.created_by != user_id:
        raise HTTPException(status_code=403, detail="Cannot change visibility of others' data")

    # Map enum
    visibility = DataVisibility(request.visibility.value)

    updated = await service.update_visibility(pointer_id, visibility, user_id)
    await db.commit()

    return DataPointerResponse.model_validate(updated)


@router.post("/batch-visibility", response_model=BatchVisibilityUpdateResponse)
async def batch_update_visibility(
    request: BatchVisibilityUpdateRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    Batch update visibility of multiple data pointers.

    Admin only.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin only")

    service = get_data_pointer_service(db)
    visibility = DataVisibility(request.visibility.value)

    updated_count = await service.batch_update_visibility(
        request.pointer_ids,
        visibility,
        str(current_user.id),
    )
    await db.commit()

    return BatchVisibilityUpdateResponse(
        updated_count=updated_count,
        pointer_ids=request.pointer_ids,
    )
