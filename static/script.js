// Dashboard script
document.addEventListener('DOMContentLoaded', function() {
    const detectionForm = document.getElementById('detectionForm');
    const resultDiv = document.getElementById('result');
    const resultText = document.getElementById('resultText');
    const downloadLink = document.getElementById('downloadLink');
    const fileInput = document.getElementById('fileInput');
    const messageTextarea = document.getElementById('message');

    detectionForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = messageTextarea.value.trim();
        const file = fileInput.files[0];
        
        if (!message && !file) {
            alert('Please enter a message or upload an image.');
            return;
        }
        
        if (file) {
            // Upload file for OCR
            const formData = new FormData();
            formData.append('file', file);
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    displayResult(data);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred during analysis.');
            });
        } else {
            // Analyze text
            fetch('/detect', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert(data.error);
                } else {
                    displayResult(data);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('An error occurred during analysis.');
            });
        }
    });

    function displayResult(data) {
        resultText.innerHTML = `
            <strong>Evidence ID:</strong> ${data.evidence_id}<br>
            <strong>Category:</strong> ${data.category}<br>
            <strong>Severity:</strong> <span class="badge bg-${data.severity === 'High' ? 'danger' : data.severity === 'Medium' ? 'warning' : 'success'}">${data.severity}</span><br>
            <strong>Hash:</strong> ${data.hash}<br>
            <strong>Timestamp:</strong> ${data.timestamp}
        `;
        downloadLink.href = `/legal/${data.evidence_id}`;
        resultDiv.style.display = 'block';
        
        // Update stats (simple refresh)
        location.reload();
    }

    // Vault search
    const searchForm = document.getElementById('searchForm');
    if (searchForm) {
        searchForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            const query = document.getElementById('searchQuery').value;
            const severity = document.getElementById('severityFilter').value;
            const dateFrom = document.getElementById('dateFrom').value;
            const dateTo = document.getElementById('dateTo').value;
            
            const params = new URLSearchParams();
            if (query) params.append('q', query);
            if (severity) params.append('severity', severity);
            if (dateFrom) params.append('date_from', dateFrom);
            if (dateTo) params.append('date_to', dateTo);
            
            fetch(`/search?${params}`)
            .then(response => response.json())
            .then(data => {
                updateTable(data);
            })
            .catch(error => {
                console.error('Error:', error);
            });
        });
    }

    // Load chart data
    if (document.getElementById('severityChart')) {
        fetch('/chart_data')
        .then(response => response.json())
        .then(data => {
            const ctx = document.getElementById('severityChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.months,
                    datasets: [{
                        label: 'High Severity',
                        data: data.high,
                        borderColor: 'rgb(220, 53, 69)',
                        backgroundColor: 'rgba(220, 53, 69, 0.1)',
                        tension: 0.1
                    }, {
                        label: 'Medium Severity',
                        data: data.medium,
                        borderColor: 'rgb(255, 193, 7)',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        tension: 0.1
                    }, {
                        label: 'Low Severity',
                        data: data.low,
                        borderColor: 'rgb(25, 135, 84)',
                        backgroundColor: 'rgba(25, 135, 84, 0.1)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        title: {
                            display: true,
                            text: 'Monthly Incident Trends'
                        }
                    }
                }
            });
        });
    }

    function updateTable(records) {
        const tbody = document.getElementById('recordsTable');
        tbody.innerHTML = '';
        
        records.forEach(record => {
            const row = `
                <tr>
                    <td>${record.evidence_id}</td>
                    <td>${record.message.length > 50 ? record.message.substring(0, 50) + '...' : record.message}</td>
                    <td>${record.category}</td>
                    <td>
                        <span class="badge bg-${record.severity === 'High' ? 'danger' : record.severity === 'Medium' ? 'warning' : 'success'}">
                            ${record.severity}
                        </span>
                    </td>
                    <td>${record.timestamp}</td>
                    <td>${record.hash.substring(0, 16)}...</td>
                    <td>
                        <a href="/legal/${record.evidence_id}" class="btn btn-sm btn-outline-primary">
                            <i class="fas fa-download"></i> PDF
                        </a>
                        <a href="/anchor/${record.evidence_id}" class="btn btn-sm btn-outline-success">
                            <i class="fas fa-link"></i> Anchor
                        </a>
                    </td>
                </tr>
            `;
            tbody.innerHTML += row;
        });
    }
});

function clearFilters() {
    document.getElementById('searchQuery').value = '';
    document.getElementById('severityFilter').value = '';
    document.getElementById('dateFrom').value = '';
    document.getElementById('dateTo').value = '';
    location.reload();
}