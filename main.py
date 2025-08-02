from typing import List

from fastapi import FastAPI, HTTPException, Depends

from database.core import *
from exception import NotFoundException, DatabaseException
from logger import get_logger
from schema import EmployeeRead, EmployeeCreate, CompanySchema

app = FastAPI()
logger = get_logger("fast-api-logger")


@app.post("/employees/", response_model=EmployeeRead)
def create_employee(employee: EmployeeCreate, db: Session = Depends(get_db)):
    try:
        employee = add_employee(db, employee)
        return employee
    except DatabaseException as e:
        return HTTPException(status_code=e.status_code, detail=e.detail)


@app.get("/employees/{company_id}", response_model=List[EmployeeRead])
def get_employees(company_id: str, db: Session = Depends(get_db)):
    try:
        return get_all_employees_using_company_id(db, company_id)
    except DatabaseException as e:
        return HTTPException(status_code=e.status_code, detail=e.detail)


@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int, db: Session = Depends(get_db)):
    try:
        delete_employee_using_id(db, employee_id)
    except (NotFoundException, delete_employee_using_id) as e:
        return HTTPException(status_code=e.status_code, detail=e.detail)


@app.post("/company_name/", response_model=CompanySchema)
def create_company(company_name: CompanySchema, db: Session = Depends(get_db)):
    try:
        db_company = add_company(db, company_name)
        return db_company
    except DatabaseException as e:
        return HTTPException(status_code=e.status_code, detail=e.detail)


@app.post("/role_name/")
def create_role(role_name: str, db: Session = Depends(get_db)):
    try:
        db_company = add_role(db, role_name)
        return db_company
    except DatabaseException as e:
        return HTTPException(status_code=e.status_code, detail=e.detail)
