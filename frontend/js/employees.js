let employeesIncludeInactive = false;
let employeesShowAddForm = false;

function renderEmployees() {
  const container = document.getElementById('view-employees');
  container.innerHTML = `
    <div class="card">
      <h2>Employees</h2>
      <div class="controls-row">
        <label><input type="checkbox" id="employees-include-inactive"> Show deactivated employees</label>
        <button type="button" class="secondary" id="employees-toggle-add">Add employee</button>
      </div>
      <div id="employees-add-form-container"></div>
      <div id="employees-table-container"></div>
    </div>
    <div class="card">
      <h2>Org chart</h2>
      <div id="org-chart-container"></div>
    </div>
  `;

  const includeInactiveCheckbox = document.getElementById('employees-include-inactive');
  includeInactiveCheckbox.checked = employeesIncludeInactive;
  includeInactiveCheckbox.addEventListener('change', (event) => {
    employeesIncludeInactive = event.target.checked;
    loadEmployeesTable();
  });

  document.getElementById('employees-toggle-add').addEventListener('click', () => {
    employeesShowAddForm = !employeesShowAddForm;
    renderAddEmployeeForm();
  });

  renderAddEmployeeForm();
  loadEmployeesTable();
  loadOrgChart();
}

async function renderAddEmployeeForm() {
  const container = document.getElementById('employees-add-form-container');
  if (!employeesShowAddForm) {
    container.innerHTML = '';
    return;
  }

  renderLoading(container);

  let teams;
  let managers;
  try {
    [teams, managers] = await Promise.all([apiGet('/teams'), apiGet('/employees')]);
  } catch (error) {
    renderError(container, error);
    return;
  }

  if (teams.length === 0) {
    renderEmpty(container, 'No teams exist yet, an employee needs a team to be created.');
    return;
  }

  container.innerHTML = `
    <form class="inline-form" id="add-employee-form">
      <div class="form-errors" id="add-employee-errors"></div>
      <div class="field"><label>Name</label><input name="name" required></div>
      <div class="field"><label>Role</label><input name="role" required></div>
      <div class="field">
        <label>Team</label>
        <select name="team_id" required>
          ${teams.map((team) => `<option value="${team.id}">${escapeHtml(team.name)}</option>`).join('')}
        </select>
      </div>
      <div class="field">
        <label>Manager (optional)</label>
        <select name="manager_id">
          <option value="">None</option>
          ${managers.map((manager) => `<option value="${manager.id}">${escapeHtml(manager.name)}</option>`).join('')}
        </select>
      </div>
      <div class="field"><label>Start date</label><input type="date" name="start_date" required></div>
      <div class="field"><label>Salary</label><input type="number" name="salary" min="0.01" step="0.01" required></div>
      <div class="field">
        <label>Employment type</label>
        <select name="employment_type">
          <option value="full_time">Full time</option>
          <option value="part_time">Part time</option>
          <option value="contract">Contract</option>
        </select>
      </div>
      <div class="field full-width"><button type="submit" class="primary">Create employee</button></div>
    </form>
  `;

  document.getElementById('add-employee-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.target;
    const errorsBox = document.getElementById('add-employee-errors');
    errorsBox.textContent = '';

    const payload = {
      name: form.name.value,
      role: form.role.value,
      team_id: Number(form.team_id.value),
      manager_id: form.manager_id.value ? Number(form.manager_id.value) : null,
      start_date: form.start_date.value,
      salary: Number(form.salary.value),
      employment_type: form.employment_type.value,
    };

    try {
      await apiPost('/employees', payload);
      employeesShowAddForm = false;
      renderAddEmployeeForm();
      loadEmployeesTable();
      loadOrgChart();
    } catch (error) {
      errorsBox.textContent = error.message;
    }
  });
}

async function loadEmployeesTable() {
  const container = document.getElementById('employees-table-container');
  renderLoading(container);

  try {
    const employees = await apiGet(`/employees?include_inactive=${employeesIncludeInactive}`);
    if (employees.length === 0) {
      renderEmpty(container, 'No employees yet.');
      return;
    }

    container.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Name</th><th>Role</th><th>Team</th><th>Manager</th>
            <th>Start date</th><th class="numeric">Salary</th><th>Type</th><th>Status</th><th></th>
          </tr>
        </thead>
        <tbody>${employees.map(employeeRow).join('')}</tbody>
      </table>
    `;

    container.querySelectorAll('[data-deactivate]').forEach((button) => {
      button.addEventListener('click', async () => {
        if (!confirm('Deactivate this employee? Their payroll history is kept.')) return;
        await apiPost(`/employees/${button.dataset.deactivate}/deactivate`);
        loadEmployeesTable();
        loadOrgChart();
      });
    });
  } catch (error) {
    renderError(container, error);
  }
}

function employeeRow(employee) {
  const statusBadge = employee.is_active
    ? '<span class="badge badge-good">Active</span>'
    : '<span class="badge badge-neutral">Deactivated</span>';

  const action = employee.is_active
    ? `<button type="button" class="secondary" data-deactivate="${employee.id}">Deactivate</button>`
    : '';

  return `
    <tr>
      <td>${escapeHtml(employee.name)}</td>
      <td>${escapeHtml(employee.role)}</td>
      <td>${escapeHtml(employee.team_name)}</td>
      <td>${escapeHtml(employee.manager_name || 'None')}</td>
      <td>${escapeHtml(employee.start_date)}</td>
      <td class="numeric">${formatCurrency(employee.salary)}</td>
      <td>${escapeHtml(employee.employment_type)}</td>
      <td>${statusBadge}</td>
      <td>${action}</td>
    </tr>
  `;
}

async function loadOrgChart() {
  const container = document.getElementById('org-chart-container');
  renderLoading(container);

  try {
    const roots = await apiGet('/employees/org-chart');
    if (roots.length === 0) {
      renderEmpty(container, 'No active employees yet.');
      return;
    }
    container.innerHTML = `<ul class="tree">${roots.map(orgNode).join('')}</ul>`;
  } catch (error) {
    renderError(container, error);
  }
}

function orgNode(node) {
  const children = node.reports && node.reports.length ? `<ul>${node.reports.map(orgNode).join('')}</ul>` : '';
  return `
    <li>
      <span class="node-name">${escapeHtml(node.name)}</span>
      <span class="node-role">${escapeHtml(node.role)}</span>
      ${children}
    </li>
  `;
}
