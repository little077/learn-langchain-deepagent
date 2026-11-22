from __future__ import annotations

from pydantic import BaseModel, Field, field_validator


class ContactInfo(BaseModel):
    """用户联系方式，字段在生成时由 Pydantic 校验。"""

    name: str = Field(description="联系人姓名")
    phone: str = Field(description="联系电话，只写数字，不要空格或短横线")
    address: str = Field(description="详细地址")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, value: str) -> str:
        if not value.isdigit():
            raise ValueError("电话只能是数字")
        return value
