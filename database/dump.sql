PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE
);
INSERT INTO teams VALUES(1,'Engineering');
INSERT INTO teams VALUES(2,'Sales');
INSERT INTO teams VALUES(3,'People Ops');
CREATE TABLE employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    role TEXT NOT NULL,
    team_id INTEGER NOT NULL,
    manager_id INTEGER,
    start_date TEXT NOT NULL,
    salary REAL NOT NULL,
    employment_type TEXT NOT NULL CHECK (employment_type IN ('full_time', 'part_time', 'contract')),
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    FOREIGN KEY (team_id) REFERENCES teams(id),
    FOREIGN KEY (manager_id) REFERENCES employees(id)
);
INSERT INTO employees VALUES(1,'Asha Kumar','Head of Engineering',1,NULL,'2019-01-15',9000.0,'full_time',1,'2026-07-25 22:22:34');
INSERT INTO employees VALUES(2,'Ben Ortiz','Engineering Manager',1,1,'2020-03-01',7000.0,'full_time',1,'2026-07-25 22:22:34');
INSERT INTO employees VALUES(3,'Chloe Tan','Software Engineer',1,2,'2022-06-10',5000.0,'full_time',1,'2026-07-25 22:22:34');
INSERT INTO employees VALUES(4,'David Osei','Software Engineer',1,2,'2023-01-05',4200.0,'full_time',1,'2026-07-25 22:22:34');
INSERT INTO employees VALUES(5,'Elena Petrova','Sales Lead',2,NULL,'2018-11-01',6500.0,'full_time',1,'2026-07-25 22:22:34');
INSERT INTO employees VALUES(6,'Farid Hassan','Account Executive',2,5,'2021-09-15',3800.0,'full_time',1,'2026-07-25 22:22:34');
INSERT INTO employees VALUES(7,'Grace Lin','People Ops Manager',3,NULL,'2019-05-20',6000.0,'full_time',1,'2026-07-25 22:22:34');
INSERT INTO employees VALUES(8,'Hassan Ali','HR Coordinator',3,7,'2024-07-01',3200.0,'part_time',1,'2026-07-25 22:22:34');
INSERT INTO employees VALUES(9,'Ivy Chen','Contract Designer',1,2,'2026-07-10',4500.0,'contract',1,'2026-07-25 22:22:34');
CREATE TABLE leave_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id INTEGER NOT NULL,
    leave_type TEXT NOT NULL CHECK (leave_type IN ('paid', 'unpaid', 'sick')),
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    requested_at TEXT NOT NULL DEFAULT (datetime('now')),
    decided_at TEXT,
    decided_by INTEGER,
    reason TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees(id),
    FOREIGN KEY (decided_by) REFERENCES employees(id)
);
INSERT INTO leave_requests VALUES(1,3,'paid','2026-07-03','2026-07-05','approved','2026-06-20 09:00:00','2026-06-21 10:15:00',2,'Family trip');
INSERT INTO leave_requests VALUES(2,6,'unpaid','2026-07-14','2026-07-16','approved','2026-06-30 14:00:00','2026-07-01 08:30:00',5,'Personal time off');
INSERT INTO leave_requests VALUES(3,4,'unpaid','2026-07-28','2026-07-30','pending','2026-07-25 11:00:00',NULL,NULL,'Moving apartments');
INSERT INTO leave_requests VALUES(4,9,'sick','2026-07-26','2026-07-26','pending','2026-07-25 07:45:00',NULL,NULL,'Feeling unwell');
INSERT INTO leave_requests VALUES(5,8,'sick','2026-06-20','2026-06-21','rejected','2026-06-19 16:00:00','2026-06-19 17:30:00',7,'Team was already short-staffed that week');
CREATE TABLE payroll_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_start TEXT NOT NULL,
    period_end TEXT NOT NULL,
    generated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
INSERT INTO payroll_runs VALUES(1,'2026-07-01','2026-07-31','2026-07-25 22:22:34');
CREATE TABLE payslips (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    payroll_run_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    gross_pay REAL NOT NULL,
    tax_deduction REAL NOT NULL,
    social_security_deduction REAL NOT NULL,
    net_pay REAL NOT NULL,
    unpaid_days INTEGER NOT NULL DEFAULT 0,
    notes TEXT,
    FOREIGN KEY (payroll_run_id) REFERENCES payroll_runs(id),
    FOREIGN KEY (employee_id) REFERENCES employees(id)
);
INSERT INTO payslips VALUES(1,1,1,9000.0,900.0,540.0,7560.0,0,NULL);
INSERT INTO payslips VALUES(2,1,2,7000.0,700.0,420.0,5880.0,0,NULL);
INSERT INTO payslips VALUES(3,1,3,5000.0,500.0,300.0,4200.0,0,NULL);
INSERT INTO payslips VALUES(4,1,4,4200.0,420.0,252.0,3528.0,0,NULL);
INSERT INTO payslips VALUES(5,1,5,6500.0,650.0,390.0,5460.0,0,NULL);
INSERT INTO payslips VALUES(6,1,6,3432.260000000000218,343.2300000000000181,205.9399999999999978,2883.090000000000145,3,NULL);
INSERT INTO payslips VALUES(7,1,7,6000.0,600.0,360.0,5040.0,0,NULL);
INSERT INTO payslips VALUES(8,1,8,3200.0,320.0,192.0,2688.0,0,NULL);
INSERT INTO payslips VALUES(9,1,9,3193.550000000000181,319.3600000000000136,191.6100000000000137,2682.579999999999928,0,NULL);
INSERT INTO sqlite_sequence VALUES('teams',3);
INSERT INTO sqlite_sequence VALUES('employees',9);
INSERT INTO sqlite_sequence VALUES('leave_requests',5);
INSERT INTO sqlite_sequence VALUES('payroll_runs',1);
INSERT INTO sqlite_sequence VALUES('payslips',9);
CREATE INDEX idx_employees_team ON employees(team_id);
CREATE INDEX idx_employees_manager ON employees(manager_id);
CREATE INDEX idx_leave_requests_employee ON leave_requests(employee_id);
CREATE INDEX idx_leave_requests_status ON leave_requests(status);
CREATE INDEX idx_payslips_run ON payslips(payroll_run_id);
CREATE INDEX idx_payslips_employee ON payslips(employee_id);
COMMIT;
