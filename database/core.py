import os
from typing import List, Any

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from ortools.sat.python import cp_model
from datetime import date, timedelta
import calendar

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
        shifts = db.query(ShiftTypes).with_entities(
                ShiftTypes.type_name
            ).all()

        shifts_data = [s[0] for s in shifts]

        shift_requests_data = (
            db.query(ShiftRequest)
            .join(Employee)
            .filter(Employee.company_id == company_id)
            .with_entities(
                ShiftRequest.employee_id,
                ShiftRequest.shift_type_id,
                ShiftRequest.shift_date,
                ShiftRequest.weight
            )
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
    num_employees = len(employees)
    YEAR = 2025
    MONTH = 11
    START_DATE = date(YEAR, MONTH, 1)
    HORIZON_DAYS = calendar.monthrange(YEAR, MONTH)[1]
    num_days = HORIZON_DAYS
    num_shifts = len(shifts)
    print("@#@###############")
    print(shifts)
    print(num_shifts)
    # num_shifts=1
    # print(num_shifts)
    start_sat_index = sat_index_from_pyweekday(START_DATE.weekday())

    # Demand template per weekday (Sat..Fri). For ["O","N"], each entry is a 1-tuple.
    weekday_demand_template = [
        (1,),  # Sat
        (1,),  # Sun
        (1,),  # Mon
        (1,),  # Tue
        (1,),  # Wed
        (1,),  # Thu
        (1,),  # Fri
    ]

    # ---------------------------------------------------------------------
    # Model
    # ---------------------------------------------------------------------
    shortage_penalty = 10  # tune as needed

    # Fixed assignments: (employee, shift, day).
    fixed_assignments = []

    # Requests: (employee, shift, day, weight); negative weight = employee wants it.

    print("@!!~!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    print(shift_requests)
    print("@!!~!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
    model = cp_model.CpModel()
    # Decision vars
    work = {}
    for e in range(num_employees):
        for s in range(num_shifts):
            for d in range(num_days):
                work[e, s, d] = model.new_bool_var(f"work{e}_{s}_{d}")
    # Objective accumulators
    obj_int_vars: list[cp_model.IntVar] = []
    obj_int_coeffs: list[int] = []
    obj_bool_vars: list[cp_model.BoolVarT] = []
    obj_bool_coeffs: list[int] = []

    # Exactly one shift per (employee, day)
    for e in range(num_employees):
        for d in range(num_days):
            model.add_exactly_one(work[e, s, d] for s in range(num_shifts))

    # Fixed assignments
    for e, s, d in fixed_assignments:
        model.add(work[e, s, d] == 1)

    # Employee shift_requests feed the objective (negative = gain)
    for e, s, d, w in shift_requests:
        if 0 <= e < num_employees and 0 < s < num_shifts and 0 <= d < num_days:
            obj_bool_vars.append(work[e, s, d])
            obj_bool_coeffs.append(w)

    # ELIGIBILITY: only requested/fixed working shifts; else force Off
    allowed_work = set()
    for e, s, d in fixed_assignments:
        if s > 0 and 0 <= d < num_days and 0 <= e < num_employees:
            allowed_work.add((e, s, d))
    for e, s, d, w in shift_requests:
        if s > 0 and w < 0 and 0 <= d < num_days and 0 <= e < num_employees:
            allowed_work.add((e, s, d))
    for e in range(num_employees):
        for d in range(num_days):
            for s in range(1, num_shifts):  # working shifts only
                if (e, s, d) not in allowed_work:
                    model.add(work[e, s, d] == 0)


    # Soft coverage (per absolute day)
    shortage_vars = {}  # (s, d) -> IntVar
    for s in range(1, num_shifts):  # ignore Off=0
        for d in range(num_days):
            demand = demand_for_day_and_shift(
                weekday_demand_template, start_sat_index, d, s
            )
            works_sd = [work[e, s, d] for e in range(num_employees)]
            shortage = model.new_int_var(0, demand, f"shortage_s{s}_d{d}")
            model.add(sum(works_sd) + shortage == demand)
            if shortage_penalty > 0:
                obj_int_vars.append(shortage)
                obj_int_coeffs.append(shortage_penalty)
            shortage_vars[(s, d)] = shortage


    # --- Fair-share on NIGHT workload ---
    totals_N: list[cp_model.IntVar] = []
    shift_len = len(shifts)
    for e in range(num_employees):
        t = model.new_int_var(0, num_days, f"total_N_e{e}")
        model.add(t == sum(work[e, shift_len-1, d] for d in range(num_days)))
        totals_N.append(t)

    # Keep the weight small so it nudges but doesn't dominate feasibility.
    FAIRNESS_COST = 1  # try 1–5
    vars_fair, coeffs_fair = add_fair_share(
        model,
        totals_per_employee=totals_N,
        fairness_cost=FAIRNESS_COST,
        prefix="fair_N",
        max_total=num_days,
    )
    obj_int_vars.extend(vars_fair)
    obj_int_coeffs.extend(coeffs_fair)

    # Objective
    model.minimize(
        sum(obj_bool_vars[i] * obj_bool_coeffs[i] for i in range(len(obj_bool_vars)))
        + sum(obj_int_vars[i] * obj_int_coeffs[i] for i in range(len(obj_int_vars)))
    )

    # Solve
    solver = cp_model.CpSolver()
    # If desired: solver.parameters.parse_text_format(params)
    solution_printer = cp_model.ObjectiveSolutionPrinter()
    status = solver.solve(model, solution_printer)

    # Print solution
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print()
        # Header with actual dates
        print("          " + " ".join(build_date_labels(START_DATE, num_days)))
        for e in range(num_employees):
            schedule = ""
            for d in range(num_days):
                for s in range(num_shifts):
                    if solver.boolean_value(work[e, s, d]):
                        schedule += shifts[s] + " "
            print(f"worker {e}: {schedule}")
        print()
        print("Penalties:")
        for i, var in enumerate(obj_bool_vars):
            if solver.boolean_value(var):
                penalty = obj_bool_coeffs[i]
                if penalty > 0:
                    print(f"  {var.name} violated, penalty={penalty}")
                else:
                    print(f"  {var.name} fulfilled, gain={-penalty}")
        for i, var in enumerate(obj_int_vars):
            if solver.value(var) > 0:
                print(f"  {var.name} violated by {solver.value(var)}, linear penalty={obj_int_coeffs[i]}")

        # Coverage gap report with dates
        print("\nCoverage gaps (people missing):")
        any_gap = False
        dl = build_date_labels(START_DATE, num_days)
        for (s, d), var in shortage_vars.items():
            gap = solver.value(var)
            if gap > 0:
                any_gap = True
                print(f"  {dl[d]} | shift {shifts[s]}: missing {gap}")
        if not any_gap:
            print("  None")

    print()
    print(solver.response_stats())
    return solver.response_stats()

def demand_for_day_and_shift(
    weekday_demand_template: list[tuple[int, ...]],
    start_sat_index: int,
    d: int,
    s: int,
) -> int:
    """
    Demand for absolute day d and working shift s (s>=1).
    weekday_demand_template is ordered Sat..Fri (length 7).
    """
    sat_idx = (start_sat_index + d) % 7
    return weekday_demand_template[sat_idx][s - 1]


def build_date_labels(start: date, num_days: int) -> list[str]:
    """Return compact labels like 'Sat 01-Nov' for the horizon."""
    return [(start + timedelta(days=d)).strftime("%a %d-%b") for d in range(num_days)]

def add_fair_share(
    model: cp_model.CpModel,
    totals_per_employee: list[cp_model.IntVar],
    *,
    fairness_cost: int,
    prefix: str,
    max_total: int,
) -> tuple[list[cp_model.IntVar], list[int]]:
    """Penalize |total_e - avg| to balance workload across employees.

    We minimize sum_e |n * total_e - sum_totals|, which is equivalent to
    minimizing the deviation from the (fractional) average without division.
    """
    n = len(totals_per_employee)

    sum_totals = model.new_int_var(0, n * max_total, f"{prefix}:sum")
    model.add(sum_totals == sum(totals_per_employee))

    cost_vars: list[cp_model.IntVar] = []
    cost_coeffs: list[int] = []

    for idx, t in enumerate(totals_per_employee):
        # dev_e = | n * t - sum_totals |
        tmp = model.new_int_var(-n * max_total, n * max_total, f"{prefix}:tmp_e{idx}")
        model.add(tmp == n * t - sum_totals)
        dev = model.new_int_var(0, n * max_total, f"{prefix}:dev_e{idx}")
        model.add_abs_equality(dev, tmp)
        cost_vars.append(dev)
        cost_coeffs.append(fairness_cost)

    return cost_vars, cost_coeffs

def sat_index_from_pyweekday(py_w: int) -> int:
    """Map Python weekday Mon..Sun=0..6 to Sat..Fri=0..6 indexing."""
    return (py_w + 2) % 7


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
