import enum
from datetime import date
from pydantic import BaseModel


class DesiredOption(str, enum.Enum):
    yes = "yes"
    no = "no"
    prefer_not = "prefer_not"

class WeeklyCoverDemandSchema(BaseModel):
    weekday: str  # or Enum('Sun','Mon','Tue','Wed','Thu','Fri','Sat')
    shift_type_id: int
    demand: int

class AddShiftRequest(BaseModel):
    employee_id: int
    shift_type_id: int
    shift_date: date
    desired: DesiredOption
    weight: int


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


class ShiftTypeSchema(BaseModel):
    type_name: str


class ShiftConstraintSchema(BaseModel):
    shift_type_id: int
    hard_min: int | None = None
    soft_min: int | None = None
    min_penalty: int | None = None
    soft_max: int | None = None
    hard_max: int | None = None
    max_penalty: int | None = None


class OptionalEmployeeConstraintSchema(BaseModel):
    constraint_name: str
    val: int


class ActualEmployeeConstraintSchema(BaseModel):
    constraint_id: int
    employee_id: int
