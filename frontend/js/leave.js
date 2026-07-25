let leaveStatusFilter = '';
let leaveActingAs = '';
let leaveShowForm = false;

const LEAVE_STATUS_BADGE = { pending: 'badge-warning', approved: 'badge-good', rejected: 'badge-critical' };
const LEAVE_PAST_TENSE = { approve: 'approved', reject: 'rejected' };

function renderLeave() {
  const container = document.getElementById('view-leave');
  container.innerHTML = `
    <div class="card">
      <h2>Leave requests</h2>
      <div class="controls-row">
        <label>Status
          <select id="leave-status-filter">
            <option value="">All</option>
            <option value="pending">Pending</option>
            <option value="approved">Approved</option>
            <option value="rejected">Rejected</option>
          </select>
        </label>
        <label>Acting as
          <select id="leave-acting-as"><option value="">Loading...</option></select>
        </label>
        <button type="button" class="secondary" id="leave-toggle-form">Submit leave request</button>
      </div>
      <div id="leave-message"></div>
      <div id="leave-form-container"></div>
      <div id="leave-list-container"></div>
    </div>
  `;

  const statusFilter = document.getElementById('leave-status-filter');
  statusFilter.value = leaveStatusFilter;
  statusFilter.addEventListener('change', (event) => {
    leaveStatusFilter = event.target.value;
    loadLeaveList();
  });

  document.getElementById('leave-toggle-form').addEventListener('click', () => {
    leaveShowForm = !leaveShowForm;
    renderLeaveForm();
  });

  loadActingAsOptions();
  renderLeaveForm();
  loadLeaveList();
}

async function loadActingAsOptions() {
  const select = document.getElementById('leave-acting-as');
  try {
    const employees = await apiGet('/employees');
    select.innerHTML =
      '<option value="">Select who is deciding...</option>' +
      employees.map((employee) => `<option value="${employee.id}">${escapeHtml(employee.name)}</option>`).join('');
    select.value = leaveActingAs;
    select.addEventListener('change', (event) => {
      leaveActingAs = event.target.value;
    });
  } catch (error) {
    select.innerHTML = '<option value="">Could not load employees</option>';
  }
}

async function renderLeaveForm() {
  const container = document.getElementById('leave-form-container');
  if (!leaveShowForm) {
    container.innerHTML = '';
    return;
  }

  renderLoading(container);

  let employees;
  try {
    employees = await apiGet('/employees');
  } catch (error) {
    renderError(container, error);
    return;
  }

  container.innerHTML = `
    <form class="inline-form" id="leave-form">
      <div class="form-errors" id="leave-form-errors"></div>
      <div class="field">
        <label>Employee</label>
        <select name="employee_id" required>
          ${employees.map((employee) => `<option value="${employee.id}">${escapeHtml(employee.name)}</option>`).join('')}
        </select>
      </div>
      <div class="field">
        <label>Leave type</label>
        <select name="leave_type">
          <option value="paid">Paid</option>
          <option value="unpaid">Unpaid</option>
          <option value="sick">Sick</option>
        </select>
      </div>
      <div class="field"><label>Start date</label><input type="date" name="start_date" required></div>
      <div class="field"><label>End date</label><input type="date" name="end_date" required></div>
      <div class="field full-width"><label>Reason</label><textarea name="reason" rows="2"></textarea></div>
      <div class="field full-width"><button type="submit" class="primary">Submit request</button></div>
    </form>
  `;

  document.getElementById('leave-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.target;
    const errorsBox = document.getElementById('leave-form-errors');
    errorsBox.textContent = '';

    const payload = {
      employee_id: Number(form.employee_id.value),
      leave_type: form.leave_type.value,
      start_date: form.start_date.value,
      end_date: form.end_date.value,
      reason: form.reason.value || null,
    };

    try {
      await apiPost('/leave', payload);
      leaveShowForm = false;
      renderLeaveForm();
      loadLeaveList();
      showLeaveMessage('Leave request submitted.', 'good');
    } catch (error) {
      errorsBox.textContent = error.message;
    }
  });
}

async function loadLeaveList() {
  const container = document.getElementById('leave-list-container');
  renderLoading(container);

  try {
    const query = leaveStatusFilter ? `?status=${leaveStatusFilter}` : '';
    const requests = await apiGet(`/leave${query}`);
    if (requests.length === 0) {
      renderEmpty(container, 'No leave requests match this filter.');
      return;
    }

    container.innerHTML = `
      <table>
        <thead>
          <tr>
            <th>Employee</th><th>Type</th><th>Dates</th><th>Status</th><th>Flags</th><th>Reason</th><th></th>
          </tr>
        </thead>
        <tbody>${requests.map(leaveRow).join('')}</tbody>
      </table>
    `;

    container.querySelectorAll('[data-decide]').forEach((button) => {
      button.addEventListener('click', () => handleDecision(button.dataset.decide, button.dataset.action));
    });
  } catch (error) {
    renderError(container, error);
  }
}

function leaveRow(leaveRequest) {
  const statusClass = LEAVE_STATUS_BADGE[leaveRequest.status] || 'badge-neutral';

  const flags = [];
  if (leaveRequest.is_short_notice) flags.push('<span class="badge badge-warning">Short notice</span>');
  if (leaveRequest.is_stale) flags.push('<span class="badge badge-warning">Stale</span>');

  const actions =
    leaveRequest.status === 'pending'
      ? `
        <button type="button" class="primary" data-decide="${leaveRequest.id}" data-action="approve">Approve</button>
        <button type="button" class="secondary" data-decide="${leaveRequest.id}" data-action="reject">Reject</button>
      `
      : '';

  return `
    <tr>
      <td>${escapeHtml(leaveRequest.employee_name)}</td>
      <td>${escapeHtml(leaveRequest.leave_type)}</td>
      <td>${escapeHtml(leaveRequest.start_date)} to ${escapeHtml(leaveRequest.end_date)}</td>
      <td><span class="badge ${statusClass}">${escapeHtml(leaveRequest.status)}</span></td>
      <td>${flags.join(' ')}</td>
      <td>${escapeHtml(leaveRequest.reason || '')}</td>
      <td>${actions}</td>
    </tr>
  `;
}

async function handleDecision(requestId, action) {
  if (!leaveActingAs) {
    showLeaveMessage('Select who is deciding first (Acting as).', 'critical');
    return;
  }

  try {
    const result = await apiPost(`/leave/${requestId}/${action}`, { decided_by: Number(leaveActingAs) });
    if (result.coverage_warning) {
      showLeaveMessage(result.coverage_warning, 'warning');
    } else {
      showLeaveMessage(`Request ${LEAVE_PAST_TENSE[action]}.`, 'good');
    }
    loadLeaveList();
  } catch (error) {
    showLeaveMessage(error.message, 'critical');
  }
}

function showLeaveMessage(text, kind) {
  document.getElementById('leave-message').innerHTML = `<div class="badge badge-${kind}">${escapeHtml(text)}</div>`;
}
