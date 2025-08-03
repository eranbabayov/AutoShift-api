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
    company_id = Column(Integer, ForeignKey("company.id"))
    role_id = Column(Integer, ForeignKey("roles.id"))

    company = relationship("Company", back_populates="employees")
    role = relationship("Role", back_populates="employees")
