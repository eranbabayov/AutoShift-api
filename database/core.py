import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import Session

from database.models import *
from exception import NotFoundException, DatabaseException, FailedToCreateNewRole, AlreadyExists
from logger import get_logger
from dotenv import load_dotenv

from schema import *

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = get_logger("database-logger")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def delete_employee_using_id(db: Session, employee_id):
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise NotFoundException()
        db.delete(employee)
        db.commit()
    except Exception as e:
        logger.exception(f"Failed to delete employee {e}")
        raise DatabaseException()


def add_employee(db: Session, employee: EmployeeCreate):
    try:
        db_employee = Employee(**employee.dict())
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        return db_employee
    except Exception as e:
        logger.exception(f"Failed to add new employee. exception: {e}")
        raise DatabaseException()


def add_company(db: Session, company: CompanySchema):
    try:
        db_company = Company(**company.dict())
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        return db_company
    except Exception as e:
        msg = f"Failed to add new company. exception: {e}"
        logger.exception(msg)
        raise DatabaseException(msg)


def add_role(db: Session, role_name: str):
    try:
        existing_role = db.query(Role).filter_by(role_name=role_name).first()
        if existing_role:
            raise FailedToCreateNewRole(detail=f"Role with name '{role_name}' already exists.")

        role = Role(role_name=role_name)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    except FailedToCreateNewRole as ex:
        raise ex
    except Exception as e:
        logger.exception(f"Failed to add new role. exception: {e}")
        raise DatabaseException()


def get_employee_using_id(db: Session, employee_id):
    try:
        employee = db.query(Employee).filter_by(id=employee_id).first()
        if not employee:
            raise NotFoundException(detail=f"The employee requested isn't exists")
        return employee
    except NotFoundException as ex:
        raise ex
    except Exception as e:
        logger.exception(f"Failed to search employee. exception: {e}")
        raise DatabaseException()


# def get_employee_constraints_using_id(db: Session, employee_id):
#     try:
#         employee_constraint = db.query(EmployeeConstraint).filter_by(employee_id=employee_id).all()
#         if not employee_constraint:
#             raise NotFoundException(detail=f"There are no constraint for the requested employee")
#         return employee_constraint
#     except NotFoundException as ex:
#         raise ex
#
#     except Exception as e:
#         logger.exception(f"Failed to search employee. exception: {e}")
#         raise DatabaseException()


def get_all_employees_using_company_id(db: Session, company_name):
    try:
        employees = (
            db.query(Employee)
            .filter(Employee.company_name == company_name)
            .all()
        )
        return employees
    except Exception as e:
        logger.exception(f"Failed to get employees for company_name: {company_name} exception: {e}")
        raise DatabaseException()


def get_all_optional_employee_constraint(db: Session):
    try:
        constraints = (
            db.query(OptionalEmployeeConstraint)
            .all()
        )
        return constraints
    except Exception as e:
        logger.exception(f"Failed to get constraints exception: {e}")
        raise DatabaseException()


def get_all_actual_employee_constraint(db: Session, employee_id: int):
    try:
        res = []
        constraints = (
            db.query(ActualEmployeeConstraint).filter_by(employee_id=employee_id).all()
        )
        for constraint in constraints:
            constraint_data = db.query(OptionalEmployeeConstraint).filter_by(id=constraint.constraint_id).first()
            if constraint_data:
                res.append(constraint_data)
        return res
    except Exception as e:
        logger.exception(f"Failed to get constraints exception: {e}")
        raise DatabaseException()


def get_all_shift_constraint(db: Session):
    try:
        constraints = (
            db.query(ShiftConstraint)
            .all()
        )
        return constraints
    except Exception as e:
        logger.exception(f"Failed to get constraints exception: {e}")
        raise DatabaseException()

def add_shift_type(db: Session, shift_type: ShiftTypeSchema):
    try:
        existing_type = db.query(ShiftTypes).filter_by(type_name=shift_type.type_name).first()
        if existing_type:
            raise AlreadyExists(detail=f"shift type '{shift_type.type_name}' already exists.")

        new_shift_type = ShiftTypes(type_name=shift_type.type_name)
        db.add(new_shift_type)
        db.commit()
        db.refresh(new_shift_type)
        return new_shift_type
    except AlreadyExists as ex:
        raise ex
    except Exception as e:
        logger.exception(f"Failed to add new shift type. exception: {e}")
        raise DatabaseException()


def add_shift_constraint(db: Session, shift_constraint: ShiftConstraintSchema):
    try:
        existing_constraint = db.query(ShiftConstraint).filter_by(constraint_name=shift_constraint.constraint_name).first()
        if existing_constraint:
            raise AlreadyExists(detail=f"shift constraint '{shift_constraint.constraint_name}' already exists.")

        constraint = ShiftConstraint(shift_type_name=shift_constraint.shift_type_name, constraint_name=shift_constraint.constraint_name,
                                     val=shift_constraint.val)
        db.add(constraint)
        db.commit()
        db.refresh(constraint)
        return constraint
    except AlreadyExists as ex:
        raise ex
    except Exception as e:
        logger.exception(f"Failed to add new shift constraint. exception: {e}")
        raise DatabaseException()


def add_optional_employee_constraint(db: Session, employee_constraint: OptionalEmployeeConstraintSchema):
    try:
        existing_constraint = db.query(OptionalEmployeeConstraint).filter_by(constraint_name=employee_constraint.constraint_name).first()
        if existing_constraint:
            raise AlreadyExists(detail=f"employee optional constraint '{employee_constraint.constraint_name}' already exists.")

        constraint = OptionalEmployeeConstraint(constraint_name=employee_constraint.constraint_name,
                                                val=employee_constraint.val)
        db.add(constraint)
        db.commit()
        db.refresh(constraint)
        return constraint
    except AlreadyExists as ex:
        raise ex
    except Exception as e:
        logger.exception(f"Failed to add new optional employee constraint. exception: {e}")
        raise DatabaseException()


def add_actual_employee_constraint(db: Session, employee_constraint: ActualEmployeeConstraintSchema):
    try:
        existing_constraint = db.query(ActualEmployeeConstraint).filter_by(constraint_id=employee_constraint.constraint_id,
                                                                           employee_id=employee_constraint.employee_id).first()
        if existing_constraint:
            raise AlreadyExists(detail=f"employee actual constraint '{employee_constraint.constraint_name}' already exists.")

        constraint = ActualEmployeeConstraint(constraint_id=employee_constraint.constraint_id,
                                              employee_id=employee_constraint.employee_id)
        db.add(constraint)
        db.commit()
        db.refresh(constraint)
        return constraint
    except AlreadyExists as ex:
        raise ex
    except Exception as e:
        logger.exception(f"Failed to add new actual employee constraint. exception: {e}")
        raise DatabaseException()