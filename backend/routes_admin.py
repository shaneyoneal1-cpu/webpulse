from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import User
from schemas import UserCreate, UserUpdate, UserResponse
from auth import get_current_user, get_password_hash

router = APIRouter(prefix="/api/admin", tags=["admin"])

ALL_PERMISSIONS = {
    "view_websites": "View websites and monitoring data",
    "manage_websites": "Add, edit, and delete websites",
    "run_checks": "Trigger manual website checks",
    "view_users": "View list of sub-admins",
    "manage_users": "Create and manage sub-admins",
    "view_settings": "View system settings",
    "manage_settings": "Change system settings",
}


@router.get("/permissions")
def list_permissions(user: User = Depends(get_current_user)):
    return ALL_PERMISSIONS


@router.get("/users", response_model=List[UserResponse])
def list_users(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not user.is_main_admin:
        from auth import check_permission
        if not check_permission(user, "view_users"):
            raise HTTPException(status_code=403, detail="Permission denied")
    users = db.query(User).all()
    return users


@router.post("/users", response_model=UserResponse)
def create_subadmin(
    data: UserCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user.is_main_admin:
        from auth import check_permission
        if not check_permission(user, "manage_users"):
            raise HTTPException(status_code=403, detail="Permission denied")

    existing = db.query(User).filter(User.username == data.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        username=data.username,
        hashed_password=get_password_hash(data.password),
        is_main_admin=False,
        must_change_password=True,
        permissions=data.permissions or {},
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.put("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: int,
    data: UserUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user.is_main_admin:
        from auth import check_permission
        if not check_permission(user, "manage_users"):
            raise HTTPException(status_code=403, detail="Permission denied")

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.is_main_admin:
        raise HTTPException(status_code=400, detail="Cannot modify main admin")

    if data.is_active is not None:
        target.is_active = data.is_active
    if data.permissions is not None:
        target.permissions = data.permissions
    db.commit()
    db.refresh(target)
    return target


@router.delete("/users/{user_id}")
def delete_user(
    user_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not user.is_main_admin:
        from auth import check_permission
        if not check_permission(user, "manage_users"):
            raise HTTPException(status_code=403, detail="Permission denied")

    target = db.query(User).filter(User.id == user_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found")
    if target.is_main_admin:
        raise HTTPException(status_code=400, detail="Cannot delete main admin")

    db.delete(target)
    db.commit()
    return {"message": "User deleted"}
