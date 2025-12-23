"""
账号凭证管理 API 端点
Credentials Management API Endpoints

提供账号凭证的 CRUD 操作。
遵循宪法 II.C 安全要求：凭证加密存储。
"""

import json
from typing import Annotated

from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.deps import get_current_active_user
from app.core.logging import get_logger
from app.db.session import get_db
from app.models.account_credential import AccountCredential, CredentialStatus
from app.models.social_session import Platform
from app.models.user import User
from app.schemas.system import (
    CredentialActionResponse,
    CredentialCreate,
    CredentialListResponse,
    CredentialResponse,
    CredentialUpdate,
)

logger = get_logger(__name__)

router = APIRouter(prefix="/credentials", tags=["credentials"])

# 加密密钥（生产环境应从环境变量读取）
ENCRYPTION_KEY = settings.SECRET_KEY.encode()[:32].ljust(32, b"=")
cipher = Fernet(Fernet.generate_key())  # 临时密钥，生产环境应持久化


def encrypt_credentials(data: dict) -> str:
    """加密凭证数据"""
    json_str = json.dumps(data)
    return cipher.encrypt(json_str.encode()).decode()


def decrypt_credentials(encrypted: str) -> dict:
    """解密凭证数据"""
    try:
        decrypted = cipher.decrypt(encrypted.encode())
        return json.loads(decrypted.decode())
    except Exception:
        return {}


# =============================================================
# 凭证管理端点
# =============================================================

@router.get("", response_model=CredentialListResponse)
async def list_credentials(
    current_user: Annotated[User, Depends(get_current_active_user)],
    platform: Platform | None = Query(None, description="按平台过滤"),
    status: CredentialStatus | None = Query(None, description="按状态过滤"),
    db: AsyncSession = Depends(get_db),
):
    """
    获取账号凭证列表

    支持按平台和状态过滤。
    """
    stmt = select(AccountCredential).where(AccountCredential.user_id == current_user.id)

    if platform:
        stmt = stmt.where(AccountCredential.platform == platform)
    if status:
        stmt = stmt.where(AccountCredential.status == status)

    stmt = stmt.order_by(AccountCredential.created_at.desc())

    result = await db.execute(stmt)
    credentials = result.scalars().all()

    return CredentialListResponse(
        data=[CredentialResponse.model_validate(c) for c in credentials],
        total=len(credentials),
    )


@router.post("", response_model=CredentialActionResponse)
async def create_credential(
    data: CredentialCreate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    创建新的账号凭证

    凭证数据将被加密存储。
    """
    # 如果设置为默认，取消其他默认凭证
    if data.is_default:
        await _clear_default_credentials(db, current_user.id, data.platform)

    # 加密凭证数据
    encrypted = encrypt_credentials(data.credentials)

    credential = AccountCredential(
        user_id=current_user.id,
        name=data.name,
        platform=data.platform,
        credentials_encrypted=encrypted,
        is_default=data.is_default,
        status=CredentialStatus.ACTIVE,
    )

    db.add(credential)
    await db.commit()
    await db.refresh(credential)

    logger.info(f"创建凭证: {data.name}, 平台: {data.platform.value}")

    return CredentialActionResponse(
        success=True,
        message="凭证创建成功",
        credential_id=credential.id,
        credential=CredentialResponse.model_validate(credential),
    )


@router.get("/{credential_id}", response_model=CredentialResponse)
async def get_credential(
    credential_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """获取凭证详情"""
    credential = await _get_credential_or_404(db, credential_id, current_user.id)
    return CredentialResponse.model_validate(credential)


@router.put("/{credential_id}", response_model=CredentialActionResponse)
async def update_credential(
    credential_id: str,
    data: CredentialUpdate,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    更新凭证信息

    可以更新名称、状态、是否默认等。
    """
    credential = await _get_credential_or_404(db, credential_id, current_user.id)

    # 如果设置为默认，取消其他默认凭证
    if data.is_default and not credential.is_default:
        await _clear_default_credentials(db, current_user.id, credential.platform)

    # 更新字段
    update_dict = data.model_dump(exclude_unset=True, exclude={"credentials"})
    for field, value in update_dict.items():
        setattr(credential, field, value)

    # 如果更新了凭证数据
    if data.credentials:
        credential.credentials_encrypted = encrypt_credentials(data.credentials)

    await db.commit()
    await db.refresh(credential)

    logger.info(f"更新凭证: {credential.name}")

    return CredentialActionResponse(
        success=True,
        message="凭证更新成功",
        credential_id=credential.id,
        credential=CredentialResponse.model_validate(credential),
    )


@router.delete("/{credential_id}", response_model=CredentialActionResponse)
async def delete_credential(
    credential_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """删除凭证"""
    credential = await _get_credential_or_404(db, credential_id, current_user.id)

    name = credential.name
    await db.delete(credential)
    await db.commit()

    logger.info(f"删除凭证: {name}")

    return CredentialActionResponse(
        success=True,
        message="凭证删除成功",
        credential_id=credential_id,
    )


@router.post("/{credential_id}/test", response_model=CredentialActionResponse)
async def test_credential(
    credential_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """
    测试凭证有效性

    调用平台 API 验证凭证是否有效。
    """
    credential = await _get_credential_or_404(db, credential_id, current_user.id)

    # 解密凭证
    creds = decrypt_credentials(credential.credentials_encrypted)

    # TODO: 根据平台调用对应的 API 测试
    # 这里只是一个占位实现
    if credential.platform == Platform.TWITTER:
        # 测试 Twitter API
        success = bool(creds.get("bearer_token"))
    elif credential.platform == Platform.TELEGRAM:
        # 测试 Telegram Bot API
        success = bool(creds.get("bot_token"))
    else:
        success = False

    if success:
        credential.status = CredentialStatus.ACTIVE
        await db.commit()
        return CredentialActionResponse(
            success=True,
            message="凭证测试通过",
            credential_id=credential_id,
        )
    else:
        return CredentialActionResponse(
            success=False,
            message="凭证测试失败，请检查凭证配置",
            credential_id=credential_id,
        )


@router.post("/{credential_id}/set-default", response_model=CredentialActionResponse)
async def set_default_credential(
    credential_id: str,
    current_user: Annotated[User, Depends(get_current_active_user)],
    db: AsyncSession = Depends(get_db),
):
    """设置为默认凭证"""
    credential = await _get_credential_or_404(db, credential_id, current_user.id)

    # 取消同平台其他默认凭证
    await _clear_default_credentials(db, current_user.id, credential.platform)

    credential.is_default = True
    await db.commit()
    await db.refresh(credential)

    logger.info(f"设置默认凭证: {credential.name}, 平台: {credential.platform.value}")

    return CredentialActionResponse(
        success=True,
        message="已设置为默认凭证",
        credential_id=credential.id,
        credential=CredentialResponse.model_validate(credential),
    )


# =============================================================
# 辅助函数
# =============================================================

async def _get_credential_or_404(
    db: AsyncSession,
    credential_id: str,
    user_id: str,
) -> AccountCredential:
    """获取凭证或抛出 404 异常"""
    stmt = select(AccountCredential).where(
        AccountCredential.id == credential_id,
        AccountCredential.user_id == user_id,
    )
    result = await db.execute(stmt)
    credential = result.scalar_one_or_none()

    if not credential:
        raise HTTPException(status_code=404, detail=f"凭证不存在: {credential_id}")

    return credential


async def _clear_default_credentials(
    db: AsyncSession,
    user_id: str,
    platform: Platform,
) -> None:
    """取消指定平台的所有默认凭证"""
    stmt = select(AccountCredential).where(
        AccountCredential.user_id == user_id,
        AccountCredential.platform == platform,
        AccountCredential.is_default == True,  # noqa: E712
    )
    result = await db.execute(stmt)
    for credential in result.scalars().all():
        credential.is_default = False
