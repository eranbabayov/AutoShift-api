CREATE TABLE company (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE employee (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    role_name VARCHAR(100) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    FOREIGN KEY (company_name) REFERENCES company(company_name) ON DELETE CASCADE,
    FOREIGN KEY (role_name) REFERENCES roles(role_name)
);

CREATE TABLE shift_types(
    id INT AUTO_INCREMENT PRIMARY KEY,
    type_name VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE optional_employee_constraints(
    id INT AUTO_INCREMENT PRIMARY KEY,
    constraint_name VARCHAR(255) NOT NULL,
    val INT
);

CREATE TABLE actual_employee_constraints(
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT,
    constraint_id INT NOT NULL,
    FOREIGN KEY (constraint_id) REFERENCES optional_employee_constraints(id) ON DELETE CASCADE
);


CREATE TABLE shift_constraints(
    id INT AUTO_INCREMENT PRIMARY KEY,
    constraint_name VARCHAR(255) NOT NULL UNIQUE,
    shift_type_name VARCHAR(255) NOT NULL,
    val INT,
    FOREIGN KEY (shift_type_name) REFERENCES shift_types(type_name) ON DELETE CASCADE
);
