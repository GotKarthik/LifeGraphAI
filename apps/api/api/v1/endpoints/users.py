from fastapi import APIRouter, Depends
from api.deps import SessionDep, CurrentUser
from schemas.user import UserResponse, UserUpdate

router = APIRouter()

@router.put("/profile", response_model=UserResponse)
def update_profile(user_update: UserUpdate, db: SessionDep, current_user: CurrentUser):
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    if user_update.bio is not None:
        current_user.bio = user_update.bio
        
    db.commit()
    db.refresh(current_user)
    return current_user

@router.get("/profile", response_model=UserResponse)
def get_profile(current_user: CurrentUser):
    return current_user
