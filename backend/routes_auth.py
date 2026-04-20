import pyotp
import io
import base64
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models import User, SystemConfig
from schemas import LoginRequest, TokenResponse, PasswordChange, TOTPSetupResponse, TOTPVerifyRequest
from auth import verify_password, get_password_hash, create_access_token, get_current_user, get_partial_user

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Account disabled")

    if user.must_change_password:
        token = create_access_token({"sub": user.username, "type": "partial"})
        return TokenResponse(access_token=token, must_change_password=True)

    if user.totp_enabled and user.totp_verified:
        if not req.totp_code:
            token = create_access_token({"sub": user.username, "type": "partial"})
            return TokenResponse(access_token=token, totp_required=True)
        totp = pyotp.TOTP(user.totp_secret)
        if not totp.verify(req.totp_code, valid_window=1):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code")
    elif not user.totp_enabled:
        token = create_access_token({"sub": user.username, "type": "partial"})
        return TokenResponse(access_token=token, totp_setup_required=True)

    token = create_access_token({"sub": user.username, "type": "full"})
    return TokenResponse(access_token=token)


@router.post("/change-password")
def change_password(req: PasswordChange, user: User = Depends(get_partial_user), db: Session = Depends(get_db)):
    if not user.must_change_password and req.current_password:
        if not verify_password(req.current_password, user.hashed_password):
            raise HTTPException(status_code=400, detail="Current password is incorrect")

    user.hashed_password = get_password_hash(req.new_password)
    user.must_change_password = False
    db.commit()

    config = db.query(SystemConfig).filter(SystemConfig.key == "initial_setup_done").first()
    if not config:
        config = SystemConfig(key="initial_setup_done", value="true")
        db.add(config)
        db.commit()

    if not user.totp_enabled:
        token = create_access_token({"sub": user.username, "type": "partial"})
        return {"message": "Password changed", "access_token": token, "totp_setup_required": True}

    token = create_access_token({"sub": user.username, "type": "full"})
    return {"message": "Password changed", "access_token": token}


@router.get("/totp/setup", response_model=TOTPSetupResponse)
def totp_setup(user: User = Depends(get_partial_user), db: Session = Depends(get_db)):
    if user.totp_enabled and user.totp_verified:
        raise HTTPException(status_code=400, detail="TOTP already configured")

    secret = pyotp.random_base32()
    user.totp_secret = secret
    db.commit()

    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=user.username, issuer_name="WebPulse")

    return TOTPSetupResponse(secret=secret, qr_uri=uri)


@router.post("/totp/verify")
def totp_verify(req: TOTPVerifyRequest, user: User = Depends(get_partial_user), db: Session = Depends(get_db)):
    if not user.totp_secret:
        raise HTTPException(status_code=400, detail="TOTP not set up")

    totp = pyotp.TOTP(user.totp_secret)
    if not totp.verify(req.code, valid_window=1):
        raise HTTPException(status_code=400, detail="Invalid TOTP code")

    user.totp_enabled = True
    user.totp_verified = True
    db.commit()

    token = create_access_token({"sub": user.username, "type": "full"})
    return {"message": "TOTP verified and enabled", "access_token": token}


@router.get("/me")
def get_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "is_main_admin": user.is_main_admin,
        "totp_enabled": user.totp_enabled,
        "permissions": user.permissions or {},
    }
