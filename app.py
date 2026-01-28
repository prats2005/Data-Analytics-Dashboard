"""
Resin Value Chart Generator - Enhanced for Location & Grade Selection
======================================================================
This script creates a web server that accepts Excel file uploads and generates 
interactive charts based on Location and Grade selection.

Installation:
    pip install flask pandas openpyxl --break-system-packages

Usage:
    python resin_chart_app.py
    
Then open: http://localhost:5000
"""

from flask import Flask, render_template_string, request, jsonify
import pandas as pd
import json
import io
import os

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# HTML Template with Upload Form and Chart Display
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resin Price Tracker</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 36px;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        
        .header p {
            font-size: 16px;
            opacity: 0.9;
        }
        
        .upload-section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 8px;
            padding: 40px;
            text-align: center;
            background: #f8f9ff;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        
        .upload-area:hover {
            border-color: #764ba2;
            background: #f0f2ff;
        }
        
        .upload-area.dragover {
            border-color: #764ba2;
            background: #e8eaff;
            transform: scale(1.02);
        }
        
        .upload-icon {
            font-size: 48px;
            margin-bottom: 15px;
        }
        
        .upload-text {
            color: #667eea;
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        
        .upload-hint {
            color: #666;
            font-size: 14px;
        }
        
        input[type="file"] {
            display: none;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 30px;
            border-radius: 6px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-top: 15px;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }
        
        .filter-section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            display: none;
        }
        
        .filter-section.active {
            display: block;
        }
        
        .filter-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .filter-group {
            background: #f8f9ff;
            padding: 20px;
            border-radius: 8px;
            border: 2px solid #e0e0e0;
            transition: border-color 0.3s ease;
        }
        
        .filter-group:hover {
            border-color: #667eea;
        }
        
        .filter-group label {
            display: block;
            margin-bottom: 10px;
            font-weight: 600;
            color: #333;
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .filter-group select {
            width: 100%;
            padding: 12px;
            border: 2px solid #667eea;
            border-radius: 6px;
            font-size: 15px;
            background: white;
            cursor: pointer;
            transition: all 0.3s ease;
        }
        
        .filter-group select:focus {
            outline: none;
            border-color: #764ba2;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }
        
        .filter-group select option {
            padding: 10px;
        }
        
        .chart-section {
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            display: none;
        }
        
        .chart-section.active {
            display: block;
        }
        
        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        
        .chart-title {
            color: #333;
            font-size: 24px;
            font-weight: bold;
        }
        
        .chart-subtitle {
            color: #666;
            font-size: 16px;
            margin-top: 5px;
        }
        
        #chart {
            width: 100%;
            height: 500px;
            margin-bottom: 20px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: #f8f9ff;
            padding: 20px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        
        .stat-label {
            color: #666;
            font-size: 13px;
            margin-bottom: 8px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stat-value {
            color: #667eea;
            font-size: 28px;
            font-weight: bold;
        }
        
        .stat-unit {
            font-size: 14px;
            color: #999;
            margin-left: 5px;
        }
        
        .instructions {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 15px;
            margin-top: 20px;
        }
        
        .instructions h3 {
            color: #856404;
            margin-bottom: 10px;
        }
        
        .instructions ul {
            margin-left: 20px;
            color: #856404;
        }
        
        .instructions li {
            margin-bottom: 5px;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            display: none;
        }
        
        .loading.active {
            display: block;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 15px;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            display: none;
            border-left: 4px solid #f5c6cb;
        }
        
        .error.active {
            display: block;
        }
        
        .success {
            background: #d4edda;
            color: #155724;
            padding: 15px;
            border-radius: 8px;
            margin-top: 15px;
            display: none;
            border-left: 4px solid #c3e6cb;
        }
        
        .success.active {
            display: block;
        }
        
        .file-info {
            background: #e8eaff;
            padding: 15px;
            border-radius: 6px;
            margin-top: 15px;
            display: none;
            border-left: 4px solid #667eea;
        }
        
        .file-info.active {
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        
        .file-details {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .file-icon {
            font-size: 24px;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 28px;
            }
            
            .filter-grid {
                grid-template-columns: 1fr;
            }
            
            .stats-grid {
                grid-template-columns: repeat(2, 1fr);
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Resin Price Tracker</h1>
            <p>Track resin prices by location and grade with interactive charts</p>
        </div>
        
        <div class="upload-section">
            <div class="upload-area" id="uploadArea">
                <div class="upload-icon">📁</div>
                <div class="upload-text">Click to upload or drag and drop</div>
                <div class="upload-hint">Excel files (.xlsx, .xls) - Your data should have Country, Location, Grade columns</div>
                <input type="file" id="fileInput" accept=".xlsx,.xls">
            </div>
            
            <div class="file-info" id="fileInfo"></div>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <div>Processing your file...</div>
            </div>
            
            <div class="error" id="error"></div>
            <div class="success" id="success"></div>
            
            <div class="instructions">
                <h3>📋 Instructions:</h3>
                <ul>
                    <li>Upload an Excel file with Country, Location, and Grade columns</li>
                    <li>Date columns should follow the format (e.g., 1/1/2022, 2/1/2022, etc.)</li>
                    <li>Value columns should contain numeric price data</li>
                    <li>After upload, select Location and Grade to view the price trend</li>
                </ul>
            </div>
        </div>
        
        <div class="filter-section" id="filterSection">
            <h2 style="color: #333; margin-bottom: 20px;">Select Location & Grade</h2>
            <div class="filter-grid">
                <div class="filter-group">
                    <label for="locationSelect">📍 Location</label>
                    <select id="locationSelect">
                        <option value="">-- Select Location --</option>
                    </select>
                </div>
                
                <div class="filter-group">
                    <label for="gradeSelect">🏷️ Grade</label>
                    <select id="gradeSelect">
                        <option value="">-- Select Grade --</option>
                    </select>
                </div>
            </div>
            
            <button class="btn" onclick="generateChart()">📈 Generate Chart</button>
        </div>
        
        <div class="chart-section" id="chartSection">
            <div class="chart-header">
                <div>
                    <div class="chart-title" id="chartTitle">Price Trend</div>
                    <div class="chart-subtitle" id="chartSubtitle"></div>
                </div>
            </div>
            <div id="chart"></div>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">Latest Price</div>
                    <div class="stat-value" id="latest">-<span class="stat-unit">Rs/Kg</span></div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Peak Price</div>
                    <div class="stat-value" id="peak">-<span class="stat-unit">Rs/Kg</span></div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Lowest Price</div>
                    <div class="stat-value" id="lowest">-<span class="stat-unit">Rs/Kg</span></div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Average Price</div>
                    <div class="stat-value" id="average">-<span class="stat-unit">Rs/Kg</span></div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Price Change</div>
                    <div class="stat-value" id="change">-<span class="stat-unit">%</span></div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">Data Points</div>
                    <div class="stat-value" id="dataPoints">-</div>
                </div>
            </div>
            
            <button class="btn" onclick="location.reload()" style="margin-top: 20px;">
                🔄 Upload Another File
            </button>
        </div>
    </div>

    <script>
        let uploadedFile = null;
        let availableData = null;
        
        const uploadArea = document.getElementById('uploadArea');
        const fileInput = document.getElementById('fileInput');
        const loading = document.getElementById('loading');
        const error = document.getElementById('error');
        const success = document.getElementById('success');
        const fileInfo = document.getElementById('fileInfo');
        const filterSection = document.getElementById('filterSection');
        const chartSection = document.getElementById('chartSection');
        const locationSelect = document.getElementById('locationSelect');
        const gradeSelect = document.getElementById('gradeSelect');
        
        // Click to upload
        uploadArea.addEventListener('click', () => fileInput.click());
        
        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleFile(files[0]);
            }
        });
        
        fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleFile(e.target.files[0]);
            }
        });
        
        function handleFile(file) {
            uploadedFile = file;
            hideMessages();
            chartSection.classList.remove('active');
            
            // Show file info
            fileInfo.innerHTML = `
                <div class="file-details">
                    <span class="file-icon">📄</span>
                    <div>
                        <strong>${file.name}</strong><br>
                        <small>${(file.size / 1024).toFixed(2)} KB</small>
                    </div>
                </div>
            `;
            fileInfo.classList.add('active');
            
            // Upload and get available options
            loading.classList.add('active');
            
            const formData = new FormData();
            formData.append('file', file);
            
            fetch('/upload', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                loading.classList.remove('active');
                
                if (data.error) {
                    showError(data.error);
                    return;
                }
                
                availableData = data;
                populateFilters(data.locations, data.grades);
                filterSection.classList.add('active');
                filterSection.scrollIntoView({ behavior: 'smooth' });
                success.textContent = `File uploaded successfully! Found ${data.locations.length} locations and ${data.grades.length} grades.`;
                success.classList.add('active');
            })
            .catch(err => {
                loading.classList.remove('active');
                showError('Failed to upload file: ' + err.message);
            });
        }
        
        function populateFilters(locations, grades) {
            locationSelect.innerHTML = '<option value="">-- Select Location --</option>';
            gradeSelect.innerHTML = '<option value="">-- Select Grade --</option>';
            
            locations.forEach(location => {
                const option = new Option(location, location);
                locationSelect.add(option);
            });
            
            grades.forEach(grade => {
                const option = new Option(grade, grade);
                gradeSelect.add(option);
            });
        }
        
        function generateChart() {
            const location = locationSelect.value;
            const grade = gradeSelect.value;
            
            if (!location || !grade) {
                showError('Please select both Location and Grade');
                return;
            }
            
            if (!uploadedFile) {
                showError('Please upload a file first');
                return;
            }
            
            hideMessages();
            loading.classList.add('active');
            
            const formData = new FormData();
            formData.append('file', uploadedFile);
            formData.append('location', location);
            formData.append('grade', grade);
            
            fetch('/generate', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                loading.classList.remove('active');
                
                if (data.error) {
                    showError(data.error);
                    return;
                }
                
                displayChart(data, location, grade);
                chartSection.classList.add('active');
                chartSection.scrollIntoView({ behavior: 'smooth' });
            })
            .catch(err => {
                loading.classList.remove('active');
                showError('Failed to generate chart: ' + err.message);
            });
        }
        
        function displayChart(data, location, grade) {
            // Update chart title
            document.getElementById('chartTitle').textContent = `${location} - ${grade}`;
            document.getElementById('chartSubtitle').textContent = `Price trend from ${data.dates[0]} to ${data.dates[data.dates.length - 1]}`;
            
            const trace = {
                x: data.dates,
                y: data.values,
                type: 'scatter',
                mode: 'lines+markers',
                line: {
                    color: '#667eea',
                    width: 3,
                    shape: 'spline'
                },
                marker: {
                    size: 8,
                    color: '#667eea',
                    line: {
                        color: '#764ba2',
                        width: 2
                    }
                },
                hovertemplate: '<b>%{x}</b><br>Price: ₹%{y:,.0f}/Kg<extra></extra>',
                fill: 'tozeroy',
                fillcolor: 'rgba(102, 126, 234, 0.1)'
            };
            
            const minVal = Math.min(...data.values);
            const maxVal = Math.max(...data.values);
            const padding = (maxVal - minVal) * 0.1;
            
            const layout = {
                xaxis: {
                    title: 'Date',
                    showgrid: true,
                    gridcolor: '#f0f0f0',
                    tickangle: -45
                },
                yaxis: {
                    title: 'Price (Rs/Kg)',
                    showgrid: true,
                    gridcolor: '#f0f0f0',
                    range: [Math.max(0, minVal - padding), maxVal + padding],
                    tickformat: ',.0f'
                },
                plot_bgcolor: 'white',
                paper_bgcolor: 'white',
                hovermode: 'closest',
                margin: {
                    l: 80,
                    r: 30,
                    t: 30,
                    b: 100
                }
            };
            
            const config = {
                responsive: true,
                displayModeBar: true,
                displaylogo: false,
                modeBarButtonsToRemove: ['lasso2d', 'select2d']
            };
            
            Plotly.newPlot('chart', [trace], layout, config);
            
            // Update statistics
            const values = data.values;
            const latest = values[values.length - 1];
            const first = values[0];
            const peak = Math.max(...values);
            const lowest = Math.min(...values);
            const avg = values.reduce((a, b) => a + b, 0) / values.length;
            const change = ((latest - first) / first * 100);
            
            document.getElementById('latest').innerHTML = `₹${latest.toLocaleString()}<span class="stat-unit">Rs/Kg</span>`;
            document.getElementById('peak').innerHTML = `₹${peak.toLocaleString()}<span class="stat-unit">Rs/Kg</span>`;
            document.getElementById('lowest').innerHTML = `₹${lowest.toLocaleString()}<span class="stat-unit">Rs/Kg</span>`;
            document.getElementById('average').innerHTML = `₹${avg.toLocaleString('en-IN', {maximumFractionDigits: 0})}<span class="stat-unit">Rs/Kg</span>`;
            document.getElementById('dataPoints').textContent = values.length;
            
            const changeEl = document.getElementById('change');
            const changeText = Math.abs(change).toFixed(2);
            changeEl.innerHTML = `${change >= 0 ? '+' : '-'}${changeText}<span class="stat-unit">%</span>`;
            changeEl.style.color = change >= 0 ? '#27ae60' : '#e74c3c';
        }
        
        function showError(message) {
            error.textContent = '❌ ' + message;
            error.classList.add('active');
        }
        
        function hideMessages() {
            error.classList.remove('active');
            success.classList.remove('active');
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        # Read the file
        file_bytes = file.read()
        
        # Try to read as Excel
        try:
            df = pd.read_excel(io.BytesIO(file_bytes))
        except Exception as e:
            return jsonify({'error': f'Failed to read Excel file: {str(e)}'}), 400
        
        # Verify required columns exist
        required_cols = ['Country', 'Location', 'Grade']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return jsonify({'error': f'Missing required columns: {", ".join(missing_cols)}'}), 400
        
        # Get unique locations and grades
        locations = sorted(df['Location'].dropna().unique().tolist())
        grades = sorted(df['Grade'].dropna().unique().tolist())
        
        if not locations or not grades:
            return jsonify({'error': 'No valid locations or grades found in the file'}), 400
        
        return jsonify({
            'locations': locations,
            'grades': grades,
            'rows': len(df)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/generate', methods=['POST'])
def generate_chart():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        location = request.form.get('location')
        grade = request.form.get('grade')
        
        if not location or not grade:
            return jsonify({'error': 'Location and Grade are required'}), 400
        
        # Read the file
        file_bytes = file.read()
        
        try:
            df = pd.read_excel(io.BytesIO(file_bytes))
        except Exception as e:
            return jsonify({'error': f'Failed to read Excel file: {str(e)}'}), 400
        
        # Filter data for the selected location and grade
        filtered_df = df[(df['Location'] == location) & (df['Grade'] == grade)]
        
        if filtered_df.empty:
            return jsonify({'error': f'No data found for Location: {location}, Grade: {grade}'}), 400
        
        # Get the row (should be only one row after filtering)
        row = filtered_df.iloc[0]
        
        # Extract date columns (skip Country, Location, Grade, Unit columns and any other non-numeric columns)
        skip_cols = ['Country', 'Location', 'Grade', 'Unit']
        
        # Extract dates and values
        dates = []
        values = []
        
        for col in df.columns:
            if col in skip_cols:
                continue
            
            value = row[col]
            
            # Skip if value is 0, NaN, empty, or not numeric
            try:
                numeric_value = float(value)
                if numeric_value != 0 and pd.notna(numeric_value):
                    dates.append(str(col))
                    values.append(numeric_value)
            except (ValueError, TypeError):
                # Skip non-numeric columns
                continue
        
        if not dates or not values:
            return jsonify({'error': 'No valid price data found for this location and grade'}), 400
        
        return jsonify({
            'dates': dates,
            'values': values
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("=" * 70)
    print("🚀 Resin Price Tracker - Web Application")
    print("=" * 70)
    print("\n✅ Server starting...")
    print("\n📍 Open your browser and go to:")
    print("   http://localhost:5000")
    print("\n📱 To access from other devices on your network:")
    print("   http://YOUR_LOCAL_IP:5000")
    print("\n💡 Features:")
    print("   • Upload Excel files with resin price data")
    print("   • Filter by Location and Grade")
    print("   • Interactive price trend charts")
    print("   • Comprehensive price statistics")
    print("\n⚠️  Press CTRL+C to stop the server")
    print("=" * 70)
    print()
    
    app.run(host='0.0.0.0', port=5000, debug=True)