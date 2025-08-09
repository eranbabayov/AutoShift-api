from typing import List

from fastapi import FastAPI, Depends

from database.core import *
from exception import NotFoundException, DatabaseException
from logger import get_logger
from schema import *

app = FastAPI(
    title="My API",
    description="This is the API documentation.",
    version="1.0.0",
    docs_url="/",  # 👈 Set Swagger UI to root
    redoc_url=None,  # Disable ReDoc if not needed
    openapi_url="/openapi.json",  # URL where OpenAPI schema is served
)

logger = get_logger("fast-api-logger")


@app.get("/get-employee-data/{employee_id}")
def get_employee_data(employee_id: int, db: Session = Depends(get_db)):
    employee_data = {}
    try:
        employee_data['employee_info'] = get_employee_using_id(db, employee_id)
        # employee_data['constraint'] = get_employee_constraints_using_id(db, employee_id)
        return employee_data
    except Exception as e:
        return e


@app.get("/get-employees/{company_name}", response_model=List[EmployeeRead])
def get_employees(company_name: str, db: Session = Depends(get_db)):
    try:
        return get_all_employees_using_company_id(db, company_name)
    except DatabaseException as e:
        return e


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


@app.get("/get-all-shift-constraint", response_model=List[ShiftConstraintSchema])
def get_all_shift_constraint_data(db: Session = Depends(get_db)):
    try:
        return get_all_shift_constraint(db)
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
        db_company = add_role(db, role_name)
        return db_company
    except (DatabaseException, FailedToCreateNewRole) as e:
        return e


@app.post("/add-employee/", response_model=EmployeeRead)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    try:
        employee = add_employee(db, employee)
        return employee
    except DatabaseException as e:
        return e


@app.post("/add-shift-type/")
def add_new_shift_type(shift_type: ShiftTypeSchema, db: Session = Depends(get_db)):
    try:
        new_shift_type = add_shift_type(db, shift_type)
        return new_shift_type
    except (DatabaseException, FailedToCreateNewRole) as e:
        return e


@app.post("/add-shift-constraint/")
def add_new_shift_constraint(shift_constraint: ShiftConstraintSchema, db: Session = Depends(get_db)):
    try:
        new_shift_constraint = add_shift_constraint(db, shift_constraint)
        return new_shift_constraint
    except (DatabaseException, FailedToCreateNewRole) as e:
        return e


@app.post("/add-optional-employee-constraint/")
def add_new_optional_employee_constraint(employee_constraint: OptionalEmployeeConstraintSchema,
                                         db: Session = Depends(get_db)):
    try:
        new_shift_constraint = add_optional_employee_constraint(db, employee_constraint)
        return new_shift_constraint
    except (DatabaseException, FailedToCreateNewRole) as e:
        return e


@app.post("/add-actual-employee-constraint/{employee_id}")
def add_new_actual_employee_constraint(employee_constraint: ActualEmployeeConstraintSchema,
                                       db: Session = Depends(get_db)):
    try:
        new_shift_constraint = add_actual_employee_constraint(db, employee_constraint)
        return new_shift_constraint
    except (DatabaseException, FailedToCreateNewRole) as e:
        return e


@app.delete("/delete-employee/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    try:
        delete_employee_using_id(db, employee_id)
    except (NotFoundException, delete_employee_using_id) as e:
        return e
