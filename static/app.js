// CarMax Data Classification Platform - Frontend Logic

// Initialize on page load
document.addEventListener('DOMContentLoaded', () => {
    checkSystemStatus();
    loadDashboard();
    loadCatalogs();
});

// Tab switching
function switchTab(tabName) {
    // Update tab buttons
    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    event.target.classList.add('active');

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
    document.getElementById(`${tabName}-tab`).classList.add('active');

    // Load tab-specific data
    if (tabName === 'dashboard') loadDashboard();
    if (tabName === 'taxonomy') loadTaxonomy();
    if (tabName === 'classify') loadCatalogs();
    if (tabName === 'review') loadReview();
}

// Check system status
async function checkSystemStatus() {
    try {
        const response = await fetch('/api/admin/taxonomy-status');
        const data = await response.json();

        const statusEl = document.getElementById('global-status');
        if (data.initialized) {
            statusEl.textContent = `✓ Ready (${data.stats.elements} elements)`;
            statusEl.style.background = 'rgba(34, 197, 94, 0.3)';
        } else {
            statusEl.textContent = '⚠ Taxonomy Not Initialized';
            statusEl.style.background = 'rgba(251, 191, 36, 0.3)';
        }
    } catch (error) {
        console.error('Status check failed:', error);
    }
}

// Load dashboard stats
async function loadDashboard() {
    try {
        const [taxStatus, dashStats] = await Promise.all([
            fetch('/api/admin/taxonomy-status').then(r => r.json()),
            fetch('/api/dashboard/stats').then(r => r.json())
        ]);

        if (taxStatus.initialized) {
            document.getElementById('stat-elements').textContent = taxStatus.stats.elements || 0;
            document.getElementById('stat-tags').textContent = taxStatus.stats.tags || 0;
        }

        if (dashStats) {
            document.getElementById('stat-classifications').textContent = dashStats.total_classifications || 0;
            document.getElementById('stat-pending').textContent = dashStats.pending_review || 0;
        }
    } catch (error) {
        console.error('Dashboard load failed:', error);
    }
}

// Load catalogs
async function loadCatalogs() {
    try {
        const response = await fetch('/api/catalogs');
        const data = await response.json();

        const select = document.getElementById('catalog-select');
        select.innerHTML = '<option value="">Select catalog...</option>';

        data.catalogs.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat;
            option.textContent = cat;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Catalog load failed:', error);
    }
}

// Load schemas
async function loadSchemas() {
    const catalog = document.getElementById('catalog-select').value;
    if (!catalog) return;

    try {
        const response = await fetch(`/api/schemas?catalog=${catalog}`);
        const data = await response.json();

        const select = document.getElementById('schema-select');
        select.innerHTML = '<option value="">Select schema...</option>';

        data.schemas.forEach(schema => {
            const option = document.createElement('option');
            option.value = schema;
            option.textContent = schema;
            select.appendChild(option);
        });
    } catch (error) {
        console.error('Schema load failed:', error);
    }
}

// Classify columns
async function classifyColumns() {
    const catalog = document.getElementById('catalog-select').value;
    const schema = document.getElementById('schema-select').value;
    const messageEl = document.getElementById('classify-message');
    const spinner = document.getElementById('classify-spinner');

    if (!catalog || !schema) {
        showMessage('classify', 'error', 'Please select both catalog and schema');
        return;
    }

    spinner.style.display = 'block';

    try {
        const response = await fetch('/api/classify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ catalog, schema })
        });

        const data = await response.json();

        if (data.total) {
            showMessage('classify', 'success', `✓ Classified ${data.processed} of ${data.total} columns successfully!`);
            loadDashboard();
        } else {
            showMessage('classify', 'info', 'No unclassified columns found');
        }
    } catch (error) {
        showMessage('classify', 'error', `Error: ${error.message}`);
    } finally {
        spinner.style.display = 'none';
    }
}

// Load review list
async function loadReview() {
    const listEl = document.getElementById('review-list');

    try {
        const response = await fetch('/api/classifications?status=PENDING');
        const data = await response.json();

        if (!data.items || data.items.length === 0) {
            listEl.innerHTML = '<p style="color: #64748b; text-align: center; padding: 40px;">No pending classifications</p>';
            return;
        }

        listEl.innerHTML = data.items.map(c => `
            <div style="border: 1px solid #e2e8f0; border-radius: 6px; padding: 16px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: start;">
                    <div>
                        <strong>${c.catalog_name}.${c.schema_name}.${c.table_name}.${c.column_name}</strong>
                        <div style="margin-top: 8px; color: #64748b; font-size: 14px;">
                            Suggested: <strong>${c.suggested_element}</strong>
                            <span style="color: #3b82f6; margin-left: 12px;">${c.confidence_score}% confidence</span>
                        </div>
                    </div>
                    <div>
                        <button class="btn btn-primary" style="margin-right: 8px;" onclick="approveClassification(${c.id})">Approve</button>
                        <button class="btn btn-secondary" onclick="rejectClassification(${c.id})">Reject</button>
                    </div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Review load failed:', error);
    }
}

// Approve classification
async function approveClassification(id) {
    try {
        await fetch(`/api/classifications/${id}/approve`, { method: 'POST' });
        showMessage('review', 'success', '✓ Classification approved');
        loadReview();
        loadDashboard();
    } catch (error) {
        showMessage('review', 'error', `Error: ${error.message}`);
    }
}

// Reject classification
async function rejectClassification(id) {
    try {
        await fetch(`/api/classifications/${id}/reject`, { method: 'POST' });
        showMessage('review', 'info', 'Classification rejected');
        loadReview();
        loadDashboard();
    } catch (error) {
        showMessage('review', 'error', `Error: ${error.message}`);
    }
}

// Check taxonomy status
async function checkTaxonomyStatus() {
    try {
        const response = await fetch('/api/admin/taxonomy-status');
        const data = await response.json();

        const statsEl = document.getElementById('taxonomy-stats');
        if (data.initialized) {
            statsEl.style.display = 'grid';
            document.getElementById('tax-elements').textContent = data.stats.elements;
            document.getElementById('tax-tags').textContent = data.stats.tags;
            document.getElementById('tax-subjects').textContent = data.stats.subjects;
        } else {
            statsEl.style.display = 'none';
        }
    } catch (error) {
        console.error('Taxonomy status failed:', error);
    }
}

// Helper function to show messages
function showMessage(tab, type, text) {
    const messageEl = document.getElementById(`${tab}-message`);
    messageEl.className = `message ${type}`;
    messageEl.textContent = text;
    messageEl.style.display = 'block';

    setTimeout(() => {
        messageEl.style.display = 'none';
    }, 10000);
}

// ============================================================
// TAXONOMY MANAGEMENT FUNCTIONS
// ============================================================

let allTaxonomyElements = [];
let currentPage = 1;
const elementsPerPage = 20;

// Load taxonomy elements
async function loadTaxonomy(page = 1) {
    currentPage = page;
    const tbody = document.getElementById('taxonomy-table-body');

    try {
        const response = await fetch('/api/taxonomy/elements');
        const data = await response.json();

        allTaxonomyElements = data.elements || [];
        renderTaxonomyTable(allTaxonomyElements);
    } catch (error) {
        console.error('Failed to load taxonomy:', error);
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px; color: #ef4444;">
                    Error loading taxonomy. Please refresh the page.
                </td>
            </tr>
        `;
    }
}

// Render taxonomy table
function renderTaxonomyTable(elements) {
    const tbody = document.getElementById('taxonomy-table-body');

    if (!elements || elements.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="5" style="text-align: center; padding: 40px; color: #64748b;">
                    No data elements found. Click "Add New Element" to get started.
                </td>
            </tr>
        `;
        return;
    }

    // Pagination
    const startIdx = (currentPage - 1) * elementsPerPage;
    const endIdx = startIdx + elementsPerPage;
    const pageElements = elements.slice(startIdx, endIdx);

    tbody.innerHTML = pageElements.map(el => `
        <tr style="border-bottom: 1px solid #e2e8f0;">
            <td style="padding: 12px;">${el.element_name}</td>
            <td style="padding: 12px;">${el.element_category}</td>
            <td style="padding: 12px;">
                <span style="
                    background: ${el.sensitive_flag === 'Yes' ? '#fee2e2' : '#dcfce7'};
                    color: ${el.sensitive_flag === 'Yes' ? '#991b1b' : '#15803d'};
                    padding: 4px 12px;
                    border-radius: 12px;
                    font-size: 12px;
                    font-weight: 600;
                ">${el.sensitive_flag}</span>
            </td>
            <td style="padding: 12px; max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">
                ${el.element_description || '-'}
            </td>
            <td style="padding: 12px;">
                <div style="display: flex; gap: 8px; white-space: nowrap;">
                    <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 13px;" onclick="editElement('${el.element_id}')">Edit</button>
                    <button class="btn btn-secondary" style="padding: 6px 12px; font-size: 13px; background: #fee2e2; color: #991b1b;" onclick="deleteElement('${el.element_id}')">Delete</button>
                </div>
            </td>
        </tr>
    `).join('');

    // Update pagination
    renderPagination(elements.length);
}

// Render pagination
function renderPagination(totalElements) {
    const paginationEl = document.getElementById('taxonomy-pagination');
    const totalPages = Math.ceil(totalElements / elementsPerPage);

    if (totalPages <= 1) {
        paginationEl.innerHTML = '';
        return;
    }

    let html = '';

    // Previous button
    if (currentPage > 1) {
        html += `<button class="btn btn-secondary" onclick="loadTaxonomy(${currentPage - 1})">Previous</button>`;
    }

    // Page numbers
    for (let i = 1; i <= totalPages; i++) {
        if (i === currentPage) {
            html += `<button class="btn btn-primary" style="padding: 8px 12px;">${i}</button>`;
        } else if (i === 1 || i === totalPages || Math.abs(i - currentPage) <= 2) {
            html += `<button class="btn btn-secondary" onclick="loadTaxonomy(${i})">${i}</button>`;
        } else if (Math.abs(i - currentPage) === 3) {
            html += `<span style="padding: 8px;">...</span>`;
        }
    }

    // Next button
    if (currentPage < totalPages) {
        html += `<button class="btn btn-secondary" onclick="loadTaxonomy(${currentPage + 1})">Next</button>`;
    }

    paginationEl.innerHTML = html;
}

// Filter taxonomy
function filterTaxonomy() {
    const searchTerm = document.getElementById('taxonomy-search').value.toLowerCase();

    if (!searchTerm) {
        renderTaxonomyTable(allTaxonomyElements);
        return;
    }

    const filtered = allTaxonomyElements.filter(el =>
        el.element_name.toLowerCase().includes(searchTerm) ||
        el.element_category.toLowerCase().includes(searchTerm) ||
        (el.element_description && el.element_description.toLowerCase().includes(searchTerm))
    );

    currentPage = 1;
    renderTaxonomyTable(filtered);
}

// Show add element form
function showAddElementForm() {
    document.getElementById('add-element-form').style.display = 'block';
    document.getElementById('new-element-name').value = '';
    document.getElementById('new-element-category').value = '';
    document.getElementById('new-element-sensitive').value = 'No';
    document.getElementById('new-element-description').value = '';
}

// Cancel add element
function cancelAddElement() {
    document.getElementById('add-element-form').style.display = 'none';
}

// Save new element
async function saveNewElement() {
    const name = document.getElementById('new-element-name').value.trim();
    const category = document.getElementById('new-element-category').value.trim();
    const sensitive = document.getElementById('new-element-sensitive').value;
    const description = document.getElementById('new-element-description').value.trim();

    if (!name || !category) {
        showMessage('taxonomy', 'error', 'Element name and category are required');
        return;
    }

    try {
        const response = await fetch('/api/taxonomy/elements', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                element_name: name,
                element_category: category,
                sensitive_flag: sensitive,
                element_description: description
            })
        });

        const data = await response.json();

        if (response.ok) {
            showMessage('taxonomy', 'success', 'Element added successfully!');
            cancelAddElement();
            loadTaxonomy();
            checkSystemStatus();
        } else {
            showMessage('taxonomy', 'error', data.error || 'Failed to add element');
        }
    } catch (error) {
        showMessage('taxonomy', 'error', `Error: ${error.message}`);
    }
}

// Edit element - show modal
let currentEditElementId = null;

function editElement(elementId) {
    const element = allTaxonomyElements.find(el => el.element_id === elementId);
    if (!element) return;

    currentEditElementId = elementId;

    // Populate modal fields
    document.getElementById('edit-element-name').value = element.element_name;
    document.getElementById('edit-element-category').value = element.element_category;
    document.getElementById('edit-element-sensitive').value = element.sensitive_flag;
    document.getElementById('edit-element-description').value = element.element_description || '';

    // Show modal
    const modal = document.getElementById('edit-modal');
    modal.style.display = 'flex';
}

function closeEditModal() {
    document.getElementById('edit-modal').style.display = 'none';
    currentEditElementId = null;
}

async function saveEditElement() {
    if (!currentEditElementId) return;

    const newName = document.getElementById('edit-element-name').value.trim();
    const newCategory = document.getElementById('edit-element-category').value.trim();
    const newSensitive = document.getElementById('edit-element-sensitive').value;
    const newDescription = document.getElementById('edit-element-description').value.trim();

    if (!newName || !newCategory) {
        showMessage('taxonomy', 'error', 'Name and category are required');
        return;
    }

    try {
        const response = await fetch(`/api/taxonomy/elements/${currentEditElementId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                element_name: newName,
                element_category: newCategory,
                sensitive_flag: newSensitive,
                element_description: newDescription
            })
        });

        if (response.ok) {
            showMessage('taxonomy', 'success', 'Element updated successfully!');
            closeEditModal();
            loadTaxonomy();
        } else {
            const data = await response.json();
            showMessage('taxonomy', 'error', data.error || 'Failed to update element');
        }
    } catch (error) {
        showMessage('taxonomy', 'error', `Error: ${error.message}`);
    }
}

// Delete element - show modal
let currentDeleteElementId = null;

function deleteElement(elementId) {
    const element = allTaxonomyElements.find(el => el.element_id === elementId);
    if (!element) return;

    currentDeleteElementId = elementId;
    document.getElementById('delete-element-name').textContent = element.element_name;

    // Show modal
    const modal = document.getElementById('delete-modal');
    modal.style.display = 'flex';
}

function closeDeleteModal() {
    document.getElementById('delete-modal').style.display = 'none';
    currentDeleteElementId = null;
}

async function confirmDeleteElement() {
    if (!currentDeleteElementId) return;

    try {
        const response = await fetch(`/api/taxonomy/elements/${currentDeleteElementId}`, {
            method: 'DELETE'
        });

        if (response.ok) {
            showMessage('taxonomy', 'success', 'Element deleted successfully!');
            closeDeleteModal();
            loadTaxonomy();
            checkSystemStatus();
        } else {
            const data = await response.json();
            showMessage('taxonomy', 'error', data.error || 'Failed to delete element');
        }
    } catch (error) {
        showMessage('taxonomy', 'error', `Error: ${error.message}`);
    }
}
