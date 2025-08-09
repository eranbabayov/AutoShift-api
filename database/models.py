from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()


class Company(Base):
    __tablename__ = "company"
    id = Column(Integer, primary_key=True, index=True)
    company_name = Column(String(255), nullable=False, unique=True)
    employees = relationship("Employee", back_populates="company")


class Role(Base):
    __tablename__ = "roles"
    id = Column(Integer, primary_key=True, index=True)
    role_name = Column(String(100), nullable=False, unique=True)
    employees = relationship("Employee", back_populates="role")


class Employee(Base):
    __tablename__ = "employee"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String(255), nullable=False)
    company_name = Column(String(255), ForeignKey("company.company_name"))
    role_name = Column(String(100), ForeignKey("roles.role_name"))

    company = relationship("Company", back_populates="employees")
    role = relationship("Role", back_populates="employees")


class ShiftTypes(Base):
    __tablename__ = "shift_types"
    id = Column(Integer, primary_key=True, index=True)
    type_name = Column(String(100), nullable=False, unique=True)


class ShiftConstraint(Base):
    __tablename__ = "shift_constraints"
    id = Column(Integer, primary_key=True, index=True)
    shift_type_name = Column(String(100), ForeignKey("shift_types.type_name"))
    constraint_name = Column(String(255), nullable=False, unique=True)
    val = Column(Integer, nullable=True)


class OptionalEmployeeConstraint(Base):
    __tablename__ = "optional_employee_constraints"
    id = Column(Integer, primary_key=True, index=True)
    constraint_name = Column(String(255), nullable=False)
    val = Column(Integer, nullable=True)


class ActualEmployeeConstraint(Base):
    __tablename__ = "actual_employee_constraints"
    id = Column(Integer, primary_key=True, index=True)
    constraint_id = Column(Integer, nullable=False)
    employee_id = Column(Integer, nullable=False)
