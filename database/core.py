import os
from datetime import timedelta, date, datetime
from typing import List, Any

from ortools.sat.python import cp_model
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from algo_example import add_soft_sum_constraint
from database.models import (
    Company,
    Role,
    Employee,
    ShiftTypes,
    ShiftConstraint,
    OptionalEmployeeConstraint,
    ActualEmployeeConstraint,
    ShiftRequest, WeeklyCoverDemands, PenalizedTransitions,
)
from exception import NotFoundException, DatabaseException, FailedToCreateNewRole, AlreadyExists
from logger import get_logger
from dotenv import load_dotenv

from schema import (
    EmployeeCreate,
    CompanySchema,
    ShiftTypeSchema,
    ShiftConstraintSchema,
    OptionalEmployeeConstraintSchema,
    ActualEmployeeConstraintSchema,
    AddShiftRequest, WeeklyCoverDemandSchema,
)

load_dotenv()

DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = get_logger("database-logger")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# -------------------------
# Company / Role / Employee
# -------------------------

def add_company(db: Session, company: CompanySchema) -> Company:
    try:
        db_company = Company(**company.model_dump())
        db.add(db_company)
        db.commit()
        db.refresh(db_company)
        return db_company
    except Exception as e:
        msg = f"Failed to add new company. exception: {e}"
        logger.exception(msg)
        raise DatabaseException(msg)


def add_role(db: Session, role_name: str) -> Role:
    try:
        existing_role = db.query(Role).filter_by(role_name=role_name).first()
        if existing_role:
            raise FailedToCreateNewRole(detail=f"Role with name '{role_name}' already exists.")
        role = Role(role_name=role_name)
        db.add(role)
        db.commit()
        db.refresh(role)
        return role
    except FailedToCreateNewRole:
        raise
    except Exception as e:
        logger.exception(f"Failed to add new role. exception: {e}")
        raise DatabaseException()


def add_employee(db: Session, employee: EmployeeCreate) -> Employee:
    try:
        # Validate FKs exist (optional but helpful)
        if not db.query(Company).filter_by(id=employee.company_id).first():
            raise NotFoundException(detail=f"Company id {employee.company_id} not found")
        if not db.query(Role).filter_by(id=employee.role_id).first():
            raise NotFoundException(detail=f"Role id {employee.role_id} not found")

        db_employee = Employee(**employee.model_dump())
        db.add(db_employee)
        db.commit()
        db.refresh(db_employee)
        return db_employee
    except NotFoundException:
        raise
    except Exception as e:
        logger.exception(f"Failed to add new employee. exception: {e}")
        raise DatabaseException()


def get_employee_using_id(db: Session, employee_id: int) -> Employee:
    try:
        employee = db.query(Employee).filter_by(id=employee_id).first()
        if not employee:
            raise NotFoundException(detail="The employee requested doesn't exist")
        return employee
    except NotFoundException:
        raise
    except Exception as e:
        logger.exception(f"Failed to search employee. exception: {e}")
        raise DatabaseException()


def delete_employee_using_id(db: Session, employee_id: int) -> None:
    try:
        employee = db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise NotFoundException(detail=f"Employee id {employee_id} not found")
        db.delete(employee)
        db.commit()
    except NotFoundException:
        raise
    except Exception as e:
        logger.exception(f"Failed to delete employee {e}")
        raise DatabaseException()


def get_all_employees_using_company_id(db: Session, company_id: int) -> List[Employee]:
    try:
        employees = db.query(Employee).filter(Employee.company_id == company_id).all()
        return employees
    except Exception as e:
        logger.exception(f"Failed to get employees for company_id: {company_id} exception: {e}")
        raise DatabaseException()


# -------------------------
# Shift types / constraints
# -------------------------

def add_shift_type(db: Session, shift_type: ShiftTypeSchema) -> ShiftTypes:
    try:
        existing_type = db.query(ShiftTypes).filter_by(type_name=shift_type.type_name).first()
        if existing_type:
            raise AlreadyExists(detail=f"shift type '{shift_type.type_name}' already exists.")
        new_shift_type = ShiftTypes(type_name=shift_type.type_name)
        db.add(new_shift_type)
        db.commit()
        db.refresh(new_shift_type)
        return new_shift_type
    except AlreadyExists:
        raise
    except Exception as e:
        logger.exception(f"Failed to add new shift type. exception: {e}")
        raise DatabaseException()


def add_shift_constraint(db: Session, shift_constraint: ShiftConstraintSchema) -> ShiftConstraint:
    try:
        # Validate FK
        if not db.query(ShiftTypes).filter_by(id=shift_constraint.shift_type_id).first():
            raise NotFoundException(detail=f"shift_type_id {shift_constraint.shift_type_id} not found")

        constraint = ShiftConstraint(**shift_constraint.model_dump())
        db.add(constraint)
        db.commit()
        db.refresh(constraint)
        return constraint
    except NotFoundException:
        raise
    except Exception as e:
        logger.exception(f"Failed to add new shift constraint. exception: {e}")
        raise DatabaseException()


def get_all_shift_constraint(db: Session) -> List[ShiftConstraint]:
    try:
        return db.query(ShiftConstraint).all()
    except Exception as e:
        logger.exception(f"Failed to get constraints exception: {e}")
        raise DatabaseException()


# -------------------------------------
# Optional / Actual employee constraints
# -------------------------------------

def get_all_optional_employee_constraint(db: Session) -> List[OptionalEmployeeConstraint]:
    try:
        return db.query(OptionalEmployeeConstraint).all()
    except Exception as e:
        logger.exception(f"Failed to get constraints exception: {e}")
        raise DatabaseException()


def get_all_actual_employee_constraint(db: Session, employee_id: int) -> List[OptionalEmployeeConstraint]:
    """
    Returns the OptionalEmployeeConstraint rows assigned to the given employee.
    """
    try:
        res: List[OptionalEmployeeConstraint] = []
        rows = db.query(ActualEmployeeConstraint).filter_by(employee_id=employee_id).all()
        for row in rows:
            oc = db.query(OptionalEmployeeConstraint).filter_by(id=row.constraint_id).first()
            if oc:
                res.append(oc)
        return res
    except Exception as e:
        logger.exception(f"Failed to get constraints exception: {e}")
        raise DatabaseException()


def add_optional_employee_constraint(db: Session, employee_constraint: OptionalEmployeeConstraintSchema) -> OptionalEmployeeConstraint:
    try:
        existing_constraint = db.query(OptionalEmployeeConstraint).filter_by(
            constraint_name=employee_constraint.constraint_name
        ).first()
        if existing_constraint:
            raise AlreadyExists(detail=f"employee optional constraint '{employee_constraint.constraint_name}' already exists.")

        constraint = OptionalEmployeeConstraint(**employee_constraint.model_dump())
        db.add(constraint)
        db.commit()
        db.refresh(constraint)
        return constraint
    except AlreadyExists:
        raise
    except Exception as e:
        logger.exception(f"Failed to add new optional employee constraint. exception: {e}")
        raise DatabaseException()


def add_actual_employee_constraint(db: Session, employee_constraint: ActualEmployeeConstraintSchema) -> ActualEmployeeConstraint:
    try:
        # Validate FKs
        if not db.query(OptionalEmployeeConstraint).filter_by(id=employee_constraint.constraint_id).first():
            raise NotFoundException(detail=f"optional constraint id {employee_constraint.constraint_id} not found")
        if not db.query(Employee).filter_by(id=employee_constraint.employee_id).first():
            raise NotFoundException(detail=f"employee id {employee_constraint.employee_id} not found")

        # Uniqueness check
        existing_constraint = db.query(ActualEmployeeConstraint).filter_by(
            constraint_id=employee_constraint.constraint_id,
            employee_id=employee_constraint.employee_id
        ).first()
        if existing_constraint:
            raise AlreadyExists(detail=f"employee actual constraint for constraint_id={employee_constraint.constraint_id} already exists.")

        row = ActualEmployeeConstraint(**employee_constraint.model_dump())
        db.add(row)
        db.commit()
        db.refresh(row)
        return row
    except (AlreadyExists, NotFoundException):
        raise
    except Exception as e:
        logger.exception(f"Failed to add new actual employee constraint. exception: {e}")
        raise DatabaseException()


# ---------------
# Shift requests
# ---------------

def add_shift_request(db: Session, shift: AddShiftRequest) -> ShiftRequest:
    try:
        # Validate FKs
        if not db.query(Employee).filter_by(id=shift.employee_id).first():
            raise NotFoundException(detail=f"employee id {shift.employee_id} not found")
        if not db.query(ShiftTypes).filter_by(id=shift.shift_type_id).first():
            raise NotFoundException(detail=f"shift_type_id {shift.shift_type_id} not found")

        new_shift_req = ShiftRequest(**shift.model_dump())
        db.add(new_shift_req)
        db.commit()
        db.refresh(new_shift_req)
        return new_shift_req
    except NotFoundException:
        raise
    except Exception as e:
        logger.exception(f"Failed to add new shift request for employee {shift.employee_id}. exception: {e}")
        raise DatabaseException()

def add_weekly_cover_demand(db: Session, demand: WeeklyCoverDemandSchema):
    try:
        new_demand = WeeklyCoverDemands(
            weekday=demand.weekday,
            shift_type_id=demand.shift_type_id,
            demand=demand.demand
        )
        db.add(new_demand)
        db.commit()
        db.refresh(new_demand)
        return new_demand
    except Exception as e:
        logger.exception(f"Failed to add weekly cover demand: {e}")
        raise DatabaseException()

def run_scheduler_for_company(db: Session, company_id: int) -> dict:
    """
    Loads all data for a specific company and runs the scheduler.
    """
    try:
        # 1. Load company-specific data
        employees = db.query(Employee).filter(Employee.company_id == company_id).all()
        shifts = db.query(ShiftTypes).all()
        shift_requests = (
            db.query(ShiftRequest)
            .join(Employee)
            .filter(Employee.company_id == company_id)
            .all()
        )
        weekly_demands = db.query(WeeklyCoverDemands).all()
        penalties = db.query(PenalizedTransitions).all()
        constraints = (
            db.query(ActualEmployeeConstraint)
            .join(Employee)
            .filter(Employee.company_id == company_id)
            .all()
        )

        # 2. Convert ORM objects to dicts for the algorithm
        employees_data = [e.__dict__ for e in employees]
        shift_requests_data = [s.__dict__ for s in shift_requests]
        shifts_data = [s.__dict__ for s in shifts]
        weekly_demands_data = [d.__dict__ for d in weekly_demands]
        penalties_data = [p.__dict__ for p in penalties]
        constraints_data = [c.__dict__ for c in constraints]

        # 3. Run scheduling algorithm
        schedule = my_scheduler(
            employees=employees_data,
            shift_requests=shift_requests_data,
            shifts=shifts_data,
            weekly_demands=weekly_demands_data,
            penalties=penalties_data,
            constraints=constraints_data
        )

        return schedule

    except Exception as e:
        raise DatabaseException(detail=f"Failed to run scheduler: {e}")


def my_scheduler(
    employees: list,
    shift_requests: list,
    shifts: list,
    weekly_demands: list,
    penalties: list,
    constraints: list
) -> dict:
    """
    Example scheduler stub. Replace with real scheduling logic.
    Returns a dictionary:
    {
        "employee_id": {
            "2025-09-01": "Morning",
            ...
        },
        ...
    }
    """
    schedule = {}
    for emp in employees:
        emp_id = emp['id']
        schedule[emp_id] = {}
        if shifts:
            # Example: assign first shift to first date
            schedule[emp_id]['2025-09-01'] = shifts[0]['type_name']
    return schedule

def add_soft_sequence_constraint(model, work_vars, max_length, penalty, penalty_var):
    """
    Adds a soft constraint that prevents more than `max_length` consecutive 1s in work_vars.
    If violated, adds `penalty` to penalty_var.
    """
    n = len(work_vars)
    for i in range(n - max_length):
        # Window of size max_length+1
        window = work_vars[i:i+max_length+1]
        # If all are 1s, that's a violation
        violation = model.NewBoolVar(f"violation_{i}")
        model.Add(sum(window) <= max_length).OnlyEnforceIf(violation.Not())
        model.Add(sum(window) > max_length).OnlyEnforceIf(violation)

        # Add penalty if violated
        model.Add(penalty_var >= violation * penalty)

def solve_shift_scheduling_from_data(
    num_employees: int,
    num_weeks: int,
    shifts: List[str],
    fixed_assignments: List[tuple],  # (emp_idx, shift_idx, day_idx)
    requests: List[tuple],  # (emp_idx, shift_idx, day_idx, weight)
    shift_constraints: List[tuple],  # (shift_idx, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost)
    weekly_sum_constraints: List[tuple],
    penalized_transitions: List[tuple],  # (prev_shift_idx, next_shift_idx, penalty)
    weekly_cover_demands: List[dict],  # list of 7 dicts: weekday -> {shift_idx: demand}
    excess_cover_penalties: List[int],
    params: str | None = "max_time_in_seconds:10.0",
):
    """Build a CP-SAT model using the provided structured data and solve it."""
    num_days = num_weeks * 7
    num_shifts = len(shifts)

    model = cp_model.CpModel()

    # work[e,s,d] boolean
    work = {}
    for e in range(num_employees):
        for s in range(num_shifts):
            for d in range(num_days):
                work[e, s, d] = model.NewBoolVar(f"work_{e}_{s}_{d}")

    obj_bool_vars = []
    obj_bool_coeffs = []
    obj_int_vars = []
    obj_int_coeffs = []

    # Exactly one shift per day per employee
    for e in range(num_employees):
        for d in range(num_days):
            model.AddExactlyOne(work[e, s, d] for s in range(num_shifts))

    # Fixed assignments
    for (emp_idx, shift_idx, day_idx) in fixed_assignments:
        if 0 <= emp_idx < num_employees and 0 <= shift_idx < num_shifts and 0 <= day_idx < num_days:
            model.Add(work[emp_idx, shift_idx, day_idx] == 1)

    # Requests -> add to objective
    for (emp_idx, shift_idx, day_idx, weight) in requests:
        if 0 <= emp_idx < num_employees and 0 <= shift_idx < num_shifts and 0 <= day_idx < num_days:
            obj_bool_vars.append(work[emp_idx, shift_idx, day_idx])
            obj_bool_coeffs.append(weight)

    # Shift sequence constraints
    for (shift_idx, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost) in shift_constraints:
        for e in range(num_employees):
            works = [work[e, shift_idx, d] for d in range(num_days)]
            lits, coeffs = add_soft_sequence_constraint(
                model,
                works,
                hard_min,
                soft_min,
                min_cost,
                soft_max,
                hard_max,
                max_cost,
                prefix=f"shift_constraint(emp={e},shift={shift_idx})",
            )
            obj_bool_vars.extend(lits)
            obj_bool_coeffs.extend(coeffs)

    # Weekly sum constraints
    for (shift_idx, hard_min, soft_min, min_cost, soft_max, hard_max, max_cost) in weekly_sum_constraints:
        for e in range(num_employees):
            for w in range(num_weeks):
                works = [work[e, shift_idx, d + w * 7] for d in range(7)]
                ints, coeffs = add_soft_sum_constraint(
                    model,
                    works,
                    hard_min,
                    soft_min,
                    min_cost,
                    soft_max,
                    hard_max,
                    max_cost,
                    prefix=f"weekly_sum(emp={e},shift={shift_idx},week={w})",
                )
                obj_int_vars.extend(ints)
                obj_int_coeffs.extend(coeffs)

    # Penalized transitions
    for (prev_s, next_s, cost) in penalized_transitions:
        for e in range(num_employees):
            for d in range(num_days - 1):
                clause = [work[e, prev_s, d].Not(), work[e, next_s, d + 1].Not()]
                if cost == 0:
                    model.AddBoolOr(clause)
                else:
                    trans_var = model.NewBoolVar(f"trans_emp{e}_d{d}_p{prev_s}_n{next_s}")
                    clause.append(trans_var)
                    model.AddBoolOr(clause)
                    obj_bool_vars.append(trans_var)
                    obj_bool_coeffs.append(cost)

    # Cover constraints
    for s in range(num_shifts):
        for w in range(num_weeks):
            for d in range(7):
                demand_val = weekly_cover_demands[d].get(s, 0)
                if demand_val == 0:
                    continue
                works = [work[e, s, w * 7 + d] for e in range(num_employees)]
                worked = model.NewIntVar(demand_val, num_employees, f"worked_s{s}_w{w}_d{d}")
                model.Add(worked == sum(works))
                over_penalty = excess_cover_penalties[s] if (0 <= s < len(excess_cover_penalties)) else 0
                if over_penalty > 0:
                    excess = model.NewIntVar(0, num_employees - demand_val, f"excess_s{s}_w{w}_d{d}")
                    model.Add(excess == worked - demand_val)
                    obj_int_vars.append(excess)
                    obj_int_coeffs.append(over_penalty)

    # Objective
    model.Minimize(
        sum(obj_bool_vars[i] * obj_bool_coeffs[i] for i in range(len(obj_bool_vars))) +
        sum(obj_int_vars[i] * obj_int_coeffs[i] for i in range(len(obj_int_vars)))
    )

    # Solve
    solver = cp_model.CpSolver()
    if params:
        solver.parameters.ParseFromString(params)
    status = solver.Solve(model)

    result_schedule = {}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        for e in range(num_employees):
            result_schedule[e] = {}
            for d in range(num_days):
                for s in range(num_shifts):
                    if solver.Value(work[e, s, d]):
                        result_schedule[e][d] = s
                        break

    return result_schedule
