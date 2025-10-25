from typing import List

from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from database.core import (
    get_db,
    add_company,
    add_role,
    add_employee,
    delete_employee_using_id,
    get_employee_using_id,
    get_all_employees_using_company_id,
    get_all_optional_employee_constraint,
    get_all_actual_employee_constraint,
    get_all_shift_constraint,
    add_shift_type,
    add_shift_constraint,
    add_optional_employee_constraint,
    add_actual_employee_constraint,
    add_shift_request, add_weekly_cover_demand, run_scheduler_for_company
)
from exception import NotFoundException, DatabaseException, FailedToCreateNewRole, AlreadyExists
from logger import get_logger
from schema import (
    EmployeeRead,
    EmployeeCreate,
    CompanySchema,
    ShiftTypeSchema,
    ShiftConstraintSchema,
    OptionalEmployeeConstraintSchema,
    ActualEmployeeConstraintSchema,
    AddShiftRequest, WeeklyCoverDemandSchema,
)

app = FastAPI(
    title="My API",
    description="This is the API documentation.",
    version="1.0.0",
    docs_url="/",   # Swagger UI at root
    redoc_url=None,
    openapi_url="/openapi.json",
)

logger = get_logger("fast-api-logger")


# -------------------
# Employees & Company
# -------------------

@app.get("/get-employee-data/{employee_id}")
def get_employee_data(employee_id: int, db: Session = Depends(get_db)):
    try:
        employee_info = get_employee_using_id(db, employee_id)
        return {"employee_info": employee_info}
    except (NotFoundException, DatabaseException) as e:
        return e


@app.get("/get-employees/{company_id}", response_model=List[EmployeeRead])
def get_employees(company_id: int, db: Session = Depends(get_db)):
    try:
        return get_all_employees_using_company_id(db, company_id)
    except DatabaseException as e:
        return e


@app.post("/create-company/", response_model=CompanySchema)
def create_company(company_name: CompanySchema, db: Session = Depends(get_db)):
    try:
        db_company = add_company(db, company_name)
        return db_company
    except DatabaseException as e:
        return e


@app.post("/create-role/")
def create_role(role_name: str, db: Session = Depends(get_db)):
    try:
        db_role = add_role(db, role_name)
        return db_role
    except (DatabaseException, FailedToCreateNewRole) as e:
        return e


@app.post("/add-employee/", response_model=EmployeeRead)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    try:
        employee = add_employee(db, employee)
        return employee
    except (DatabaseException, NotFoundException) as e:
        return e


@app.delete("/delete-employee/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    try:
        delete_employee_using_id(db, employee_id)
        return {"status": "ok"}
    except (NotFoundException, DatabaseException) as e:
        return e


# -----------------
# Shift definitions
# -----------------

@app.post("/add-shift-type/")
def add_new_shift_type(shift_type: ShiftTypeSchema, db: Session = Depends(get_db)):
    try:
        new_shift_type = add_shift_type(db, shift_type)
        return new_shift_type
    except (DatabaseException, AlreadyExists) as e:
        return e


@app.post("/add-shift-constraint/")
def add_new_shift_constraint(shift_constraint: ShiftConstraintSchema, db: Session = Depends(get_db)):
    try:
        new_shift_constraint = add_shift_constraint(db, shift_constraint)
        return new_shift_constraint
    except (DatabaseException, AlreadyExists, NotFoundException) as e:
        return e


@app.get("/get-all-shift-constraint", response_model=List[ShiftConstraintSchema])
def get_all_shift_constraint_data(db: Session = Depends(get_db)):
    try:
        return get_all_shift_constraint(db)
    except DatabaseException as e:
        return e


# -------------------------
# Employee-level constraints
# -------------------------

@app.get("/get-all-optional-employee-constraint/", response_model=List[OptionalEmployeeConstraintSchema])
def get_all_employee_constraint_data(db: Session = Depends(get_db)):
    try:
        return get_all_optional_employee_constraint(db)
    except DatabaseException as e:
        return e


@app.get("/get-employee-constraint-using-id/{employee_id}", response_model=List[OptionalEmployeeConstraintSchema])
def get_actual_constraint_data_using_employee_id(employee_id: int, db: Session = Depends(get_db)):
    try:
        return get_all_actual_employee_constraint(db, employee_id)
    except DatabaseException as e:
        return e


@app.post("/add-optional-employee-constraint/")
def add_new_optional_employee_constraint(employee_constraint: OptionalEmployeeConstraintSchema,
                                         db: Session = Depends(get_db)):
    try:
        return add_optional_employee_constraint(db, employee_constraint)
    except (DatabaseException, AlreadyExists) as e:
        return e


@app.post("/add-actual-employee-constraint/")
def add_new_actual_employee_constraint(employee_constraint: ActualEmployeeConstraintSchema,
                                       db: Session = Depends(get_db)):
    try:
        return add_actual_employee_constraint(db, employee_constraint)
    except (DatabaseException, AlreadyExists, NotFoundException) as e:
        return e


# --------------
# Shift requests
# --------------

@app.post("/add-shift-request/")
def create_shift_request(shift: AddShiftRequest, db: Session = Depends(get_db)):
    try:
        return add_shift_request(db, shift)
    except (DatabaseException, NotFoundException) as e:
        return e


@app.post("/add-weekly-cover-demand/", response_model=WeeklyCoverDemandSchema)
def create_weekly_cover_demand(demand: WeeklyCoverDemandSchema, db: Session = Depends(get_db)):
    try:
        return add_weekly_cover_demand(db, demand)
    except DatabaseException as e:
        return e


@app.post("/run-scheduler/{company_id}")
def run_scheduler(company_id: int, db: Session = Depends(get_db)):
    try:
        schedule = run_scheduler_for_company(db, company_id)
        return {"schedule": schedule}
    except Exception as e:
        logger.exception(f"Failed to run scheduler: {e}")
        raise DatabaseException(detail=str(e))