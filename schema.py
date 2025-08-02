from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    full_name: str
    company_id: int
    role_id: int


class EmployeeRead(BaseModel):
    id: int
    full_name: str
    company_id: int
    role_id: int


class CompanySchema(BaseModel):
    company_name: str
