const leasingForm = document.getElementById('leasing-form');
const leasingTableBody = document.getElementById('leasing-table');
const employeeForm = document.getElementById('employee-form');
const employeeTableBody = document.getElementById('employee-table');
const overheadInputs = {
  office: document.getElementById('office-cost'),
  utilities: document.getElementById('utilities-cost'),
  management: document.getElementById('management-cost'),
};

const summaryElements = {
  leasing: document.getElementById('summary-leasing'),
  payroll: document.getElementById('summary-payroll'),
  overheads: document.getElementById('summary-overheads'),
  total: document.getElementById('summary-total'),
  taxDeductible: document.getElementById('summary-tax-deductible'),
};

const leasingCategories = {
  equipment: {
    label: 'Sprzęt (100% kosztów)',
    taxRate: 1,
  },
  car_full: {
    label: 'Samochód (100% kosztów)',
    taxRate: 1,
  },
  car_half: {
    label: 'Samochód (50% kosztów)',
    taxRate: 0.5,
  },
};

const leasingItems = [];
const employeeItems = [];
const overheads = {
  office: 0,
  utilities: 0,
  management: 0,
};

leasingForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const description = document.getElementById('leasing-description').value.trim();
  const category = document.getElementById('leasing-category').value;
  const amount = parseFloat(document.getElementById('leasing-amount').value);

  if (!description || Number.isNaN(amount) || amount < 0) {
    return;
  }

  leasingItems.push({
    id: createId(),
    description,
    category,
    amount,
  });

  leasingForm.reset();
  document.getElementById('leasing-category').value = 'equipment';
  renderLeasingTable();
  updateSummary();
});

employeeForm.addEventListener('submit', (event) => {
  event.preventDefault();
  const name = document.getElementById('employee-name').value.trim();
  const grossValue = parseFloat(document.getElementById('employee-gross').value);

  if (!name || Number.isNaN(grossValue) || grossValue < 0) {
    return;
  }

  const payroll = calculatePolishPayroll(grossValue);

  employeeItems.push({
    id: createId(),
    name,
    gross: grossValue,
    payroll,
  });

  employeeForm.reset();
  renderEmployeeTable();
  updateSummary();
});

Object.entries(overheadInputs).forEach(([key, input]) => {
  input.addEventListener('input', () => {
    const value = parseFloat(input.value);
    overheads[key] = Number.isNaN(value) || value < 0 ? 0 : value;
    updateSummary();
  });
});

function renderLeasingTable() {
  leasingTableBody.innerHTML = '';

  if (!leasingItems.length) {
    leasingTableBody.appendChild(createEmptyRow(5, 'Brak dodanych leasingów.'));
    return;
  }

  leasingItems.forEach((item) => {
    const categoryInfo = leasingCategories[item.category];
    const deductible = item.amount * categoryInfo.taxRate;

    const row = document.createElement('tr');

    row.innerHTML = `
      <td>${escapeHtml(item.description)}</td>
      <td><span class="badge">${categoryInfo.label}</span></td>
      <td>${formatPLN(item.amount)}</td>
      <td>${formatPLN(deductible)}</td>
      <td><button class="remove-button" data-remove-leasing="${item.id}">Usuń</button></td>
    `;

    leasingTableBody.appendChild(row);
  });
}

function renderEmployeeTable() {
  employeeTableBody.innerHTML = '';

  if (!employeeItems.length) {
    employeeTableBody.appendChild(createEmptyRow(6, 'Brak dodanych pracowników.'));
    return;
  }

  employeeItems.forEach((employee) => {
    const { payroll } = employee;
    const row = document.createElement('tr');

    const contributionsTooltip = `Składki społeczne: ${formatPLN(payroll.social)}\nSkładka zdrowotna: ${formatPLN(payroll.health)}`;

    row.innerHTML = `
      <td>${escapeHtml(employee.name)}</td>
      <td>${formatPLN(employee.gross)}</td>
      <td>${formatPLN(payroll.net)}</td>
      <td>${formatPLN(payroll.tax)}</td>
      <td title="${contributionsTooltip}">${formatPLN(payroll.totalContributions)}</td>
      <td><button class="remove-button" data-remove-employee="${employee.id}">Usuń</button></td>
    `;

    employeeTableBody.appendChild(row);
  });
}

function updateSummary() {
  const leasingTotals = leasingItems.reduce(
    (acc, item) => {
      const categoryInfo = leasingCategories[item.category];
      const deductible = item.amount * categoryInfo.taxRate;
      acc.gross += item.amount;
      acc.deductible += deductible;
      return acc;
    },
    { gross: 0, deductible: 0 },
  );

  const payrollTotals = employeeItems.reduce(
    (acc, employee) => {
      acc.gross += employee.gross;
      acc.net += employee.payroll.net;
      acc.tax += employee.payroll.tax;
      return acc;
    },
    { gross: 0, net: 0, tax: 0 },
  );

  const otherCosts = overheads.office + overheads.utilities + overheads.management;

  const totalCosts = leasingTotals.gross + payrollTotals.gross + otherCosts;
  const taxDeductible = leasingTotals.deductible + payrollTotals.gross + otherCosts;

  summaryElements.leasing.textContent = formatPLN(leasingTotals.gross);
  summaryElements.payroll.textContent = formatPLN(payrollTotals.gross);
  summaryElements.overheads.textContent = formatPLN(otherCosts);
  summaryElements.total.textContent = formatPLN(totalCosts);
  summaryElements.taxDeductible.textContent = formatPLN(taxDeductible);
}

function calculatePolishPayroll(gross) {
  const pension = gross * 0.0976;
  const disability = gross * 0.015;
  const sickness = gross * 0.0245;
  const social = pension + disability + sickness;

  const healthBase = Math.max(0, gross - social);
  const health = healthBase * 0.09;

  const standardCosts = 250;
  const taxableBase = Math.max(0, gross - social - standardCosts);
  const firstThreshold = 120000 / 12;

  let incomeTax;
  if (taxableBase <= firstThreshold) {
    incomeTax = taxableBase * 0.12;
  } else {
    incomeTax = firstThreshold * 0.12 + (taxableBase - firstThreshold) * 0.32;
  }

  const taxRelief = 300;
  incomeTax = Math.max(0, incomeTax - taxRelief);

  const net = gross - social - health - incomeTax;

  return {
    net: roundCurrency(net),
    social: roundCurrency(social),
    health: roundCurrency(health),
    tax: roundCurrency(incomeTax),
    totalContributions: roundCurrency(social + health),
  };
}

function createEmptyRow(colspan, message) {
  const row = document.createElement('tr');
  const cell = document.createElement('td');
  cell.colSpan = colspan;
  cell.textContent = message;
  cell.style.textAlign = 'center';
  cell.style.color = '#657786';
  row.appendChild(cell);
  return row;
}

function roundCurrency(value) {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

function formatPLN(value) {
  return `${roundCurrency(value).toLocaleString('pl-PL', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })} PLN`;
}

function escapeHtml(value) {
  return value
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

function handleTableActions(event) {
  const { target } = event;
  if (target.matches('button[data-remove-leasing]')) {
    const id = target.getAttribute('data-remove-leasing');
    const index = leasingItems.findIndex((item) => item.id === id);
    if (index !== -1) {
      leasingItems.splice(index, 1);
      renderLeasingTable();
      updateSummary();
    }
  }

  if (target.matches('button[data-remove-employee]')) {
    const id = target.getAttribute('data-remove-employee');
    const index = employeeItems.findIndex((item) => item.id === id);
    if (index !== -1) {
      employeeItems.splice(index, 1);
      renderEmployeeTable();
      updateSummary();
    }
  }
}

function createId() {
  if (typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function') {
    return crypto.randomUUID();
  }
  return `id-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

leasingTableBody.addEventListener('click', handleTableActions);
employeeTableBody.addEventListener('click', handleTableActions);

// Initialize empty states
renderLeasingTable();
renderEmployeeTable();
updateSummary();
