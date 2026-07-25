let payrollSelectedRunId = null;

function renderPayroll() {
  const container = document.getElementById('view-payroll');
  container.innerHTML = `
    <div class="card">
      <h2>Generate payroll</h2>
      <form class="inline-form" id="payroll-generate-form">
        <div class="form-errors" id="payroll-generate-errors"></div>
        <div class="field"><label>Period start</label><input type="date" name="period_start" required></div>
        <div class="field"><label>Period end</label><input type="date" name="period_end" required></div>
        <div class="field"><button type="submit" class="primary">Generate payroll</button></div>
      </form>
    </div>
    <div class="card">
      <h2>Payroll runs</h2>
      <div id="payroll-runs-container"></div>
    </div>
    <div class="card">
      <h2>Payslips</h2>
      <div id="payroll-payslips-container"><div class="empty-state">Select a payroll run above to see its payslips.</div></div>
    </div>
  `;

  document.getElementById('payroll-generate-form').addEventListener('submit', async (event) => {
    event.preventDefault();
    const form = event.target;
    const errorsBox = document.getElementById('payroll-generate-errors');
    errorsBox.textContent = '';

    try {
      const run = await apiPost('/payroll/runs', {
        period_start: form.period_start.value,
        period_end: form.period_end.value,
      });
      payrollSelectedRunId = run.id;
      loadPayrollRuns();
      renderPayslips(run);
    } catch (error) {
      errorsBox.textContent = error.message;
    }
  });

  loadPayrollRuns();
}

async function loadPayrollRuns() {
  const container = document.getElementById('payroll-runs-container');
  renderLoading(container);

  try {
    const runs = await apiGet('/payroll/runs');
    if (runs.length === 0) {
      renderEmpty(container, 'No payroll runs generated yet.');
      return;
    }

    container.innerHTML = `
      <table>
        <thead><tr><th>Period</th><th>Generated at</th><th></th></tr></thead>
        <tbody>${runs.map(payrollRunRow).join('')}</tbody>
      </table>
    `;

    container.querySelectorAll('[data-view-run]').forEach((button) => {
      button.addEventListener('click', () => selectPayrollRun(Number(button.dataset.viewRun)));
    });

    if (payrollSelectedRunId) {
      selectPayrollRun(payrollSelectedRunId);
    }
  } catch (error) {
    renderError(container, error);
  }
}

function payrollRunRow(run) {
  return `
    <tr>
      <td>${escapeHtml(run.period_start)} to ${escapeHtml(run.period_end)}</td>
      <td>${escapeHtml(run.generated_at)}</td>
      <td><button type="button" class="secondary" data-view-run="${run.id}">View payslips</button></td>
    </tr>
  `;
}

async function selectPayrollRun(runId) {
  payrollSelectedRunId = runId;
  const container = document.getElementById('payroll-payslips-container');
  renderLoading(container);

  try {
    const run = await apiGet(`/payroll/runs/${runId}`);
    renderPayslips(run);
  } catch (error) {
    renderError(container, error);
  }
}

function renderPayslips(run) {
  const container = document.getElementById('payroll-payslips-container');
  if (!run.payslips || run.payslips.length === 0) {
    renderEmpty(container, 'No payslips in this run.');
    return;
  }

  container.innerHTML = `
    <h3>${escapeHtml(run.period_start)} to ${escapeHtml(run.period_end)}</h3>
    <table>
      <thead>
        <tr>
          <th>Employee</th><th class="numeric">Gross</th><th class="numeric">Tax</th>
          <th class="numeric">Social security</th><th class="numeric">Net</th>
          <th class="numeric">Unpaid days</th><th>Notes</th>
        </tr>
      </thead>
      <tbody>${run.payslips.map(payslipRow).join('')}</tbody>
    </table>
  `;
}

function payslipRow(payslip) {
  return `
    <tr>
      <td>${escapeHtml(payslip.employee_name)}</td>
      <td class="numeric">${formatCurrency(payslip.gross_pay)}</td>
      <td class="numeric">${formatCurrency(payslip.tax_deduction)}</td>
      <td class="numeric">${formatCurrency(payslip.social_security_deduction)}</td>
      <td class="numeric">${formatCurrency(payslip.net_pay)}</td>
      <td class="numeric">${payslip.unpaid_days}</td>
      <td>${escapeHtml(payslip.notes || '')}</td>
    </tr>
  `;
}
