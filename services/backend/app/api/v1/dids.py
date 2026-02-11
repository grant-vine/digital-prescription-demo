from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.dependencies.auth import get_current_user, get_db
from app.models.user import User
from app.models.did import DID
from app.models.wallet import Wallet
from app.services.acapy import ACAPyService

router = APIRouter()


class DIDResponse(BaseModel):
    did: str
    user_id: int
    role: str
    created_at: datetime

    class Config:
        from_attributes = True


class WalletResponse(BaseModel):
    wallet_id: str
    user_id: int
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class ErrorDetail(BaseModel):
    detail: str


@router.post(
    "/api/v1/dids",
    response_model=DIDResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorDetail, "description": "Not authenticated"},
        409: {"model": ErrorDetail, "description": "DID already exists for user"},
    },
)
async def create_did(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing_did = db.query(DID).filter(DID.user_id == current_user.id).first()
    if existing_did:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="DID already exists for this user",
        )

    acapy_service = ACAPyService()
    try:
        wallet_result = await acapy_service.create_wallet()

        if "error" in wallet_result or not wallet_result.get("did"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create DID in ACA-Py",
            )

        did_identifier = wallet_result["did"]

        existing_wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
        if not existing_wallet:
            wallet = Wallet(
                user_id=current_user.id,
                wallet_id=did_identifier.replace("did:cheqd:testnet:", "wallet-"),
                status="active",
            )
            db.add(wallet)

        did_record = DID(
            user_id=current_user.id,
            did_identifier=did_identifier,
            role=str(current_user.role),
        )
        db.add(did_record)
        db.commit()
        db.refresh(did_record)

        return DIDResponse(
            did=did_record.did_identifier,
            user_id=did_record.user_id,
            role=did_record.role,
            created_at=did_record.created_at,
        )

    finally:
        await acapy_service.close()


@router.get(
    "/api/v1/dids/{user_id}",
    response_model=DIDResponse,
    responses={
        401: {"model": ErrorDetail, "description": "Not authenticated"},
        404: {"model": ErrorDetail, "description": "DID not found"},
    },
)
async def resolve_did(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    did_record = db.query(DID).filter(DID.user_id == user_id).first()

    if not did_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="DID not found for user",
        )

    return DIDResponse(
        did=did_record.did_identifier,
        user_id=did_record.user_id,
        role=did_record.role,
        created_at=did_record.created_at,
    )


@router.post(
    "/api/v1/wallet/setup",
    response_model=WalletResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        401: {"model": ErrorDetail, "description": "Not authenticated"},
        409: {"model": ErrorDetail, "description": "Wallet already exists for user"},
    },
)
async def setup_wallet(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    existing_wallet = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()
    if existing_wallet:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Wallet already exists for this user",
        )

    acapy_service = ACAPyService()
    try:
        wallet_result = await acapy_service.create_wallet()

        if "error" in wallet_result or not wallet_result.get("did"):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create wallet in ACA-Py",
            )

        wallet_id = wallet_result["did"].replace("did:cheqd:testnet:", "wallet-")

        wallet_record = Wallet(
            user_id=current_user.id,
            wallet_id=wallet_id,
            status="active",
        )
        db.add(wallet_record)
        db.commit()
        db.refresh(wallet_record)

        return WalletResponse(
            wallet_id=wallet_record.wallet_id,
            user_id=wallet_record.user_id,
            status=wallet_record.status,
            created_at=wallet_record.created_at,
        )

    finally:
        await acapy_service.close()


@router.get(
    "/api/v1/wallet/status",
    response_model=WalletResponse,
    responses={
        401: {"model": ErrorDetail, "description": "Not authenticated"},
        404: {"model": ErrorDetail, "description": "Wallet not initialized"},
    },
)
async def get_wallet_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    wallet_record = db.query(Wallet).filter(Wallet.user_id == current_user.id).first()

    if not wallet_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Wallet not initialized for user",
        )

    return WalletResponse(
        wallet_id=wallet_record.wallet_id,
        user_id=wallet_record.user_id,
        status=wallet_record.status,
        created_at=wallet_record.created_at,
    )
