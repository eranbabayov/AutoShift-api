from pydantic import BaseModel


class EmployeeCreate(BaseModel):
    full_name: str
    company_name: str
    role_name: str


class EmployeeRead(BaseModel):
    id: int
    full_name: str
    company_name: str
    role_name: str


class CompanySchema(BaseModel):
    company_name: str


class ShiftTypeSchema(BaseModel):
    type_name: str


class ShiftConstraintSchema(BaseModel):
    shift_type_name: str
    constraint_name: str
    val: int


class OptionalEmployeeConstraintSchema(BaseModel):
    constraint_name: str
    val: int


class ActualEmployeeConstraintSchema(BaseModel):
    constraint_id: int
    employee_id: int
