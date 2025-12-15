// CarMax Data Classification Platform - Frontend Logic

let elementsFile = null;
let subjectsFile = null;

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
    if (tabName === 'classify') loadCatalogs();
    if (tabName === 'review') loadReview();
    if (tabName === 'taxonomy') checkTaxonomyStatus();
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
        const catalogs = await response.json();

        const select = document.getElementById('catalog-select');
        select.innerHTML = '<option value="">Select catalog...</option>';

        catalogs.forEach(cat => {
            const option = document.createElement('option');
            option.value = cat.name;
            option.textContent = cat.name;
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
        const schemas = await response.json();

        const select = document.getElementById('schema-select');
        select.innerHTML = '<option value="">Select schema...</option>';

        schemas.forEach(schema => {
            const option = document.createElement('option');
            option.value = schema.name;
            option.textContent = schema.name;
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
        const classifications = await response.json();

        if (!classifications || classifications.length === 0) {
            listEl.innerHTML = '<p style="color: #64748b; text-align: center; padding: 40px;">No pending classifications</p>';
            return;
        }

        listEl.innerHTML = classifications.map(c => `
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

// File upload handling
const fileUploadZone = document.getElementById('file-upload-zone');

fileUploadZone.addEventListener('click', () => {
    if (!elementsFile) {
        document.getElementById('elements-file').click();
    } else {
        document.getElementById('subjects-file').click();
    }
});

fileUploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUploadZone.classList.add('dragover');
});

fileUploadZone.addEventListener('dragleave', () => {
    fileUploadZone.classList.remove('dragover');
});

fileUploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUploadZone.classList.remove('dragover');

    const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.xlsx') || f.name.endsWith('.xls'));

    if (files.length > 0 && !elementsFile) {
        elementsFile = files[0];
        if (files[1]) subjectsFile = files[1];
        updateFileDisplay();
    }
});

function handleFileSelect() {
    const elementsInput = document.getElementById('elements-file');
    const subjectsInput = document.getElementById('subjects-file');

    if (elementsInput.files[0]) elementsFile = elementsInput.files[0];
    if (subjectsInput.files[0]) subjectsFile = subjectsInput.files[0];

    updateFileDisplay();
}

function updateFileDisplay() {
    const display = document.getElementById('file-names');
    const btn = document.getElementById('upload-btn');

    if (elementsFile && subjectsFile) {
        display.innerHTML = `
            <div>✓ Elements file: ${elementsFile.name}</div>
            <div>✓ Subjects file: ${subjectsFile.name}</div>
        `;
        btn.style.display = 'block';
    } else if (elementsFile) {
        display.textContent = `Elements file: ${elementsFile.name} (Need: Personal Data file)`;
        btn.style.display = 'none';
    }
}

// Upload taxonomy
async function uploadTaxonomy() {
    if (!elementsFile || !subjectsFile) {
        showMessage('taxonomy', 'error', 'Please select both files');
        return;
    }

    const spinner = document.getElementById('taxonomy-spinner');
    const btn = document.getElementById('upload-btn');

    spinner.style.display = 'block';
    btn.disabled = true;
    btn.textContent = 'Importing...';

    try {
        const formData = new FormData();
        formData.append('elements_file', elementsFile);
        formData.append('subjects_file', subjectsFile);
        formData.append('version', '1.0');

        const response = await fetch('/api/admin/import-taxonomy', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (data.success) {
            showMessage('taxonomy', 'success', `✓ Taxonomy imported! ${data.elements_imported} elements, ${data.tags_created} tags created.`);
            checkTaxonomyStatus();
            checkSystemStatus();
            loadDashboard();

            // Reset
            elementsFile = null;
            subjectsFile = null;
            document.getElementById('file-names').innerHTML = '';
            btn.style.display = 'none';
        } else {
            showMessage('taxonomy', 'error', `Import failed: ${data.error}`);
        }
    } catch (error) {
        showMessage('taxonomy', 'error', `Error: ${error.message}`);
    } finally {
        spinner.style.display = 'none';
        btn.disabled = false;
        btn.textContent = 'Import Taxonomy';
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
