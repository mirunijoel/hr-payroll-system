INSERT INTO teams (name) VALUES
    ('Engineering'),
    ('Sales'),
    ('People Ops');

-- team_id: 1 = Engineering, 2 = Sales, 3 = People Ops
INSERT INTO employees (name, role, team_id, manager_id, start_date, salary, employment_type, is_active) VALUES
    ('Asha Kumar', 'Head of Engineering', 1, NULL, '2019-01-15', 9000, 'full_time', 1),
    ('Ben Ortiz', 'Engineering Manager', 1, 1, '2020-03-01', 7000, 'full_time', 1),
    ('Chloe Tan', 'Software Engineer', 1, 2, '2022-06-10', 5000, 'full_time', 1),
    ('David Osei', 'Software Engineer', 1, 2, '2023-01-05', 4200, 'full_time', 1),
    ('Elena Petrova', 'Sales Lead', 2, NULL, '2018-11-01', 6500, 'full_time', 1),
    ('Farid Hassan', 'Account Executive', 2, 5, '2021-09-15', 3800, 'full_time', 1),
    ('Grace Lin', 'People Ops Manager', 3, NULL, '2019-05-20', 6000, 'full_time', 1),
    ('Hassan Ali', 'HR Coordinator', 3, 7, '2024-07-01', 3200, 'part_time', 1),
    ('Ivy Chen', 'Contract Designer', 1, 2, '2026-07-10', 4500, 'contract', 1);

-- employee_id: 3 = Chloe Tan, 4 = David Osei, 6 = Farid Hassan, 8 = Hassan Ali, 9 = Ivy Chen
-- decided_by: 2 = Ben Ortiz, 7 = Grace Lin
INSERT INTO leave_requests (employee_id, leave_type, start_date, end_date, status, requested_at, decided_at, decided_by, reason) VALUES
    (3, 'paid', '2026-07-03', '2026-07-05', 'approved', '2026-06-20 09:00:00', '2026-06-21 10:15:00', 2, 'Family trip'),
    (6, 'unpaid', '2026-07-14', '2026-07-16', 'approved', '2026-06-30 14:00:00', '2026-07-01 08:30:00', 5, 'Personal time off'),
    (4, 'unpaid', '2026-07-28', '2026-07-30', 'pending', '2026-07-25 11:00:00', NULL, NULL, 'Moving apartments'),
    (9, 'sick', '2026-07-26', '2026-07-26', 'pending', '2026-07-25 07:45:00', NULL, NULL, 'Feeling unwell'),
    (8, 'sick', '2026-06-20', '2026-06-21', 'rejected', '2026-06-19 16:00:00', '2026-06-19 17:30:00', 7, 'Team was already short-staffed that week');
