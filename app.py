from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import pandas as pd
import os

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
        
        # Remove duplicates
        cleaned_df = df.drop_duplicates()
        
        # Build response
        schema = {col: {'type': str(df[col].dtype), 'nullable': bool(df[col].isna().any())} for col in df.columns}
        stats = {
            'row_count': len(cleaned_df),
            'column_count': len(cleaned_df.columns),
            'missing_values': int(df.isna().sum().sum()),
            'duplicate_rows': len(df) - len(cleaned_df),
            'memory_usage': str(df.memory_usage(deep=True).sum() / 1024)[:5] + ' KB'
        }
        
        return jsonify({
            'validation': {'is_valid': True, 'errors': []},
            'schema': schema,
            'statistics': stats,
            'cleaned_data': cleaned_df.head(10).astype(str).to_dict('records')
        }), 200
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'API running', 'version': '1.0.0'}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(debug=True, host='0.0.0.0', port=port)
