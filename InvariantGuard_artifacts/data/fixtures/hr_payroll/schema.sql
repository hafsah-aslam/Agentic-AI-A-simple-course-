CREATE TABLE departments (department_id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE employees (
    employee_id INTEGER PRIMARY KEY,
    department_id INTEGER NOT NULL REFERENCES departments(department_id) ON DELETE RESTRICT,
    manager_id INTEGER REFERENCES employees(employee_id) ON DELETE SET NULL,
    name TEXT NOT NULL,
    salary_cents INTEGER NOT NULL CHECK (salary_cents >= 0)
);
CREATE TABLE projects (project_id INTEGER PRIMARY KEY, name TEXT NOT NULL, budget_cents INTEGER NOT NULL CHECK (budget_cents >= 0));
CREATE TABLE employee_projects (employee_id INTEGER REFERENCES employees(employee_id) ON DELETE CASCADE, project_id INTEGER REFERENCES projects(project_id) ON DELETE CASCADE, allocation INTEGER NOT NULL CHECK (allocation BETWEEN 0 AND 100), PRIMARY KEY (employee_id, project_id));
CREATE TABLE payroll (payroll_id INTEGER PRIMARY KEY, employee_id INTEGER NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE, net_cents INTEGER NOT NULL CHECK (net_cents >= 0));
CREATE TABLE audit_events (event_id INTEGER PRIMARY KEY, detail TEXT NOT NULL);
CREATE TABLE benefit_plans (
    benefit_id INTEGER PRIMARY KEY,
    plan_code TEXT NOT NULL UNIQUE,
    monthly_cents INTEGER NOT NULL CHECK (monthly_cents >= 0)
);
CREATE TABLE employee_benefits (
    employee_id INTEGER REFERENCES employees(employee_id) ON DELETE CASCADE,
    benefit_id INTEGER REFERENCES benefit_plans(benefit_id) ON DELETE RESTRICT,
    enrolled_on DATE NOT NULL,
    PRIMARY KEY (employee_id, benefit_id)
);
CREATE TABLE leave_requests (
    leave_id INTEGER PRIMARY KEY,
    employee_id INTEGER NOT NULL REFERENCES employees(employee_id) ON DELETE CASCADE,
    starts_on DATE NOT NULL,
    ends_on DATE NOT NULL,
    status TEXT NOT NULL CHECK (status IN ('pending', 'approved', 'rejected')),
    CHECK (ends_on >= starts_on)
);
CREATE TABLE payroll_tax_lines (
    payroll_id INTEGER REFERENCES payroll(payroll_id) ON DELETE CASCADE,
    tax_code TEXT NOT NULL,
    amount_cents INTEGER NOT NULL CHECK (amount_cents >= 0),
    PRIMARY KEY (payroll_id, tax_code)
);
