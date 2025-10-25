from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Date
from sqlalchemy.orm import relationship, declarative_base
import enum

from schema import DesiredOption

Base = declarative_base()


class Company(Base):
    __tablename__ = "company"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False, unique=True)

    employees = relationship("Employee", back_populates="company")
    shift_types = relationship("CompanyShiftType", back_populates="company")


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(100), nullable=False, unique=True)

    employees = relationship("Employee", back_populates="role")


class Employee(Base):
    __tablename__ = "employee"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    company_id = Column(Integer, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)

    company = relationship("Company", back_populates="employees")
    role = relationship("Role", back_populates="employees")
    shift_requests = relationship("ShiftRequest", back_populates="employee")
    actual_constraints = relationship("ActualEmployeeConstraint", back_populates="employee")


class ShiftTypes(Base):
    __tablename__ = "shift_types"
    id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String(100), nullable=False, unique=True)

    shift_constraints = relationship("ShiftConstraint", back_populates="shift_type")
    shift_requests = relationship("ShiftRequest", back_populates="shift_type")
    company_shift_types = relationship("CompanyShiftType", back_populates="shift_type")


class ShiftConstraint(Base):
    __tablename__ = "shift_constraints"
    id = Column(Integer, primary_key=True, index=True)
    shift_type_id = Column(Integer, ForeignKey("shift_types.id", ondelete="CASCADE"))
    hard_min = Column(Integer, nullable=True)
    soft_min = Column(Integer, nullable=True)
    min_penalty = Column(Integer, nullable=True)
    soft_max = Column(Integer, nullable=True)
    hard_max = Column(Integer, nullable=True)
    max_penalty = Column(Integer, nullable=True)

    shift_type = relationship("ShiftTypes", back_populates="shift_constraints")


class OptionalEmployeeConstraint(Base):
    __tablename__ = "optional_employee_constraints"
    id = Column(Integer, primary_key=True, index=True)
    constraint_name = Column(String(255), nullable=False)
    val = Column(Integer, nullable=True)

    actual_constraints = relationship("ActualEmployeeConstraint", back_populates="constraint")


class ActualEmployeeConstraint(Base):
    __tablename__ = "actual_employee_constraints"
    id = Column(Integer, primary_key=True, index=True)
    constraint_id = Column(Integer, ForeignKey("optional_employee_constraints.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employee.id", ondelete="CASCADE"), nullable=False)

    constraint = relationship("OptionalEmployeeConstraint", back_populates="actual_constraints")
    employee = relationship("Employee", back_populates="actual_constraints")


class ShiftRequest(Base):
    __tablename__ = "shift_request"

    id = Column(Integer, primary_key=True, autoincrement=True)
    employee_id = Column(Integer, ForeignKey("employee.id", ondelete="CASCADE"), nullable=False)
    shift_type_id = Column(Integer, ForeignKey("shift_types.id", ondelete="CASCADE"), nullable=False)
    shift_date = Column(Date, nullable=False)
    desired = Column(Enum(DesiredOption), nullable=False)
    weight = Column(Integer, nullable=False)

    employee = relationship("Employee", back_populates="shift_requests")
    shift_type = relationship("ShiftTypes", back_populates="shift_requests")


class CompanyShiftType(Base):
    __tablename__ = "company_shift_types"
    id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("company.id", ondelete="CASCADE"), nullable=False)
    shift_type_id = Column(Integer, ForeignKey("shift_types.id", ondelete="CASCADE"), nullable=False)

    company = relationship("Company", back_populates="shift_types")
    shift_type = relationship("ShiftTypes", back_populates="company_shift_types")

class WeeklyCoverDemands(Base):
    __tablename__ = "weekly_cover_demands"
    id = Column(Integer, primary_key=True, index=True)
    weekday = Column(Enum('Sun','Mon','Tue','Wed','Thu','Fri','Sat'), nullable=False)
    shift_type_id = Column(Integer, ForeignKey("shift_types.id", ondelete="CASCADE"), nullable=False)
    demand = Column(Integer, nullable=False)


class PenalizedTransitions(Base):
    __tablename__ = "penalized_transitions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    from_shift_id = Column(Integer, ForeignKey("shift_types.id", ondelete="CASCADE"), nullable=False)
    to_shift_id = Column(Integer, ForeignKey("shift_types.id", ondelete="CASCADE"), nullable=False)
    penalty = Column(Integer, nullable=False)

    from_shift = relationship("ShiftTypes", foreign_keys=[from_shift_id])
    to_shift = relationship("ShiftTypes", foreign_keys=[to_shift_id])
