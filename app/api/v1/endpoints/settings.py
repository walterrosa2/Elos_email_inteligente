from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.db.models import SystemSetting
from app.api.schemas import schemas
from app.api.security import get_admin_user

router = APIRouter()

@router.get("", response_model=List[schemas.SystemSettingResponse])
def list_settings(db: Session = Depends(get_db), current_admin=Depends(get_admin_user)):
    return db.query(SystemSetting).all()

@router.get("/{key}", response_model=schemas.SystemSettingResponse)
def get_setting(key: str, db: Session = Depends(get_db), current_admin=Depends(get_admin_user)):
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        raise HTTPException(status_code=404, detail="Setting not found")
    return setting

@router.put("/{key}", response_model=schemas.SystemSettingResponse)
def update_setting(
    key: str, 
    setting_in: schemas.SystemSettingBase, 
    db: Session = Depends(get_db),
    current_admin=Depends(get_admin_user)
):
    setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
    if not setting:
        # Create it if it doesn't exist
        new_setting = SystemSetting(**setting_in.model_dump())
        db.add(new_setting)
        db.commit()
        db.refresh(new_setting)
        return new_setting
         
    setting.value = setting_in.value
    if setting_in.description:
        setting.description = setting_in.description
        
    db.commit()
    db.refresh(setting)
    return setting
