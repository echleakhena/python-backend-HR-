import sqlite3
from typing import Any

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from database import (
    add_employee,
    get_all_employees,
    get_employee_by_id,
    get_total_payroll_budget,
    initialize_database,
    login_user,
    remove_employee,
    search_employees,
)


app = FastAPI(
    title="HRM System API",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class LoginRequest(BaseModel):
    username: str = Field(min_length=1)
    password: str = Field(min_length=1)


class EmployeeCreate(BaseModel):
    employee_code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=150)
    gender: str | None = None
    phone: str | None = None
    email: str | None = None
    department: str | None = None
    position: str | None = None
    salary: float = Field(default=0, ge=0)


@app.on_event("startup")
def startup_event():
    initialize_database()


@app.get("/")
def home():
    return {
        "message": "HRM System API is running",
    }


@app.post("/api/login")
def login(data: LoginRequest):
    user = login_user(data.username, data.password)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    return {
        "message": "Login successful",
        "user": user,
        "token": f"demo-token-{user['id']}",
    }


@app.get("/api/employees")
def employees(search: str | None = Query(default=None)) -> list[dict[str, Any]]:
    if search:
        return search_employees(search)

    return get_all_employees()


@app.get("/api/employees/{employee_id}")
def employee_detail(employee_id: int):
    employee = get_employee_by_id(employee_id)

    if employee is None:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    return employee


@app.post("/api/employees", status_code=201)
def create_employee(employee: EmployeeCreate):
    try:
        return add_employee(
            employee_code=employee.employee_code,
            name=employee.name,
            gender=employee.gender,
            phone=employee.phone,
            email=employee.email,
            department=employee.department,
            position=employee.position,
            salary=employee.salary,
        )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Employee code or email already exists",
        )


@app.delete("/api/employees/{employee_id}")
def deactivate_employee(employee_id: int):
    removed = remove_employee(employee_id)

    if not removed:
        raise HTTPException(
            status_code=404,
            detail="Employee not found",
        )

    return {
        "message": "Employee removed successfully",
    }


@app.get("/api/payroll/total-budget")
def total_payroll_budget():
    return {
        "total_budget": get_total_payroll_budget(),
    }