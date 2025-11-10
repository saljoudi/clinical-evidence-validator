/**
 * OCEV Dashboard JavaScript
 */
let currentTaskId = null;

// Chart instances
const charts = {};

// Initialize
document.addEventListener('DOMContentLoaded', function() {
    setupEventListeners();
    console.log('OCEV Dashboard loaded');
});

function setupEventListeners() {
    // CSV Form
    document.getElementById('csvForm').addEventListener('submit', handleCsvSubmit);
    
    // FHIR Form
    document.getElementById('fhirForm').addEventListener('submit', handleFhirSubmit);
    
    // Synthetic Form
    document.getElementById('syntheticForm').addEventListener('submit', handleSyntheticSubmit);
    
    // Download buttons
    document.getElementById('downloadPdf').addEventListener('click', () => downloadReport('pdf'));
    document.getElementById('downloadJson').addEventListener('click', () => downloadReport('json'));
    document.getElementById('downloadTtl').addEventListener('click', () => downloadReport('ttl'));
}

async function handleCsvSubmit(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('csvFile');
    const evidenceType = document.getElementById('evidenceType').value;
    
    if (!fileInput.files[0]) {
        alert('Please select a CSV file');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    formData.append('evidence_type', evidenceType);
    
    await submitValidation('/api/validate/csv', formData);
}

async function handleFhirSubmit(e) {
    e.preventDefault();
    
    const fileInput = document.getElementById('fhirFile');
    
    if (!fileInput.files[0]) {
        alert('Please select a FHIR JSON file');
        return;
    }
    
    const formData = new FormData();
    formData.append('file', fileInput.files[0]);
    
    await submitValidation('/api/validate/fhir', formData);
}

async function handleSyntheticSubmit(e) {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('n_samples', document.getElementById('sampleSize').value);
    formData.append('evidence_type', document.getElementById('synthEvidenceType').value);
    
    const seed = document.getElementById('seed').value;
    if (seed) {
        formData.append('seed', seed);
    }
    
    await submitValidation('/api/generate/synthetic', formData);
}

async function submitValidation(endpoint, formData) {
    // Show loading
    showLoading(true);
    hideResults();
    
    try {
        const response = await fetch(endpoint, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        currentTaskId = result.task_id;
        
        // Fetch detailed results
        const detailsResponse = await fetch(`/api/results/${currentTaskId}`);
        const details = await detailsResponse.json();
        
        displayResults(details);
        
    } catch (error) {
        console.error('Validation error:', error);
        alert('Validation failed: ' + error.message);
    } finally {
        showLoading(false);
    }
}

function showLoading(show) {
    const indicator = document.getElementById('loadingIndicator');
    indicator.classList.toggle('hidden', !show);
}

function hideResults() {
    document.getElementById('resultsPanel').classList.add('hidden');
}

function displayResults(results) {
    const panel = document.getElementById('resultsPanel');
    panel.classList.remove('hidden');
    
    const scores = results.scores;
    
    // Update score displays
    document.getElementById('integrityScore').textContent = scores.integrity.toFixed(2);
    document.getElementById('fairnessScore').textContent = scores.fairness.toFixed(2);
    document.getElementById('fhirScore').textContent = scores.fhir_compliance.toFixed(2);
    document.getElementById('overallScore').textContent = scores.overall.toFixed(2);
    
    // Create gauge charts
    createGaugeChart('integrityGauge', scores.integrity, '#3B82F6');
    createGaugeChart('fairnessGauge', scores.fairness, '#10B981');
    createGaugeChart('fhirGauge', scores.fhir_compliance, '#8B5CF6');
    createGaugeChart('overallGauge', scores.overall, '#F59E0B');
    
    // Display feedback
    displayFeedback(results);
}

function createGaugeChart(canvasId, score, color) {
    const canvas = document.getElementById(canvasId);
    const ctx = canvas.getContext('2d');
    
    // Destroy existing chart
    if (charts[canvasId]) {
        charts[canvasId].destroy();
    }
    
    // Create gauge
    charts[canvasId] = new Chart(ctx, {
        type: 'doughnut',
        data: {
            datasets: [{
                data: [score, 1 - score],
                backgroundColor: [color, '#E5E7EB'],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '75%',
            plugins: {
                legend: { display: false },
                tooltip: { enabled: false }
            }
        }
    });
}

function displayFeedback(results) {
    const feedbackPanel = document.getElementById('feedbackPanel');
    const validation = results.validation_results;
    
    // Simple feedback generation
    let feedback = '';
    
    if (validation.conforms) {
        feedback += '<div class="bg-green-50 border-l-4 border-green-400 p-4 mb-4">';
        feedback += '<p class="text-green-800"><strong>✓ Excellent:</strong> Evidence conforms to all SHACL constraints.</p>';
        feedback += '</div>';
    } else {
        feedback += '<div class="bg-yellow-50 border-l-4 border-yellow-400 p-4 mb-4">';
        feedback += `<p class="text-yellow-800"><strong>⚠ Issues Found:</strong> ${validation.violations} violations detected.</p>`;
        feedback += '</div>';
    }
    
    // Add constraint summary
    feedback += '<div class="bg-blue-50 p-4 rounded">';
    feedback += `<p class="text-blue-800">Constraints: ${validation.passing_constraints}/${validation.total_constraints} passing</p>`;
    feedback += '</div>';
    
    feedbackPanel.innerHTML = feedback;
}

function downloadReport(format) {
    if (!currentTaskId) {
        alert('No validation results to download');
        return;
    }
    
    const endpoint = `/api/report/${currentTaskId}/${format}`;
    
    // Trigger download
    fetch(endpoint)
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `validation_report_${currentTaskId}.${format}`;
            document.body.appendChild(a);
            a.click();
            a.remove();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Download error:', error);
            alert('Download failed');
        });
}