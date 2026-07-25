const API_BASE = '/api';

async function apiRequest(method, path, body) {
  const options = { method, headers: {} };
  if (body !== undefined) {
    options.headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE}${path}`, options);
  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const message = (data && (data.error || (data.errors || []).join(', '))) || `Request failed (${response.status})`;
    throw new Error(message);
  }

  return data;
}

function apiGet(path) {
  return apiRequest('GET', path);
}

function apiPost(path, body) {
  return apiRequest('POST', path, body === undefined ? {} : body);
}

function apiPut(path, body) {
  return apiRequest('PUT', path, body === undefined ? {} : body);
}

function escapeHtml(value) {
  const div = document.createElement('div');
  div.textContent = value === null || value === undefined ? '' : String(value);
  return div.innerHTML;
}

function renderLoading(container) {
  container.innerHTML = '<div class="loading-state">Loading...</div>';
}

function renderEmpty(container, message) {
  container.innerHTML = `<div class="empty-state">${escapeHtml(message)}</div>`;
}

function renderError(container, error) {
  container.innerHTML = `<div class="error-state">${escapeHtml(error.message || 'Something went wrong.')}</div>`;
}

function formatCurrency(amount) {
  return Number(amount).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}
