async function renderDashboard() {
  const container = document.getElementById('view-dashboard');
  container.innerHTML = `
    <div class="stat-row" id="dashboard-stats"></div>
    <div class="dashboard-grid">
      <div class="card">
        <h2>Pending approvals</h2>
        <div id="dashboard-pending-container"></div>
      </div>
      <div class="card">
        <h2>Who's out</h2>
        <div id="dashboard-whos-out-container"></div>
      </div>
      <div class="card">
        <h2>Leave taken this year</h2>
        <p style="font-size:12px;color:var(--text-muted);margin:-6px 0 12px;">
          Approved leave days used since January 1st, by type. There is no leave
          allowance or balance tracked in this system yet, so this is usage, not
          a remaining balance.
        </p>
        <div id="dashboard-leave-taken-container"></div>
      </div>
      <div class="card">
        <h2>Recent payroll runs</h2>
        <div id="dashboard-payroll-container"></div>
      </div>
    </div>
  `;

  const statsEl = document.getElementById('dashboard-stats');
  const pendingEl = document.getElementById('dashboard-pending-container');
  const whosOutEl = document.getElementById('dashboard-whos-out-container');
  const leaveTakenEl = document.getElementById('dashboard-leave-taken-container');
  const payrollEl = document.getElementById('dashboard-payroll-container');

  [statsEl, pendingEl, whosOutEl, leaveTakenEl, payrollEl].forEach(renderLoading);

  try {
    const [leaveRequests, employees, payrollRuns] = await Promise.all([
      apiGet('/leave'),
      apiGet('/employees'),
      apiGet('/payroll/runs'),
    ]);

    renderDashboardStats(statsEl, leaveRequests, employees);
    renderPendingApprovals(pendingEl, leaveRequests);
    renderWhosOut(whosOutEl, leaveRequests);
    renderLeaveTaken(leaveTakenEl, leaveRequests, employees);
    renderRecentPayroll(payrollEl, payrollRuns);
  } catch (error) {
    [statsEl, pendingEl, whosOutEl, leaveTakenEl, payrollEl].forEach((el) => renderError(el, error));
  }
}

function todayString() {
  return new Date().toISOString().slice(0, 10);
}

function renderDashboardStats(container, leaveRequests, employees) {
  const today = todayString();
  const pendingCount = leaveRequests.filter((request) => request.status === 'pending').length;
  const outTodayCount = leaveRequests.filter(
    (request) => request.status === 'approved' && request.start_date <= today && request.end_date >= today
  ).length;

  container.innerHTML = `
    <div class="stat-tile"><div class="value">${pendingCount}</div><div class="label">Pending approvals</div></div>
    <div class="stat-tile"><div class="value">${outTodayCount}</div><div class="label">Out today</div></div>
    <div class="stat-tile"><div class="value">${employees.length}</div><div class="label">Active employees</div></div>
  `;
}

function renderPendingApprovals(container, leaveRequests) {
  const pending = leaveRequests.filter((request) => request.status === 'pending');
  if (pending.length === 0) {
    renderEmpty(container, 'No pending approvals.');
    return;
  }

  container.innerHTML = `<ul>${pending
    .map(
      (request) => `
        <li style="margin-bottom:8px;">
          <strong>${escapeHtml(request.employee_name)}</strong> - ${escapeHtml(request.leave_type)},
          ${escapeHtml(request.start_date)} to ${escapeHtml(request.end_date)}
          ${request.is_short_notice ? '<span class="badge badge-warning">Short notice</span>' : ''}
          ${request.is_stale ? '<span class="badge badge-warning">Stale</span>' : ''}
        </li>
      `
    )
    .join('')}</ul>`;
}

function renderWhosOut(container, leaveRequests) {
  const today = todayString();
  const in14Days = new Date();
  in14Days.setDate(in14Days.getDate() + 14);
  const in14DaysStr = in14Days.toISOString().slice(0, 10);

  const approved = leaveRequests.filter((request) => request.status === 'approved');
  const outNow = approved.filter((request) => request.start_date <= today && request.end_date >= today);
  const upcoming = approved.filter((request) => request.start_date > today && request.start_date <= in14DaysStr);

  if (outNow.length === 0 && upcoming.length === 0) {
    renderEmpty(container, 'No one is out, or scheduled to be out in the next two weeks.');
    return;
  }

  const listItem = (request) =>
    `<li>${escapeHtml(request.employee_name)}: ${escapeHtml(request.start_date)} to ${escapeHtml(request.end_date)} (${escapeHtml(request.leave_type)})</li>`;

  const section = (title, items) =>
    items.length === 0 ? '' : `<h3>${title}</h3><ul>${items.map(listItem).join('')}</ul>`;

  container.innerHTML = section('Out now', outNow) + section('Next 14 days', upcoming);
}

function daysBetweenInclusive(startDateString, endDateString) {
  const start = new Date(`${startDateString}T00:00:00Z`);
  const end = new Date(`${endDateString}T00:00:00Z`);
  return Math.round((end - start) / 86400000) + 1;
}

function renderLeaveTaken(container, leaveRequests, employees) {
  const year = new Date().getFullYear();
  const yearStart = `${year}-01-01`;
  const yearEnd = `${year}-12-31`;

  const totals = {};
  employees.forEach((employee) => {
    totals[employee.id] = { name: employee.name, paid: 0, unpaid: 0, sick: 0 };
  });

  leaveRequests
    .filter((request) => request.status === 'approved' && totals[request.employee_id])
    .forEach((request) => {
      const clippedStart = request.start_date < yearStart ? yearStart : request.start_date;
      const clippedEnd = request.end_date > yearEnd ? yearEnd : request.end_date;
      if (clippedEnd < clippedStart) return;
      totals[request.employee_id][request.leave_type] += daysBetweenInclusive(clippedStart, clippedEnd);
    });

  const rows = Object.values(totals).filter((row) => row.paid + row.unpaid + row.sick > 0);

  if (rows.length === 0) {
    renderEmpty(container, 'No approved leave taken this year yet.');
    return;
  }

  container.innerHTML = `
    <table>
      <thead><tr><th>Employee</th><th class="numeric">Paid</th><th class="numeric">Unpaid</th><th class="numeric">Sick</th></tr></thead>
      <tbody>${rows
        .map(
          (row) => `
            <tr>
              <td>${escapeHtml(row.name)}</td>
              <td class="numeric">${row.paid}</td>
              <td class="numeric">${row.unpaid}</td>
              <td class="numeric">${row.sick}</td>
            </tr>
          `
        )
        .join('')}</tbody>
    </table>
  `;
}

function renderRecentPayroll(container, payrollRuns) {
  if (payrollRuns.length === 0) {
    renderEmpty(container, 'No payroll runs generated yet.');
    return;
  }

  const recent = [...payrollRuns].sort((a, b) => b.period_start.localeCompare(a.period_start)).slice(0, 5);
  container.innerHTML = `<ul>${recent
    .map((run) => `<li>${escapeHtml(run.period_start)} to ${escapeHtml(run.period_end)}</li>`)
    .join('')}</ul>`;
}
