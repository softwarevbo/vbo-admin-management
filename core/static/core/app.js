// Admin & Inventory Management System Client Script

// Global State Variables
let currentTab = 'dashboard-tab';
let employees = [];
let vendors = [];
let bills = [];
let items = [];
let logs = [];

// Chart instances
let monthlyChart = null;
let divisionChart = null;

// Initialization
document.addEventListener('DOMContentLoaded', () => {
    initClock();
    setupTabNavigation();
    
    // Load theme configuration
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (savedTheme === 'light') {
        document.body.classList.add('light-theme');
        updateThemeToggleUI(true);
    } else {
        updateThemeToggleUI(false);
    }
    
    loadAllData();
});

// Real-time Clock
function initClock() {
    const clockEl = document.getElementById('current-datetime');
    const updateTime = () => {
        const now = new Date();
        const options = { 
            weekday: 'short', 
            year: 'numeric', 
            month: 'short', 
            day: 'numeric',
            hour: '2-digit', 
            minute: '2-digit', 
            second: '2-digit',
            hour12: true 
        };
        clockEl.innerHTML = `<i class="fa-regular fa-clock"></i> ${now.toLocaleDateString('en-IN', options)}`;
    };
    updateTime();
    setInterval(updateTime, 1000);
}

// Single Page Tab Navigation
function setupTabNavigation() {
    const navButtons = document.querySelectorAll('.nav-btn');
    const pageTitle = document.getElementById('page-title');
    
    navButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            // Remove active classes
            navButtons.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
            
            // Add active to current
            btn.classList.add('active');
            const tabId = btn.getAttribute('data-tab');
            const panel = document.getElementById(tabId);
            panel.classList.add('active');
            
            // Set header title
            currentTab = tabId;
            const spanText = btn.querySelector('span').innerText;
            pageTitle.innerText = spanText === "Dashboard" ? "Dashboard Overview" : spanText;
            
            // Reload tab data
            loadTabData(tabId);
        });
    });
}

// Load appropriate data based on current tab
function loadTabData(tabId) {
    switch (tabId) {
        case 'dashboard-tab':
            loadStats();
            break;
        case 'bills-tab':
            loadBills();
            loadVendors(); // required for dropdowns in modal
            break;
        case 'items-tab':
            loadItems();
            loadBills();
            loadEmployees();
            break;
        case 'vendors-tab':
            loadVendors();
            break;
        case 'employees-tab':
            loadEmployees();
            break;
        case 'logs-tab':
            loadLogs();
            break;
        case 'stock-tab':
            loadStock();
            break;
    }
}

// Load all background details for dropdown operations
function loadAllData() {
    loadStats();
    loadEmployees();
    loadVendors();
    loadBills();
    loadItems();
    loadLogs();
    loadStock();
}

// Stats & Charts Fetching
async function loadStats() {
    try {
        const res = await fetch('/api/stats/');
        const stats = await res.json();
        
        // Populate stats cards
        document.getElementById('stat-total-amount').innerText = `₹${stats.total_amount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        document.getElementById('stat-total-bills').innerText = stats.total_bills;
        document.getElementById('stat-issued-items').innerText = stats.issued_items;
        document.getElementById('stat-total-employees').innerText = stats.total_employees;
        
        // Update charts
        updateCharts(stats.monthly_data, stats.division_data);
    } catch (err) {
        console.error("Failed to load dashboard statistics:", err);
    }
}

// Chart.js Operations
function updateCharts(monthlyData, divisionData) {
    const isLight = document.body.classList.contains('light-theme');
    const textColor = isLight ? '#111827' : '#f3f4f6';
    const labelColor = isLight ? '#4b5563' : '#9ca3af';
    const gridColor = isLight ? 'rgba(0, 0, 0, 0.06)' : 'rgba(255, 255, 255, 0.05)';
    const chartBorderColor = isLight ? 'rgba(0, 0, 0, 0.1)' : 'rgba(255, 255, 255, 0.1)';

    // 1. Monthly Line Chart
    const monthlyCtx = document.getElementById('monthlyChart').getContext('2d');
    const months = Object.keys(monthlyData);
    const monthlyAmounts = Object.values(monthlyData);
    
    if (monthlyChart) {
        monthlyChart.destroy();
    }
    
    monthlyChart = new Chart(monthlyCtx, {
        type: 'line',
        data: {
            labels: months.length > 0 ? months : ['No Data'],
            datasets: [{
                label: 'Monthly Expenditure (₹)',
                data: monthlyAmounts.length > 0 ? monthlyAmounts : [0],
                borderColor: '#3b82f6',
                backgroundColor: isLight ? 'rgba(59, 130, 246, 0.08)' : 'rgba(59, 130, 246, 0.1)',
                borderWidth: 3,
                tension: 0.3,
                fill: true,
                pointBackgroundColor: '#3b82f6',
                pointHoverRadius: 7
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: textColor, font: { family: 'Outfit' } } }
            },
            scales: {
                x: { grid: { color: gridColor }, ticks: { color: labelColor, font: { family: 'Outfit' } } },
                y: { grid: { color: gridColor }, ticks: { color: labelColor, font: { family: 'Outfit' } } }
            }
        }
    });

    // 2. Division Pie Chart
    const divCtx = document.getElementById('divisionChart').getContext('2d');
    const divisions = Object.keys(divisionData);
    const divisionAmounts = Object.values(divisionData);
    
    if (divisionChart) {
        divisionChart.destroy();
    }
    
    // Generate distinct theme colors
    const colors = ['#3b82f6', '#10b981', '#8b5cf6', '#f59e0b', '#ef4444', '#06b6d4', '#ec4899'];
    
    divisionChart = new Chart(divCtx, {
        type: 'doughnut',
        data: {
            labels: divisions.length > 0 ? divisions : ['No Data'],
            datasets: [{
                data: divisionAmounts.length > 0 ? divisionAmounts : [1],
                backgroundColor: divisionAmounts.length > 0 ? colors.slice(0, divisions.length) : [gridColor],
                borderWidth: 1,
                borderColor: chartBorderColor
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: 'bottom', labels: { color: textColor, font: { family: 'Outfit' } } }
            }
        }
    });
}

// Fetch: Employees
async function loadEmployees() {
    try {
        const res = await fetch('/api/employees/');
        employees = await res.json();
        renderEmployeesTable();
        updateEmployeeDropdowns();
    } catch (err) {
        console.error("Failed to load employees:", err);
    }
}

function renderEmployeesTable() {
    const tbody = document.getElementById('employees-table-body');
    tbody.innerHTML = '';
    
    if (employees.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" class="text-center">No employee records found.</td></tr>`;
        return;
    }

    employees.forEach(emp => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${escapeHTML(emp.employee_id)}</strong></td>
            <td>${escapeHTML(emp.name)}</td>
            <td>${escapeHTML(emp.email)}</td>
            <td>${escapeHTML(emp.mobile)}</td>
            <td><span class="badge info">${escapeHTML(emp.designation)}</span></td>
            <td class="text-center">
                <div class="actions-cell">
                    <button class="btn btn-secondary btn-xs" onclick="editEmployee('${emp.employee_id}')"><i class="fa-solid fa-pen-to-square"></i></button>
                    <button class="btn btn-danger btn-xs" onclick="deleteEmployee('${emp.employee_id}')"><i class="fa-solid fa-trash-can"></i></button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Fetch: Vendors
async function loadVendors() {
    try {
        const res = await fetch('/api/vendors/');
        vendors = await res.json();
        renderVendorsTable();
        updateVendorDropdowns();
    } catch (err) {
        console.error("Failed to load vendors:", err);
    }
}

function renderVendorsTable() {
    const tbody = document.getElementById('vendors-table-body');
    tbody.innerHTML = '';
    
    if (vendors.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center">No vendor bank accounts found.</td></tr>`;
        return;
    }

    vendors.forEach(v => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${v.id}</td>
            <td><strong>${escapeHTML(v.vendor_name)}</strong></td>
            <td>${escapeHTML(v.bank_name)}</td>
            <td><code>${escapeHTML(v.account_number)}</code></td>
            <td>${escapeHTML(v.branch)}</td>
            <td><code>${escapeHTML(v.ifsc_code)}</code></td>
            <td class="text-center">
                <div class="actions-cell">
                    <button class="btn btn-secondary btn-xs" onclick="editVendor(${v.id})"><i class="fa-solid fa-pen-to-square"></i></button>
                    <button class="btn btn-danger btn-xs" onclick="deleteVendor(${v.id})"><i class="fa-solid fa-trash-can"></i></button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Fetch: Bills
async function loadBills() {
    try {
        const res = await fetch('/api/bills/');
        bills = await res.json();
        renderBillsTable();
        updateBillDropdowns();
    } catch (err) {
        console.error("Failed to load bills:", err);
    }
}

function renderBillsTable() {
    const tbody = document.getElementById('bills-table-body');
    tbody.innerHTML = '';
    
    if (bills.length === 0) {
        tbody.innerHTML = `<tr><td colspan="11" class="text-center">No bills registered in system inventory.</td></tr>`;
        return;
    }

    bills.forEach(bill => {
        const processedBadge = bill.processed_date 
            ? `<span class="badge success">${bill.processed_date}</span>`
            : `<span class="badge warning">Pending</span>`;
            
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${bill.sl_no}</td>
            <td><strong>${escapeHTML(bill.vendor_name)}</strong></td>
            <td><code>${escapeHTML(bill.vendor_bill_no)}</code></td>
            <td>${bill.vendor_bill_date}</td>
            <td><span class="badge info">${escapeHTML(bill.div_section)}</span></td>
            <td>${escapeHTML(bill.indent_end_user)}</td>
            <td>${bill.received_date}</td>
            <td>${bill.bill_received_date}</td>
            <td>${processedBadge}</td>
            <td class="text-right font-semibold text-primary-color">₹${bill.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
            <td class="text-center">
                <div class="actions-cell">
                    <button class="btn btn-secondary btn-xs" onclick="editBill(${bill.sl_no})"><i class="fa-solid fa-pen-to-square"></i></button>
                    <button class="btn btn-danger btn-xs" onclick="deleteBill(${bill.sl_no})"><i class="fa-solid fa-trash-can"></i></button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Fetch: Items
async function loadItems() {
    try {
        const res = await fetch('/api/items/');
        items = await res.json();
        renderItemsTable();
    } catch (err) {
        console.error("Failed to load inventory items:", err);
    }
}

function renderItemsTable() {
    const tbody = document.getElementById('items-table-body');
    tbody.innerHTML = '';
    
    if (items.length === 0) {
        tbody.innerHTML = `<tr><td colspan="12" class="text-center">No items recorded in inventory.</td></tr>`;
        return;
    }

    items.forEach(item => {
        const statusBadge = item.issue_status === 'ISSUED'
            ? `<span class="badge danger">Issued</span>`
            : `<span class="badge success">In Stock</span>`;

        const issuedTo = item.employee_name 
            ? `${escapeHTML(item.employee_name)} (<code>${escapeHTML(item.employee_id)}</code>)`
            : '<span class="text-muted">-</span>';
            
        const issueDate = item.issue_date ? item.issue_date : '<span class="text-muted">-</span>';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${item.id}</td>
            <td><strong>${escapeHTML(item.name)}</strong></td>
            <td><small>${escapeHTML(item.description || 'N/A')}</small></td>
            <td>${item.quantity}</td>
            <td>₹${item.unit_price.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
            <td>${item.gst}%</td>
            <td class="text-right">₹${item.amount.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
            <td><code>${escapeHTML(item.bill_no)}</code></td>
            <td>${issuedTo}</td>
            <td>${statusBadge}</td>
            <td>${issueDate}</td>
            <td class="text-center">
                <div class="actions-cell">
                    <button class="btn btn-secondary btn-xs" onclick="editItem(${item.id})"><i class="fa-solid fa-pen-to-square"></i></button>
                    <button class="btn btn-danger btn-xs" onclick="deleteItem(${item.id})"><i class="fa-solid fa-trash-can"></i></button>
                </div>
            </td>
        `;
        tbody.appendChild(tr);
    });
}

// Fetch: Logs
async function loadLogs() {
    try {
        const res = await fetch('/api/logs/');
        logs = await res.json();
        renderLogsTable();
    } catch (err) {
        console.error("Failed to load logs:", err);
    }
}

function renderLogsTable() {
    const tbody = document.getElementById('logs-table-body');
    tbody.innerHTML = '';
    
    if (logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" class="text-center">No system log activity recorded.</td></tr>`;
        return;
    }

    logs.forEach(log => {
        let actionBadgeClass = 'info';
        if (log.action === 'CREATE') actionBadgeClass = 'success';
        if (log.action === 'DELETE') actionBadgeClass = 'danger';
        if (log.action === 'UPDATE') actionBadgeClass = 'warning';

        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><small class="text-muted">${log.timestamp}</small></td>
            <td><span class="badge ${actionBadgeClass}">${log.action}</span></td>
            <td><code>${log.model_name}</code></td>
            <td><code>${log.record_id}</code></td>
            <td><strong>${escapeHTML(log.record_name)}</strong></td>
            <td>
                <button class="btn btn-secondary btn-xs" onclick="viewLogDetail(${log.id})">
                    <i class="fa-solid fa-magnifying-glass-plus"></i> View Changes
                </button>
            </td>
            <td><small>${escapeHTML(log.user)}</small></td>
        `;
        tbody.appendChild(tr);
    });
}

// Dropdown synchronization
function updateVendorDropdowns() {
    const select = document.getElementById('bill-vendor');
    select.innerHTML = '<option value="">-- Choose Vendor --</option>';
    vendors.forEach(v => {
        const opt = document.createElement('option');
        opt.value = v.id;
        opt.innerText = `${v.vendor_name} (${v.bank_name})`;
        select.appendChild(opt);
    });
}

function updateBillDropdowns() {
    const select = document.getElementById('item-bill');
    select.innerHTML = '<option value="">-- Choose Bill --</option>';
    bills.forEach(b => {
        const opt = document.createElement('option');
        opt.value = b.sl_no;
        opt.innerText = `Bill No: ${b.vendor_bill_no} (${b.vendor_name})`;
        select.appendChild(opt);
    });
}

function updateEmployeeDropdowns() {
    const select = document.getElementById('item-employee');
    select.innerHTML = '<option value="">-- Keep in Stock --</option>';
    employees.forEach(emp => {
        const opt = document.createElement('option');
        opt.value = emp.employee_id;
        opt.innerText = `${emp.name} (${emp.employee_id})`;
        select.appendChild(opt);
    });
}

// Modals Open / Close Helpers
function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}

function openModal(id) {
    document.getElementById(id).style.display = 'block';
}

// Clear form helpers
function resetForm(id) {
    document.getElementById(id).reset();
}

// Quick Create handler
function quickAddAction() {
    if (currentTab === 'employees-tab') {
        openEmployeeModal();
    } else if (currentTab === 'vendors-tab') {
        openVendorModal();
    } else if (currentTab === 'items-tab') {
        openItemModal();
    } else {
        openBillModal();
    }
}

// CRUD Save: Employee
function openEmployeeModal(isEdit = false) {
    const modal = document.getElementById('employee-modal');
    const title = document.getElementById('employee-modal-title');
    const empIdField = document.getElementById('emp-id');
    
    resetForm('employee-form');
    title.innerText = isEdit ? "Modify Employee details" : "Add Employee";
    empIdField.disabled = isEdit; // employee id is primary key and immutable
    
    openModal('employee-modal');
}

async function saveEmployee(event) {
    event.preventDefault();
    const id = document.getElementById('emp-id').value;
    const name = document.getElementById('emp-name').value;
    const email = document.getElementById('emp-email').value;
    const mobile = document.getElementById('emp-mobile').value;
    const designation = document.getElementById('emp-designation').value;

    const payload = { employee_id: id, name, email, mobile, designation };
    const isEdit = document.getElementById('emp-id').disabled;
    
    const url = isEdit ? `/api/employees/${id}/` : '/api/employees/';
    const method = isEdit ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        
        if (data.status === 'success') {
            closeModal('employee-modal');
            loadEmployees();
            loadStats();
        } else {
            alert("Error: " + data.message);
        }
    } catch (err) {
        console.error("Save employee error:", err);
    }
}

async function editEmployee(id) {
    try {
        const res = await fetch(`/api/employees/${id}/`);
        const emp = await res.json();
        
        openEmployeeModal(true);
        document.getElementById('emp-id').value = emp.employee_id;
        document.getElementById('emp-name').value = emp.name;
        document.getElementById('emp-email').value = emp.email;
        document.getElementById('emp-mobile').value = emp.mobile;
        document.getElementById('emp-designation').value = emp.designation;
    } catch (err) {
        console.error("Fetch employee error:", err);
    }
}

async function deleteEmployee(id) {
    if (!confirm("Are you sure you want to delete this employee? This will set related item issues to NULL.")) return;
    try {
        const res = await fetch(`/api/employees/${id}/`, { method: 'DELETE' });
        const data = await res.json();
        if (data.status === 'success') {
            loadEmployees();
            loadItems();
            loadStats();
        } else {
            alert(data.message);
        }
    } catch (err) {
        console.error("Delete employee error:", err);
    }
}

// CRUD Save: Vendor
function openVendorModal(isEdit = false) {
    const title = document.getElementById('vendor-modal-title');
    resetForm('vendor-form');
    document.getElementById('vendor-id-field').value = '';
    title.innerText = isEdit ? "Modify Vendor bank details" : "Add Vendor bank details";
    openModal('vendor-modal');
}

async function saveVendor(event) {
    event.preventDefault();
    const id = document.getElementById('vendor-id-field').value;
    const vendor_name = document.getElementById('vendor-name').value;
    const bank_name = document.getElementById('vendor-bank').value;
    const account_number = document.getElementById('vendor-account').value;
    const branch = document.getElementById('vendor-branch').value;
    const ifsc_code = document.getElementById('vendor-ifsc').value;

    const payload = { vendor_name, bank_name, account_number, branch, ifsc_code };
    const url = id ? `/api/vendors/${id}/` : '/api/vendors/';
    const method = id ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
            closeModal('vendor-modal');
            loadVendors();
            loadBills(); // updates bill tables as company name might have changed
            loadStats();
        } else {
            alert(data.message);
        }
    } catch (err) {
        console.error(err);
    }
}

async function editVendor(id) {
    try {
        const res = await fetch(`/api/vendors/${id}/`);
        const v = await res.json();
        openVendorModal(true);
        document.getElementById('vendor-id-field').value = v.id;
        document.getElementById('vendor-name').value = v.vendor_name;
        document.getElementById('vendor-bank').value = v.bank_name;
        document.getElementById('vendor-account').value = v.account_number;
        document.getElementById('vendor-branch').value = v.branch;
        document.getElementById('vendor-ifsc').value = v.ifsc_code;
    } catch (err) {
        console.error(err);
    }
}

async function deleteVendor(id) {
    if (!confirm("Are you sure you want to delete this vendor? This will delete all their registered bills!")) return;
    try {
        const res = await fetch(`/api/vendors/${id}/`, { method: 'DELETE' });
        const data = await res.json();
        if (data.status === 'success') {
            loadVendors();
            loadBills();
            loadItems();
            loadStats();
        } else {
            alert(data.message);
        }
    } catch (err) {
        console.error(err);
    }
}

// CRUD Save: Bill
function openBillModal(isEdit = false) {
    const title = document.getElementById('bill-modal-title');
    resetForm('bill-form');
    document.getElementById('bill-sl-no').value = '';
    title.innerText = isEdit ? "Modify Admin Bill Entry" : "Create Admin Bill Entry";
    
    // Default dates to today
    const today = new Date().toISOString().split('T')[0];
    document.getElementById('bill-date').value = today;
    document.getElementById('bill-received').value = today;
    document.getElementById('bill-received-office').value = today;
    
    openModal('bill-modal');
}

async function saveBill(event) {
    event.preventDefault();
    const id = document.getElementById('bill-sl-no').value;
    const vendor_id = document.getElementById('bill-vendor').value;
    const vendor_bill_no = document.getElementById('bill-no').value;
    const vendor_bill_date = document.getElementById('bill-date').value;
    const div_section = document.getElementById('bill-div').value;
    const indent_end_user = document.getElementById('bill-indent').value;
    const received_date = document.getElementById('bill-received').value;
    const bill_received_date = document.getElementById('bill-received-office').value;
    const processed_date = document.getElementById('bill-processed').value || null;

    const payload = { 
        vendor_id, vendor_bill_no, vendor_bill_date, 
        div_section, indent_end_user, received_date, 
        bill_received_date, processed_date 
    };

    const url = id ? `/api/bills/${id}/` : '/api/bills/';
    const method = id ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
            closeModal('bill-modal');
            loadBills();
            loadItems();
            loadStats();
        } else {
            alert(data.message);
        }
    } catch (err) {
        console.error(err);
    }
}

async function editBill(sl_no) {
    try {
        const res = await fetch(`/api/bills/${sl_no}/`);
        const bill = await res.json();
        openBillModal(true);
        document.getElementById('bill-sl-no').value = bill.sl_no;
        document.getElementById('bill-vendor').value = bill.vendor_id;
        document.getElementById('bill-no').value = bill.vendor_bill_no;
        document.getElementById('bill-date').value = bill.vendor_bill_date;
        document.getElementById('bill-div').value = bill.div_section;
        document.getElementById('bill-indent').value = bill.indent_end_user;
        document.getElementById('bill-received').value = bill.received_date;
        document.getElementById('bill-received-office').value = bill.bill_received_date;
        document.getElementById('bill-processed').value = bill.processed_date || '';
    } catch (err) {
        console.error(err);
    }
}

async function deleteBill(sl_no) {
    if (!confirm("Are you sure you want to delete this bill? All items under this bill will also be deleted!")) return;
    try {
        const res = await fetch(`/api/bills/${sl_no}/`, { method: 'DELETE' });
        const data = await res.json();
        if (data.status === 'success') {
            loadBills();
            loadItems();
            loadStats();
        } else {
            alert(data.message);
        }
    } catch (err) {
        console.error(err);
    }
}

// CRUD Save: Item (With Live Calculations)
function openItemModal(isEdit = false) {
    const title = document.getElementById('item-modal-title');
    resetForm('item-form');
    document.getElementById('item-id-field').value = '';
    title.innerText = isEdit ? "Modify Item details" : "Add Item to Bill";
    
    // Set default calculation displays
    calculateItemTotal();
    openModal('item-modal');
}

// Math calculation formula logic
function calculateItemTotal() {
    const qty = parseInt(document.getElementById('item-qty').value) || 0;
    const price = parseFloat(document.getElementById('item-price').value) || 0.0;
    const gstPercent = parseFloat(document.getElementById('item-gst').value) || 0.0;
    
    const subtotal = qty * price;
    const gstAmount = subtotal * (gstPercent / 100.0);
    const total = subtotal + gstAmount;

    // Display formatted results in calculations box
    document.getElementById('calc-subtotal').innerText = `₹${subtotal.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById('calc-gst-amount').innerText = `₹${gstAmount.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    document.getElementById('calc-total').innerText = `₹${total.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

// Auto-fill dates and change status depending on employee selection
function toggleIssueStatus() {
    const empSelect = document.getElementById('item-employee');
    const issueDateInput = document.getElementById('item-issue-date');
    
    if (empSelect.value) {
        issueDateInput.required = true;
        // set default date to today if empty
        if (!issueDateInput.value) {
            issueDateInput.value = new Date().toISOString().split('T')[0];
        }
    } else {
        issueDateInput.required = false;
        issueDateInput.value = '';
    }
}

async function saveItem(event) {
    event.preventDefault();
    const id = document.getElementById('item-id-field').value;
    const bill_id = document.getElementById('item-bill').value;
    const name = document.getElementById('item-name').value;
    const description = document.getElementById('item-desc').value;
    const quantity = document.getElementById('item-qty').value;
    const unit_price = document.getElementById('item-price').value;
    const gst = document.getElementById('item-gst').value;
    
    const employee_id = document.getElementById('item-employee').value || null;
    const issue_status = employee_id ? 'ISSUED' : 'IN_STOCK';
    const issue_date = employee_id ? document.getElementById('item-issue-date').value : null;

    const payload = { 
        bill_id, name, description, quantity, unit_price, gst,
        employee_id, issue_status, issue_date 
    };

    const url = id ? `/api/items/${id}/` : '/api/items/';
    const method = id ? 'PUT' : 'POST';

    try {
        const res = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.status === 'success') {
            closeModal('item-modal');
            loadItems();
            loadBills(); // updates bill amount totals
            loadStats();
            loadStock();
        } else {
            alert(data.message);
        }
    } catch (err) {
        console.error(err);
    }
}

async function editItem(id) {
    try {
        const res = await fetch(`/api/items/${id}/`);
        const item = await res.json();
        
        openItemModal(true);
        document.getElementById('item-id-field').value = item.id;
        document.getElementById('item-bill').value = item.bill_id;
        document.getElementById('item-name').value = item.name;
        document.getElementById('item-desc').value = item.description;
        document.getElementById('item-qty').value = item.quantity;
        document.getElementById('item-price').value = item.unit_price;
        document.getElementById('item-gst').value = item.gst;
        document.getElementById('item-employee').value = item.employee_id || '';
        document.getElementById('item-issue-date').value = item.issue_date || '';
        
        calculateItemTotal();
        toggleIssueStatus();
    } catch (err) {
        console.error(err);
    }
}

async function deleteItem(id) {
    if (!confirm("Are you sure you want to delete this item?")) return;
    try {
        const res = await fetch(`/api/items/${id}/`, { method: 'DELETE' });
        const data = await res.json();
        if (data.status === 'success') {
            loadItems();
            loadBills(); // recalculates bill amount totals
            loadStats();
            loadStock();
        } else {
            alert(data.message);
        }
    } catch (err) {
        console.error(err);
    }
}

// Log view detail modal populating
function viewLogDetail(id) {
    const log = logs.find(l => l.id === id);
    if (!log) return;

    const actionBadge = document.getElementById('log-detail-action');
    actionBadge.innerText = log.action;
    actionBadge.className = 'badge'; // reset
    if (log.action === 'CREATE') actionBadge.classList.add('success');
    else if (log.action === 'UPDATE') actionBadge.classList.add('warning');
    else if (log.action === 'DELETE') actionBadge.classList.add('danger');

    document.getElementById('log-detail-model').innerText = log.model_name;
    document.getElementById('log-detail-record-id').innerText = log.record_id;
    document.getElementById('log-detail-record-name').innerText = log.record_name;
    document.getElementById('log-detail-timestamp').innerText = log.timestamp;
    
    // Parse and show pretty formatted JSON changes
    try {
        const changesObj = JSON.parse(log.changed_fields);
        document.getElementById('log-detail-diff').innerText = JSON.stringify(changesObj, null, 2);
    } catch (e) {
        document.getElementById('log-detail-diff').innerText = log.changed_fields || "No fields changed.";
    }

    openModal('log-modal');
}

// Client-Side Search Filters
function filterBills() {
    const query = document.getElementById('bill-search').value.toLowerCase();
    const rows = document.querySelectorAll('#bills-table-body tr');
    rows.forEach(row => {
        if (row.cells.length < 2) return;
        const vendor = row.cells[1].innerText.toLowerCase();
        const billNo = row.cells[2].innerText.toLowerCase();
        const div = row.cells[4].innerText.toLowerCase();
        const user = row.cells[5].innerText.toLowerCase();
        
        if (vendor.includes(query) || billNo.includes(query) || div.includes(query) || user.includes(query)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function filterItems() {
    const query = document.getElementById('item-search').value.toLowerCase();
    const rows = document.querySelectorAll('#items-table-body tr');
    rows.forEach(row => {
        if (row.cells.length < 2) return;
        const name = row.cells[1].innerText.toLowerCase();
        const desc = row.cells[2].innerText.toLowerCase();
        const bill = row.cells[7].innerText.toLowerCase();
        const issued = row.cells[8].innerText.toLowerCase();
        const status = row.cells[9].innerText.toLowerCase();
        
        if (name.includes(query) || desc.includes(query) || bill.includes(query) || issued.includes(query) || status.includes(query)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function filterVendors() {
    const query = document.getElementById('vendor-search').value.toLowerCase();
    const rows = document.querySelectorAll('#vendors-table-body tr');
    rows.forEach(row => {
        if (row.cells.length < 2) return;
        const name = row.cells[1].innerText.toLowerCase();
        const bank = row.cells[2].innerText.toLowerCase();
        const acc = row.cells[3].innerText.toLowerCase();
        const branch = row.cells[4].innerText.toLowerCase();
        const ifsc = row.cells[5].innerText.toLowerCase();
        
        if (name.includes(query) || bank.includes(query) || acc.includes(query) || branch.includes(query) || ifsc.includes(query)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function filterEmployees() {
    const query = document.getElementById('employee-search').value.toLowerCase();
    const rows = document.querySelectorAll('#employees-table-body tr');
    rows.forEach(row => {
        if (row.cells.length < 2) return;
        const id = row.cells[0].innerText.toLowerCase();
        const name = row.cells[1].innerText.toLowerCase();
        const email = row.cells[2].innerText.toLowerCase();
        const mobile = row.cells[3].innerText.toLowerCase();
        const designation = row.cells[4].innerText.toLowerCase();
        
        if (id.includes(query) || name.includes(query) || email.includes(query) || mobile.includes(query) || designation.includes(query)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

function filterLogs() {
    const query = document.getElementById('log-search').value.toLowerCase();
    const rows = document.querySelectorAll('#logs-table-body tr');
    rows.forEach(row => {
        if (row.cells.length < 2) return;
        const action = row.cells[1].innerText.toLowerCase();
        const model = row.cells[2].innerText.toLowerCase();
        const name = row.cells[4].innerText.toLowerCase();
        
        if (action.includes(query) || model.includes(query) || name.includes(query)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Utility: Escape HTML string to avoid XSS injections
function escapeHTML(str) {
    if (!str) return '';
    return str.replace(/[&<>'"]/g, 
        tag => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[tag] || tag)
    );
}

// Fetch and render stock inventory
async function loadStock() {
    try {
        const res = await fetch('/api/stock/');
        const stockData = await res.json();
        renderStockTable(stockData);
    } catch (err) {
        console.error("Failed to load stock data:", err);
    }
}

function renderStockTable(stockData) {
    const tbody = document.getElementById('stock-table-body');
    tbody.innerHTML = '';
    
    if (stockData.length === 0) {
        tbody.innerHTML = `<tr><td colspan="5" class="text-center">No stock items in system.</td></tr>`;
        return;
    }
    
    stockData.forEach(item => {
        const tr = document.createElement('tr');
        const stockColor = item.total_in_stock === 0 ? 'text-danger font-semibold' : 'text-primary-color font-semibold';
        
        tr.innerHTML = `
            <td><strong>${escapeHTML(item.name)}</strong></td>
            <td class="text-center">${item.total_purchased}</td>
            <td class="text-center">${item.total_issued}</td>
            <td class="text-center ${stockColor}">${item.total_in_stock}</td>
            <td class="text-right text-accent-color">₹${item.total_value.toLocaleString('en-IN', { minimumFractionDigits: 2 })}</td>
        `;
        tbody.appendChild(tr);
    });
}

function filterStock() {
    const query = document.getElementById('stock-search').value.toLowerCase();
    const rows = document.querySelectorAll('#stock-table-body tr');
    rows.forEach(row => {
        if (row.cells.length < 2) return;
        const name = row.cells[0].innerText.toLowerCase();
        if (name.includes(query)) {
            row.style.display = '';
        } else {
            row.style.display = 'none';
        }
    });
}

// Light & Dark Theme Switcher Logic
function toggleTheme() {
    const isLight = document.body.classList.toggle('light-theme');
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
    updateThemeToggleUI(isLight);
    
    // Refresh statistics & charts to apply new theme-specific colors
    if (currentTab === 'dashboard-tab') {
        loadStats();
    }
}

function updateThemeToggleUI(isLight) {
    const btn = document.getElementById('theme-toggle-btn');
    if (!btn) return;
    if (isLight) {
        btn.innerHTML = `<i class="fa-solid fa-moon"></i> <span>Dark Mode</span>`;
    } else {
        btn.innerHTML = `<i class="fa-solid fa-sun"></i> <span>Light Mode</span>`;
    }
}
