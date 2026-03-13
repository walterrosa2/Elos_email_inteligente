from app.db.models import SystemSetting
from app.db.database import SessionLocal
from typing import Any

class SettingsService:
    @staticmethod
    def get_setting(key: str, default: Any = None) -> Any:
        db = SessionLocal()
        try:
            setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
            if setting:
                return setting.value
            return default
        finally:
            db.close()

    @staticmethod
    def set_setting(key: str, value: Any, description: str = None):
        db = SessionLocal()
        try:
            setting = db.query(SystemSetting).filter(SystemSetting.key == key).first()
            if setting:
                setting.value = value
                if description:
                    setting.description = description
            else:
                setting = SystemSetting(key=key, value=value, description=description)
                db.add(setting)
            db.commit()
        finally:
            db.close()

    @staticmethod
    def get_allowed_extensions() -> list:
        # Default if not configured
        default = [".pdf", ".xlsx", ".csv", ".xml", ".txt", ".xls"]
        return SettingsService.get_setting("allowed_extensions", default)

settings_service = SettingsService()
