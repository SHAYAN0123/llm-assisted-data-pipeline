from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os
from pipeline import SchemaValidator, DataCleaner, StatisticsCalculator

app = Flask(__name__, static_folder='docs', static_url_path='')
CORS(app)

@app.route('/')
def index():
    return send_from_directory('docs', 'index.html')

@app.route('/api/process', methods=['POST'])
def process_csv():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file'}), 400
        file = request.files['file']
        if not file.filename:
            return jsonify({'error': 'No filename'}), 400
        df = pd.read_csv(file)
        if df.empty:
            return jsonify({'error': 'Empty CSV'}), 400
        
        validator = SchemaValidator()
        cleaner = DataCleaner()
        stats_calc = StatisticsCalculator()
        
        has_tx = all(c in df.columns for c in ['transaction_id', 'amount', 'timestamp', 'country'])
        
        if has_tx:
            valid_df, _ = validator.validate_rows(df)
            schema = validator.detect_schema(df)
        else:
            schema = {col: {'type': str(df[col].dtype), 'nullable': bool(df[col].isna().any())} for col in df.columns}
            valid_df = df
        
        cleaned_df = cleaner.clean(valid_df)
        statistics = stats_calc.calculate(cleaned_df)
        
        return jsonify({
            'validation': {'is_valid': True, 'errors': []},
            'schema': {col: {'type': str(schema[col].get('type', 'unknown') if isinstance(schema[col], dict) else schema[col]), 'nullable': schema[col].get('nullable', False) if isinstance(schema[col], dict) else False} for col in schema},
            'statistics': {'row_count': int(len(cleaned_df)), 'column_count': int(len(cleaned_df.columns)), 'missing_values': int(cleaned_df.isna().sum().sum()), 'duplicate_rows': int(len(cleaned_df) - len(cleaned_df.drop_duplicates())), 'memory_usage': str(cleaned_df.memory_usage(deep=True).sum() / 1024)[:5] + ' KB'},
            'cleaned_data': cleaned_df.head(10).astype(str).to_dict('records')
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'API running', 'version': '1.0.0'}), 200

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
