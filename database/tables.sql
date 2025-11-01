CREATE TABLE company (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL UNIQUE,
);

CREATE TABLE shift_request (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    shift_type_id INT NOT NULL,
    shift_date INT NOT NULL,
    weight INT NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employee(id) ON DELETE CASCADE,
    FOREIGN KEY (shift_type_id) REFERENCES shift_types(id) ON DELETE CASCADE
);

CREATE TABLE roles (
    id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE employee (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    role_id INT NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,
    FOREIGN KEY (role_id) REFERENCES roles(id) ON DELETE CASCADE
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

CREATE TABLE weekly_sum_constraints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shift_type_id INT NOT NULL,
    hard_min INT,
    soft_min INT,
    min_penalty INT,
    soft_max INT,
    hard_max INT,
    max_penalty INT,
    FOREIGN KEY (shift_type_id) REFERENCES shift_types(id) ON DELETE CASCADE
);

CREATE TABLE actual_employee_constraints(
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    constraint_id INT NOT NULL,
    FOREIGN KEY (constraint_id) REFERENCES optional_employee_constraints(id) ON DELETE CASCADE
);

CREATE TABLE company_shift_types (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    shift_type_id INT NOT NULL,
    FOREIGN KEY (company_id) REFERENCES company(id) ON DELETE CASCADE,
    FOREIGN KEY (shift_type_id) REFERENCES shift_types(id) ON DELETE CASCADE
);


CREATE TABLE shift_constraints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shift_type_id INT NOT NULL,
    hard_min INT,
    soft_min INT,
    min_penalty INT,
    soft_max INT,
    hard_max INT,
    max_penalty INT,
    FOREIGN KEY (shift_type_id) REFERENCES shift_types(id) ON DELETE CASCADE
);

CREATE TABLE fixed_assignments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    shift_type_id INT NOT NULL,
    shift_date DATE NOT NULL,
    FOREIGN KEY (employee_id) REFERENCES employee(id),
    FOREIGN KEY (shift_type_id) REFERENCES shift_types(id)
);

CREATE TABLE penalized_transitions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    from_shift_id INT NOT NULL,
    to_shift_id INT NOT NULL,
    penalty INT NOT NULL,
    FOREIGN KEY (from_shift_id) REFERENCES shift_types(id),
    FOREIGN KEY (to_shift_id) REFERENCES shift_types(id)
);

CREATE TABLE weekly_cover_demands (
    id INT AUTO_INCREMENT PRIMARY KEY,
    weekday ENUM('Sun','Mon','Tue','Wed','Thu','Fri','Sat') NOT NULL,
    shift_type_id INT NOT NULL,
    demand INT NOT NULL,
    FOREIGN KEY (shift_type_id) REFERENCES shift_types(id) ON DELETE CASCADE
);


CREATE TABLE excess_cover_penalties (
    id INT AUTO_INCREMENT PRIMARY KEY,
    shift_type_id INT NOT NULL,
    penalty INT NOT NULL,
    FOREIGN KEY (shift_type_id) REFERENCES shift_types(id)
);
CREATE INDEX idx_shift_request_emp_date ON shift_request(employee_id, shift_date);
CREATE INDEX idx_fixed_assignments_emp_date ON fixed_assignments(employee_id, shift_date);
