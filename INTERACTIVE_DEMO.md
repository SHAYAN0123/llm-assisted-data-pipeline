# 🚀 Modern Interactive Landing Page & Backend API

## Overview

This is a **crisp, modern landing page** that demonstrates a **production-grade data processing backend**. It proves this is more than "just a fancy web page" by implementing real backend functionality.

## Features

### 🎨 Frontend
- **Modern Dark Theme**: Sleek, professional design with gradient accents
- **Interactive Demo**: Live CSV processing with real-time results display
- **Drag & Drop**: Upload files by dragging or clicking
- **Sample Data**: One-click sample data loading for testing
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Real-time Feedback**: Status messages, loading states, error handling

### ⚙️ Backend API
- **Flask REST API**: Production-ready Python backend
- **CSV Processing**: Upload and process CSV files instantly
- **Schema Detection**: Automatically detects data types and nullability
- **Data Validation**: Checks data integrity with detailed error reporting
- **Data Cleaning**: Removes duplicates, handles missing values
- **Statistics**: Calculates data profiling and analytics
- **JSON Responses**: Structured API responses for integration

## How It Works

### 1. Upload CSV File
```
POST /api/process
Content-Type: multipart/form-data

file: <your_file.csv>
```

**Response:**
```json
{
  "validation": {
    "is_valid": true,
    "errors": []
  },
  "schema": {
    "name": {"type": "object", "nullable": false},
    "age": {"type": "int64", "nullable": false}
  },
  "statistics": {
    "row_count": 100,
    "column_count": 5,
    "missing_values": 2,
    "duplicate_rows": 0,
    "memory_usage": "0.005 MB"
  },
  "cleaned_data": [...]
}
```

### 2. What Happens Behind the Scenes

1. **File Validation**: Checks file format and size (max 16MB)
2. **Schema Detection**: Analyzes columns and data types
3. **Data Cleaning**: 
   - Removes duplicate rows
   - Handles missing values
   - Normalizes data types
4. **Statistics Calculation**:
   - Row and column counts
   - Missing value analysis
   - Duplicate detection
   - Memory profiling
5. **Response Generation**: Returns cleaned data + metadata

## Running the Demo

### Start the Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run Flask server
python3 app.py
```

The API will be available at:
- **Frontend**: `http://localhost:8000/`
- **API Health**: `http://localhost:8000/api/health`
- **API Process**: `POST http://localhost:8000/api/process`

### Test with Sample Data

1. Visit `http://localhost:8000/`
2. Click "Load Sample Data"
3. See real-time validation, cleaning, and analysis results

### Test with Your Own CSV

1. Prepare a CSV file
2. Click upload box or drag & drop
3. Watch as it processes in real-time
4. See schema, statistics, and cleaned data preview

## API Endpoints

### Health Check
```
GET /api/health
```
Check if API is running and responsive.

### Process CSV
```
POST /api/process
Content-Type: multipart/form-data

file: <your_file.csv>
```
Process CSV with full validation, cleaning, and analysis pipeline.

## Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | HTML5/CSS3 | Modern UI with dark theme |
| **Backend** | Python Flask | REST API server |
| **Data Processing** | pandas/numpy | CSV processing |
| **Validation** | Custom validators | Schema & data validation |
| **Communication** | async/fetch | Real-time frontend-backend calls |

## Code Quality

- ✅ **34 comprehensive unit tests** (100% passing)
- ✅ **Full validation pipeline** with detailed error reporting
- ✅ **Production-ready error handling** and CORS support
- ✅ **Type hints** throughout codebase
- ✅ **Extensive documentation** in docstrings

## Why This Proves Technical Depth

1. **Not Just HTML**: Backend processes real data with validation & cleaning
2. **Real API Integration**: Frontend calls backend via fetch() for live processing
3. **Error Handling**: Graceful error messages for invalid files
4. **Performance**: Efficient pandas-based processing
5. **Scalability**: Flask can handle multiple concurrent requests
6. **Testing**: Tested suite proves reliability

## Example Use Cases

### 1. Data Quality Audit
- Upload messy CSV with duplicates and missing values
- See schema, validation errors, and cleaning stats
- Download cleaned data

### 2. Data Type Detection
- Upload CSV with mixed data types
- See automatic type inference
- Validate schema accuracy

### 3. Data Profiling
- Process large datasets
- Get detailed statistics
- Identify data quality issues

## Deployment

To deploy to production:

### Option 1: Heroku
```bash
heroku create my-data-pipeline
git push heroku main
```

### Option 2: Railway
```bash
railway link
railway up
```

### Option 3: PythonAnywhere
1. Upload to GitHub
2. Set up web app on PythonAnywhere
3. Configure WSGI to use `app.py`

## Next Steps

- Deploy backend to production server (Heroku/Railway)
- Update API URL in `docs/index.html` for deployed backend
- Add database storage for processed data
- Implement user authentication
- Add data export options (CSV, JSON, Excel)
- Implement batch processing for large files

## Files

- `app.py` - Flask backend with API endpoints
- `docs/index.html` - Modern interactive landing page
- `pipeline.py` - Core data validation & processing logic
- `test_pipeline.py` - 34 comprehensive unit tests
- `requirements.txt` - Python dependencies

## Support

For issues or questions:
- Check the GitHub repository: https://github.com/SHAYAN0123/llm-assisted-data-pipeline
- Review test cases in `test_pipeline.py` for usage examples
- Check API logs in browser console or Flask logs

---

**Built to demonstrate real backend capability beyond static HTML** 🚀
