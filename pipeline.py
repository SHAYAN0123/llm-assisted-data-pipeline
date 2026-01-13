import pandas as pd
import numpy as np
from datetime import datetime
from typing import Tuple, Dict, List
import re

# ============================================================================
# VALIDATION MODULE
# ============================================================================

class SchemaValidator:
    """Validates data against schema rules"""
    
    def __init__(self):
        self.error_codes = {
            'E101': 'Invalid transaction_id format',
            'E102': 'Duplicate transaction_id',
            'E103': 'transaction_id null or empty',
            'E201': 'Invalid amount format',
            'E202': 'Amount out of range',
            'E203': 'Amount is zero or negative',
            'E204': 'Amount null or empty',
            'E205': 'Excessive decimal precision',
            'E301': 'Invalid timestamp format',
            'E302': 'Invalid date/time components',
            'E303': 'Future timestamp',
            'E304': 'Timestamp before epoch',
            'E305': 'Timestamp null or empty',
            'E401': 'Invalid country code format',
            'E402': 'Country code not recognized',
            'E404': 'Country field null or empty'
        }
        
        self.valid_countries = {
            'US', 'GB', 'DE', 'FR', 'JP', 'CN', 'IN', 'CA', 'AU', 'BR',
            'MX', 'ES', 'IT', 'NL', 'SE', 'CH', 'KR', 'SG', 'HK', 'NZ'
        }
    
    def validate_schema_columns(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Check if required columns exist"""
        required_columns = ['transaction_id', 'amount', 'timestamp', 'country']
        missing = set(required_columns) - set(df.columns)
        
        if missing:
            return False, f"Missing required columns: {missing}"
        return True, "Schema columns valid"
    
    def validate_rows(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """Validate each row and return valid/invalid dataframes"""
        
        valid_rows = []
        invalid_rows = []
        
        for idx, row in df.iterrows():
            errors = []
            
            # Validate transaction_id
            if pd.isna(row['transaction_id']) or str(row['transaction_id']).strip() == '':
                errors.append('E103')
            elif not self._validate_transaction_id(row['transaction_id']):
                errors.append('E101')
            
            # Validate amount
            if pd.isna(row['amount']):
                errors.append('E204')
            else:
                amount_error = self._validate_amount(row['amount'])
                if amount_error:
                    errors.extend(amount_error)
            
            # Validate timestamp
            if pd.isna(row['timestamp']):
                errors.append('E305')
            else:
                ts_error = self._validate_timestamp(row['timestamp'])
                if ts_error:
                    errors.extend(ts_error)
            
            # Validate country
            if pd.isna(row['country']) or str(row['country']).strip() == '':
                errors.append('E404')
            elif not self._validate_country(row['country']):
                errors.append('E401')
            
            # Sort rows
            if errors:
                invalid_rows.append({**row.to_dict(), 'rejection_reason': '; '.join(errors)})
            else:
                valid_rows.append(row.to_dict())
        
        valid_df = pd.DataFrame(valid_rows) if valid_rows else pd.DataFrame()
        invalid_df = pd.DataFrame(invalid_rows) if invalid_rows else pd.DataFrame()
        
        return valid_df, invalid_df
    
    def _validate_transaction_id(self, txn_id) -> bool:
        """Check transaction_id format: 8-32 chars, alphanumeric + hyphen/underscore"""
        pattern = r'^[A-Z0-9_-]{8,32}$'
        return bool(re.match(pattern, str(txn_id)))
    
    def _validate_amount(self, amount) -> List[str]:
        """Validate amount field"""
        errors = []
        
        try:
            # Try to parse as float
            amount_float = float(amount)
            
            # Check if negative or zero
            if amount_float <= 0:
                errors.append('E203')
            
            # Check range
            if amount_float < 0.01 or amount_float > 999999999.99:
                errors.append('E202')
            
            # Check decimal precision (max 2 places)
            amount_str = str(amount).strip()
            if '.' in amount_str:
                decimals = len(amount_str.split('.')[1])
                if decimals > 2:
                    errors.append('E205')
        
        except (ValueError, TypeError):
            errors.append('E201')
        
        return errors
    
    def _validate_timestamp(self, timestamp) -> List[str]:
        """Validate timestamp in ISO 8601 format"""
        errors = []
        
        try:
            # Try parsing multiple ISO 8601 formats
            ts_str = str(timestamp).strip()
            dt = None
            
            # Try formats: YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, YYYY-MM-DDTHH:MM:SSZ
            formats = [
                '%Y-%m-%d',
                '%Y-%m-%dT%H:%M:%S',
                '%Y-%m-%dT%H:%M:%SZ'
            ]
            
            for fmt in formats:
                try:
                    dt = pd.to_datetime(ts_str, format=fmt)
                    break
                except:
                    continue
            
            if dt is None:
                dt = pd.to_datetime(ts_str)
            
            # Check if date is before epoch
            epoch = pd.Timestamp('1970-01-01')
            if dt < epoch:
                errors.append('E304')
            
            # Check if date is in future (beyond 2030)
            max_date = pd.Timestamp('2030-12-31')
            if dt > max_date:
                errors.append('E303')
        
        except Exception:
            errors.append('E301')
        
        return errors
    
    def _validate_country(self, country) -> bool:
        """Check if country is valid ISO 3166-1 alpha-2 code"""
        country_str = str(country).strip()
        pattern = r'^[A-Z]{2}$'
        
        if not re.match(pattern, country_str):
            return False
        
        return country_str in self.valid_countries


# ============================================================================
# DATA CLEANING MODULE
# ============================================================================

class DataCleaner:
    """Cleans and transforms valid rows"""
    
    @staticmethod
    def clean_data(df: pd.DataFrame) -> pd.DataFrame:
        """Apply cleaning transformations to valid rows"""
        
        if df.empty:
            return df
        
        df = df.copy()
        
        # Clean transaction_id: trim whitespace
        df['transaction_id'] = df['transaction_id'].astype(str).str.strip()
        
        # Clean amount: parse to float, round to 2 decimals
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        df['amount'] = df['amount'].round(2)
        
        # Clean timestamp: standardize to ISO format
        df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
        df['timestamp'] = df['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')
        
        # Clean country: trim and uppercase
        df['country'] = df['country'].astype(str).str.strip().str.upper()
        
        return df


# ============================================================================
# STATISTICS MODULE
# ============================================================================

class StatisticsCalculator:
    """Computes summary statistics"""
    
    @staticmethod
    def calculate_stats(
        df_valid: pd.DataFrame,
        df_invalid: pd.DataFrame,
        error_counts: Dict[str, int],
        processing_time: float
    ) -> Dict:
        """Calculate comprehensive statistics"""
        
        total_rows = len(df_valid) + len(df_invalid)
        valid_count = len(df_valid)
        invalid_count = len(df_invalid)
        quality_score = (valid_count / total_rows * 100) if total_rows > 0 else 0
        
        stats = {
            'execution_metadata': {
                'execution_timestamp': datetime.now().isoformat(),
                'processing_duration_seconds': round(processing_time, 2)
            },
            'ingestion_summary': {
                'total_rows_read': total_rows,
                'valid_rows': valid_count,
                'invalid_rows': invalid_count,
                'data_quality_score_percent': round(quality_score, 2)
            },
            'error_breakdown': error_counts,
            'column_statistics': {}
        }
        
        # Calculate per-column statistics for valid rows
        if not df_valid.empty:
            stats['column_statistics'] = {
                'transaction_id': StatisticsCalculator._stats_string(df_valid['transaction_id']),
                'amount': StatisticsCalculator._stats_numeric(df_valid['amount']),
                'timestamp': StatisticsCalculator._stats_datetime(df_valid['timestamp']),
                'country': StatisticsCalculator._stats_string(df_valid['country'])
            }
        
        return stats
    
    @staticmethod
    def _stats_numeric(series: pd.Series) -> Dict:
        """Calculate statistics for numeric columns"""
        return {
            'type': 'float',
            'count': int(series.count()),
            'nulls': int(series.isna().sum()),
            'min': float(series.min()) if series.notna().any() else None,
            'max': float(series.max()) if series.notna().any() else None,
            'mean': float(series.mean()) if series.notna().any() else None,
            'median': float(series.median()) if series.notna().any() else None,
            'std_dev': float(series.std()) if series.notna().any() else None,
            'sum': float(series.sum()) if series.notna().any() else None
        }
    
    @staticmethod
    def _stats_string(series: pd.Series) -> Dict:
        """Calculate statistics for string columns"""
        return {
            'type': 'string',
            'count': int(series.count()),
            'nulls': int(series.isna().sum()),
            'unique_count': int(series.nunique()),
            'most_common': series.value_counts().head(5).to_dict(),
            'avg_length': float(series.astype(str).str.len().mean())
        }
    
    @staticmethod
    def _stats_datetime(series: pd.Series) -> Dict:
        """Calculate statistics for datetime columns"""
        dt_series = pd.to_datetime(series, errors='coerce')
        return {
            'type': 'datetime',
            'count': int(dt_series.count()),
            'nulls': int(dt_series.isna().sum()),
            'earliest': str(dt_series.min()) if dt_series.notna().any() else None,
            'latest': str(dt_series.max()) if dt_series.notna().any() else None,
            'date_range_days': int((dt_series.max() - dt_series.min()).days) if dt_series.notna().any() else None
        }


# ============================================================================
# MAIN PIPELINE
# ============================================================================

def run_pipeline(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, Dict]:
    """
    Execute complete data pipeline
    
    Args:
        df: Raw pandas DataFrame loaded from CSV
    
    Returns:
        Tuple of:
        - valid_df: Cleaned valid rows
        - invalid_df: Invalid rows with rejection reasons
        - stats: Summary statistics
    """
    
    start_time = datetime.now()
    
    print("[PIPELINE] Starting data pipeline execution...")
    
    # ===== VALIDATION PHASE =====
    print("[VALIDATION] Validating schema and rows...")
    validator = SchemaValidator()
    
    # Check schema columns
    schema_valid, schema_msg = validator.validate_schema_columns(df)
    if not schema_valid:
        raise ValueError(f"Schema validation failed: {schema_msg}")
    
    # Validate rows
    valid_df, invalid_df = validator.validate_rows(df)
    print(f"[VALIDATION] Results: {len(valid_df)} valid, {len(invalid_df)} invalid")
    
    # ===== CLEANING PHASE =====
    print("[CLEANING] Cleaning valid rows...")
    valid_df = DataCleaner.clean_data(valid_df)
    print(f"[CLEANING] Cleaned {len(valid_df)} rows")
    
    # ===== STATISTICS PHASE =====
    print("[STATISTICS] Calculating summary statistics...")
    
    # Extract error codes from rejection_reason
    error_counts = {}
    if not invalid_df.empty and 'rejection_reason' in invalid_df.columns:
        for reason in invalid_df['rejection_reason']:
            codes = re.findall(r'E\d{3}', str(reason))
            for code in codes:
                error_counts[code] = error_counts.get(code, 0) + 1
    
    processing_time = (datetime.now() - start_time).total_seconds()
    
    stats = StatisticsCalculator.calculate_stats(
        valid_df,
        invalid_df,
        error_counts,
        processing_time
    )
    
    print("[STATISTICS] Statistics calculated")
    print(f"[PIPELINE] Pipeline completed in {processing_time:.2f} seconds")
    
    return valid_df, invalid_df, stats


# ============================================================================
# EXAMPLE USAGE
# ============================================================================

if __name__ == "__main__":
    # Example: Create sample data
    sample_data = {
        'transaction_id': [
            'TXN_001_ABC',
            'TXN_002_DEF',
            'TXN_003',  # Invalid: too short
            'TXN_004_GHI'
        ],
        'amount': [
            '100.50',
            '250.75',
            '-50.00',  # Invalid: negative
            '999.99'
        ],
        'timestamp': [
            '2025-01-13T14:30:00Z',
            '2025-01-12T10:15:00',
            '2050-01-01T00:00:00',  # Invalid: future date
            '2025-01-10T08:45:30'
        ],
        'country': [
            'US',
            'GB',
            'XX',  # Invalid: not recognized
            'JP'
        ]
    }
    
    df = pd.DataFrame(sample_data)
    print("\n=== INPUT DATA ===")
    print(df)
    
    # Run pipeline
    print("\n=== PIPELINE EXECUTION ===")
    valid_df, invalid_df, stats = run_pipeline(df)
    
    # Display results
    print("\n=== VALID DATA (Cleaned) ===")
    print(valid_df)
    
    print("\n=== INVALID DATA ===")
    print(invalid_df[['transaction_id', 'amount', 'timestamp', 'country', 'rejection_reason']])
    
    print("\n=== STATISTICS ===")
    import json
    print(json.dumps(stats, indent=2))