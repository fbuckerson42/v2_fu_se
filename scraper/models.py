from pydantic import BaseModel, Field
from typing import Optional, Any, Dict
from datetime import date, datetime


class OrderModel(BaseModel):
    
    id: int = Field(..., description="Order ID from KeyCRM")
    created_at: date = Field(..., description="Order creation date")
    closed_at: Optional[date] = Field(None, description="Order closing date")
    ordered_at: Optional[date] = Field(None, description="Order date")
    
    status_id: int = Field(..., description="Status ID")
    status_name: str = Field(..., description="Status name")
    status_group_name: Optional[str] = Field(None, description="Status group name")
    status_changed_at: Optional[date] = Field(None, description="Status change date")
    
    manager_id: int = Field(..., description="Manager ID")
    manager_name: str = Field(..., description="Manager full name")
    
    grand_total: float = Field(..., description="Total order amount")
    
    prp_date: Optional[date] = Field(None, description="PRP date from custom fields")
    
    raw_data: Optional[Dict[str, Any]] = Field(None, description="Full JSON response")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 91689,
                "created_at": "2026-04-24",
                "closed_at": None,
                "ordered_at": "2026-04-24",
                "status_id": 1,
                "status_name": "Новий",
                "status_group_name": "Новий",
                "status_changed_at": "2026-04-24",
                "manager_id": 320,
                "manager_name": "Ілона Ілонівна",
                "grand_total": 2000.00,
                "prp_date": "2026-04-24",
                "raw_data": {}
            }
        }


class StatusModel(BaseModel):
    
    id: int
    name: str
    alias: str
    group_id: int
    group_name: str
    is_active: bool


class ManagerModel(BaseModel):
    
    id: int
    first_name: str
    last_name: str
    full_name: str
    email: Optional[str] = None
    role_id: int
    role_name: Optional[str] = None


class CustomFieldModel(BaseModel):
    
    id: int
    field_id: int
    value: Any
    field: Optional[Dict[str, Any]] = None


class APIResponseModel(BaseModel):
    
    data: list
    meta: Optional[Dict[str, Any]] = None
    links: Optional[Dict[str, Any]] = None
