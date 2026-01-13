try:
    import pytest
except Exception:
    # Minimal local shim for environments/editors without pytest installed.
    import re
    import contextlib

    class _Approx:
        def __init__(self, value, rel=None):
            self.value = value
            # treat rel as absolute tolerance when provided
            self.rel = rel if rel is not None else 1e-9

        def __eq__(self, other):
            try:
                return abs(float(self.value) - float(other)) <= float(self.rel)
            except Exception:
                return False

    def _fixture(func=None, **kwargs):
        # Simple decorator passthrough for @pytest.fixture
        if func is None:
            def wrapper(f):
                return f
            return wrapper
        return func

    @contextlib.contextmanager
    def _raises(expected_exception, match=None):
        try:
            yield
        except Exception as exc:
            if not isinstance(exc, expected_exception):
                raise AssertionError(f"Expected {expected_exception}, got {type(exc)}") from exc
            if match is not None and not re.search(match, str(exc)):
                raise AssertionError(f"Exception message does not match pattern: {match}") from exc
            return
        raise AssertionError(f"DID NOT RAISE {expected_exception}")

    def _approx(value, rel=None):
        return _Approx(value, rel)

    def _main(argv=None):
        # Minimal stub for pytest.main used when pytest is unavailable.
        print("pytest not installed; test runner stub invoked with args:", argv or [])
        return 0

    class _PytestShim:
        fixture = _fixture
        raises = _raises
        approx = _approx
        main = _main

    pytest = _PytestShim()

import pandas as pd
import numpy as np
import json
from pipeline import SchemaValidator, DataCleaner, StatisticsCalculator, run_pipeline


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def validator():
    """Create a SchemaValidator instance for testing"""
    return SchemaValidator()


@pytest.fixture
def valid_sample_data():
    """Create valid sample data for testing"""
    return pd.DataFrame({
        'transaction_id': ['TXN_001_ABC', 'TXN_002_DEF', 'TXN_003_GHI'],
        'amount': ['100.50', '250.75', '999.99'],
        'timestamp': ['2025-01-13T14:30:00Z', '2025-01-12T10:15:00', '2025-01-10T08:45:30'],
        'country': ['US', 'GB', 'JP']
    })


@pytest.fixture
def invalid_schema_data():
    """Create data with missing required columns"""
    return pd.DataFrame({
        'transaction_id': ['TXN_001_ABC'],
        'amount': ['100.50']
        # Missing 'timestamp' and 'country'
    })


# ============================================================================
# SCHEMA VALIDATION TESTS
# ============================================================================

class TestSchemaValidation:
    """Test schema column validation"""
    
    def test_valid_schema_structure(self, validator, valid_sample_data):
        """
        VERIFY: Valid schema with all required columns passes validation
        
        Expected: Returns (True, "Schema columns valid")
        This ensures the validator correctly identifies a properly structured CSV
        """
        is_valid, message = validator.validate_schema_columns(valid_sample_data)
        
        assert is_valid is True
        assert "valid" in message.lower()
    
    def test_missing_single_column(self, validator):
        """
        VERIFY: Missing one required column fails validation
        
        Data: CSV missing 'timestamp' column
        Expected: Returns False with message listing missing column
        This catches incomplete data schemas before processing
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['100.50'],
            'country': ['US']
            # Missing 'timestamp'
        })
        
        is_valid, message = validator.validate_schema_columns(df)
        
        assert is_valid is False
        assert "Missing required columns" in message
        assert "timestamp" in message
    
    def test_missing_multiple_columns(self, validator):
        """
        VERIFY: Missing multiple required columns fails validation
        
        Data: CSV missing 'timestamp' and 'country'
        Expected: Returns False with all missing columns listed
        This ensures comprehensive error reporting
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['100.50']
        })
        
        is_valid, message = validator.validate_schema_columns(df)
        
        assert is_valid is False
        assert "timestamp" in message
        assert "country" in message
    
    def test_extra_columns_allowed(self, validator):
        """
        VERIFY: Extra columns beyond schema don't fail validation
        
        Data: CSV with required columns + extra 'notes' column
        Expected: Returns True (extra columns are ignored)
        This allows flexibility for additional data without errors
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['100.50'],
            'timestamp': ['2025-01-13T14:30:00Z'],
            'country': ['US'],
            'notes': ['Additional info']  # Extra column
        })
        
        is_valid, message = validator.validate_schema_columns(df)
        
        assert is_valid is True
    
    def test_empty_dataframe_fails(self, validator):
        """
        VERIFY: Empty DataFrame (no columns) fails validation
        
        Data: Empty DataFrame with no columns
        Expected: Returns False - missing all required columns
        This prevents processing of corrupted/empty files
        """
        df = pd.DataFrame()
        
        is_valid, message = validator.validate_schema_columns(df)
        
        assert is_valid is False
        assert "Missing required columns" in message


# ============================================================================
# MISSING VALUES TESTS
# ============================================================================

class TestMissingValues:
    """Test handling of null/empty values in required fields"""
    
    def test_null_transaction_id_rejected(self, validator):
        """
        VERIFY: Null transaction_id is rejected with error E103
        
        Data: Row with NULL/NaN in transaction_id
        Expected: Row marked as invalid with error code E103
        This ensures all transactions have identifiers
        """
        df = pd.DataFrame({
            'transaction_id': [None],
            'amount': ['100.50'],
            'timestamp': ['2025-01-13T14:30:00Z'],
            'country': ['US']
        })
        
        valid_df, invalid_df = validator.validate_rows(df)
        
        assert len(valid_df) == 0
        assert len(invalid_df) == 1
        assert 'E103' in invalid_df.iloc[0]['rejection_reason']
    
    def test_empty_string_transaction_id_rejected(self, validator):
        """
        VERIFY: Empty string transaction_id is rejected with error E103
        
        Data: Row with empty string in transaction_id field
        Expected: Row marked as invalid with E103
        This handles whitespace-only or blank entries
        """
        df = pd.DataFrame({
            'transaction_id': ['   '],  # Whitespace only
            'amount': ['100.50'],
            'timestamp': ['2025-01-13T14:30:00Z'],
            'country': ['US']
        })
        
        valid_df, invalid_df = validator.validate_rows(df)
        
        assert len(valid_df) == 0
        assert len(invalid_df) == 1
        assert 'E103' in invalid_df.iloc[0]['rejection_reason']
    
    def test_null_amount_rejected(self, validator):
        """
        VERIFY: Null amount is rejected with error E204
        
        Data: Row with NULL/NaN in amount field
        Expected: Row marked invalid with E204
        This ensures transaction amounts are always present
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': [None],
            'timestamp': ['2025-01-13T14:30:00Z'],
            'country': ['US']
        })
        
        valid_df, invalid_df = validator.validate_rows(df)
        
        assert len(valid_df) == 0
        assert len(invalid_df) == 1
        assert 'E204' in invalid_df.iloc[0]['rejection_reason']
    
    def test_null_timestamp_rejected(self, validator):
        """
        VERIFY: Null timestamp is rejected with error E305
        
        Data: Row with NULL/NaN in timestamp field
        Expected: Row marked invalid with E305
        This ensures transaction timestamps are required
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['100.50'],
            'timestamp': [None],
            'country': ['US']
        })
        
        valid_df, invalid_df = validator.validate_rows(df)
        
        assert len(valid_df) == 0
        assert len(invalid_df) == 1
        assert 'E305' in invalid_df.iloc[0]['rejection_reason']
    
    def test_null_country_rejected(self, validator):
        """
        VERIFY: Null country is rejected with error E404
        
        Data: Row with NULL/NaN in country field
        Expected: Row marked invalid with E404
        This ensures transaction origin country is always specified
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['100.50'],
            'timestamp': ['2025-01-13T14:30:00Z'],
            'country': [None]
        })
        
        valid_df, invalid_df = validator.validate_rows(df)
        
        assert len(valid_df) == 0
        assert len(invalid_df) == 1
        assert 'E404' in invalid_df.iloc[0]['rejection_reason']
    
    def test_multiple_null_values(self, validator):
        """
        VERIFY: Row with multiple null fields captures all errors
        
        Data: Row with NULLs in amount, timestamp, and country
        Expected: All three error codes (E204, E305, E404) present
        This ensures comprehensive error reporting for corrupt rows
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': [None],
            'timestamp': [None],
            'country': [None]
        })
        
        valid_df, invalid_df = validator.validate_rows(df)
        
        assert len(valid_df) == 0
        assert len(invalid_df) == 1
        
        rejection_reason = invalid_df.iloc[0]['rejection_reason']
        assert 'E204' in rejection_reason
        assert 'E305' in rejection_reason
        assert 'E404' in rejection_reason
    
    def test_mixed_valid_invalid_rows(self, validator):
        """
        VERIFY: Pipeline correctly separates valid and invalid rows
        
        Data: 3 rows - first valid, second with null amount, third with null timestamp
        Expected: 1 valid row, 2 invalid rows
        This ensures the validator doesn't reject entire batch on partial errors
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC', 'TXN_002_DEF', 'TXN_003_GHI'],
            'amount': ['100.50', None, '250.75'],
            'timestamp': ['2025-01-13T14:30:00Z', '2025-01-12T10:15:00', None],
            'country': ['US', 'GB', 'JP']
        })
        
        valid_df, invalid_df = validator.validate_rows(df)
        
        assert len(valid_df) == 1
        assert len(invalid_df) == 2
        assert valid_df.iloc[0]['transaction_id'] == 'TXN_001_ABC'


# ============================================================================
# NEGATIVE AMOUNT TESTS
# ============================================================================

class TestNegativeAmounts:
    """Test validation of negative and zero amounts"""
    
    def test_negative_amount_rejected(self, validator):
        """
        VERIFY: Negative amount is rejected with error E203
        
        Data: Row with amount = -50.00
        Expected: Row marked invalid with E203
        This prevents processing of negative/refund transactions as normal sales
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['-50.00'],
            'timestamp': ['2025-01-13T14:30:00Z'],
            'country': ['US']
        })
        
        valid_df, invalid_df = validator.validate_rows(df)
        
        assert len(valid_df) == 0
        assert len(invalid_df) == 1
        assert 'E203' in invalid_df.iloc[0]['rejection_reason']
    
    def test_zero_amount_rejected(self, validator):
        """
        VERIFY: Zero amount is rejected with error E203
        
        Data: Row with amount = 0.00 or "0"
        Expected: Row marked invalid with E203
        This ensures all transactions have positive value
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['0.00'],
            'timestamp': ['2025-01-13T14:30:00Z'],
            'country': ['US']
        })
        
        valid_df, invalid_df = validator.validate_rows(df)
        
        assert len(valid_df) == 0
        assert len(invalid_df) == 1
        assert 'E203' in invalid_df.iloc[0]['rejection_reason']
    
    def test_minimum_positive_amount_accepted(self, validator):
        """
        VERIFY: Minimum positive amount (0.01) is accepted
        
        Data: Row with amount = 0.01
        Expected: Row passes validation (valid_df)
        This confirms the lower boundary of acceptable amounts
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['0.01'],
            'timestamp': ['2025-01-13T14:30:00Z'],
            'country': ['US']
        })
        
        valid_df, invalid_df = validator.validate_rows(df)
        
        assert len(valid_df) == 1
        assert len(invalid_df) == 0
    
    def test_very_small_positive_amount_accepted(self, validator):
        """
        VERIFY: Small positive amounts like 0.10 are accepted
        
        Data: Row with amount = 0.10
        Expected: Row passes validation
        This confirms amounts just above minimum work correctly
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['0.10'],
            'timestamp': ['2025-01-13T14:30:00Z'],
            'country': ['US']
        })
        
        valid_df, invalid_df = validator.validate_rows(df)
        
        assert len(valid_df) == 1
        assert len(invalid_df) == 0
    
    def test_negative_amount_out_of_range(self, validator):
        """
        VERIFY: Negative amounts trigger both E203 and potentially E202
        
        Data: Row with amount = -100.00
        Expected: Row includes E203 (negative check)
        This ensures both negative and range checks are applied
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['-100.00'],
            'timestamp': ['2025-01-13T14:30:00Z'],
            'country': ['US']
        })
        
        valid_df, invalid_df = validator.validate_rows(df)
        
        assert len(valid_df) == 0
        assert len(invalid_df) == 1
        assert 'E203' in invalid_df.iloc[0]['rejection_reason']
    
    def test_large_positive_amount_accepted(self, validator):
        """
        VERIFY: Large positive amounts within range are accepted
        
        Data: Row with amount = 999999.99
        Expected: Row passes validation
        This confirms upper boundary handling
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['999999.99'],
            'timestamp': ['2025-01-13T14:30:00Z'],
            'country': ['US']
        })
        
        valid_df, invalid_df = validator.validate_rows(df)
        
        assert len(valid_df) == 1
        assert len(invalid_df) == 0
    
    def test_amount_exceeds_maximum_range(self, validator):
        """
        VERIFY: Amount exceeding max (999999999.99) is rejected with E202
        
        Data: Row with amount = 10000000000.00 (exceeds max)
        Expected: Row marked invalid with E202
        This prevents processing of unreasonably large amounts
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['10000000000.00'],
            'timestamp': ['2025-01-13T14:30:00Z'],
            'country': ['US']
        })
        
        valid_df, invalid_df = validator.validate_rows(df)
        
        assert len(valid_df) == 0
        assert len(invalid_df) == 1
        assert 'E202' in invalid_df.iloc[0]['rejection_reason']


# ============================================================================
# DATA CLEANING TESTS
# ============================================================================

class TestDataCleaning:
    """Test data transformation and cleaning operations"""
    
    def test_clean_trims_transaction_id_whitespace(self, valid_sample_data):
        """
        VERIFY: Cleaning module trims whitespace from transaction_id
        
        Data: transaction_id with leading/trailing spaces
        Expected: Whitespace removed in cleaned output
        This ensures consistent identifiers for matching
        """
        df = pd.DataFrame({
            'transaction_id': ['  TXN_001_ABC  '],
            'amount': [100.50],
            'timestamp': ['2025-01-13T14:30:00'],
            'country': ['US']
        })
        
        cleaned = DataCleaner.clean_data(df)
        
        assert cleaned.iloc[0]['transaction_id'] == 'TXN_001_ABC'
        assert cleaned.iloc[0]['transaction_id'] != '  TXN_001_ABC  '
    
    def test_clean_converts_amount_to_float(self):
        """
        VERIFY: Cleaning converts amount strings to float type
        
        Data: amount as string '100.50'
        Expected: Converted to float type 100.50
        This ensures proper type for calculations
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['100.50'],  # String
            'timestamp': ['2025-01-13T14:30:00'],
            'country': ['US']
        })
        
        cleaned = DataCleaner.clean_data(df)
        
        assert isinstance(cleaned.iloc[0]['amount'], (float, np.floating))
        assert cleaned.iloc[0]['amount'] == 100.50
    
    def test_clean_rounds_amount_to_two_decimals(self):
        """
        VERIFY: Cleaning rounds amounts to 2 decimal places
        
        Data: amount = '100.5' (1 decimal)
        Expected: Rounded to 100.50 (2 decimals)
        This ensures currency precision
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['100.5'],
            'timestamp': ['2025-01-13T14:30:00'],
            'country': ['US']
        })
        
        cleaned = DataCleaner.clean_data(df)
        
        assert cleaned.iloc[0]['amount'] == 100.50
    
    def test_clean_standardizes_timestamp_format(self):
        """
        VERIFY: Cleaning standardizes timestamp to ISO format
        
        Data: timestamp = '2025-01-13' (date only)
        Expected: Converted to '2025-01-13T00:00:00'
        This ensures consistent datetime formatting
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': [100.50],
            'timestamp': ['2025-01-13'],  # Date only
            'country': ['US']
        })
        
        cleaned = DataCleaner.clean_data(df)
        
        assert cleaned.iloc[0]['timestamp'] == '2025-01-13T00:00:00'
    
    def test_clean_trims_and_uppers_country(self):
        """
        VERIFY: Cleaning trims whitespace and ensures uppercase country code
        
        Data: country = ' us ' (lowercase with spaces)
        Expected: Converted to 'US'
        This ensures consistent country code format
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': [100.50],
            'timestamp': ['2025-01-13T14:30:00'],
            'country': [' us ']  # Lowercase with spaces
        })
        
        cleaned = DataCleaner.clean_data(df)
        
        assert cleaned.iloc[0]['country'] == 'US'
    
    def test_clean_empty_dataframe_returns_empty(self):
        """
        VERIFY: Cleaning empty DataFrame returns empty DataFrame
        
        Data: Empty DataFrame
        Expected: Returns empty DataFrame without errors
        This handles edge case of no valid rows
        """
        df = pd.DataFrame({
            'transaction_id': [],
            'amount': [],
            'timestamp': [],
            'country': []
        })
        
        cleaned = DataCleaner.clean_data(df)
        
        assert len(cleaned) == 0
        assert list(cleaned.columns) == ['transaction_id', 'amount', 'timestamp', 'country']


# ============================================================================
# STATISTICS TESTS
# ============================================================================

class TestStatisticsCalculation:
    """Test statistics calculation and reporting"""
    
    def test_stats_calculate_quality_score(self):
        """
        VERIFY: Statistics correctly calculates data quality score
        
        Data: 3 valid rows, 1 invalid row
        Expected: quality_score = 75.0% (3/4)
        This ensures accurate reporting of data quality metrics
        """
        valid_df = pd.DataFrame({
            'transaction_id': ['TXN_001', 'TXN_002', 'TXN_003'],
            'amount': [100.0, 200.0, 300.0],
            'timestamp': ['2025-01-13T14:30:00', '2025-01-12T10:15:00', '2025-01-11T08:45:30'],
            'country': ['US', 'GB', 'JP']
        })
        invalid_df = pd.DataFrame({'rejection_reason': ['E203']})
        
        stats = StatisticsCalculator.calculate_stats(valid_df, invalid_df, {}, 0.1)
        
        assert stats['ingestion_summary']['data_quality_score_percent'] == 75.0
    
    def test_stats_count_valid_and_invalid_rows(self):
        """
        VERIFY: Statistics correctly counts valid and invalid rows
        
        Data: 2 valid, 3 invalid rows
        Expected: valid_rows=2, invalid_rows=3, total=5
        This ensures accurate row counting
        """
        valid_df = pd.DataFrame({
            'transaction_id': ['TXN_001', 'TXN_002'],
            'amount': [100.0, 200.0],
            'timestamp': ['2025-01-13T14:30:00', '2025-01-12T10:15:00'],
            'country': ['US', 'GB']
        })
        invalid_df = pd.DataFrame({
            'rejection_reason': ['E203', 'E305', 'E401']
        })
        
        stats = StatisticsCalculator.calculate_stats(valid_df, invalid_df, {}, 0.1)
        
        assert stats['ingestion_summary']['valid_rows'] == 2
        assert stats['ingestion_summary']['invalid_rows'] == 3
        assert stats['ingestion_summary']['total_rows_read'] == 5
    
    def test_stats_numeric_column_calculations(self):
        """
        VERIFY: Statistics calculates correct numeric metrics for amount
        
        Data: Amounts = [100.0, 200.0, 300.0]
        Expected: min=100, max=300, mean=200, sum=600
        This ensures numeric statistics are accurate
        """
        valid_df = pd.DataFrame({
            'transaction_id': ['TXN_001', 'TXN_002', 'TXN_003'],
            'amount': [100.0, 200.0, 300.0],
            'timestamp': ['2025-01-13T14:30:00', '2025-01-12T10:15:00', '2025-01-11T08:45:30'],
            'country': ['US', 'GB', 'JP']
        })
        invalid_df = pd.DataFrame()
        
        stats = StatisticsCalculator.calculate_stats(valid_df, invalid_df, {}, 0.1)
        amount_stats = stats['column_statistics']['amount']
        
        assert amount_stats['min'] == 100.0
        assert amount_stats['max'] == 300.0
        assert amount_stats['mean'] == 200.0
        assert amount_stats['sum'] == 600.0
    
    def test_stats_error_breakdown(self):
        """
        VERIFY: Statistics correctly counts error codes
        
        Data: 2 rows with E203, 1 row with E305
        Expected: error_breakdown = {E203: 2, E305: 1}
        This ensures error frequency is tracked
        """
        valid_df = pd.DataFrame()
        invalid_df = pd.DataFrame({
            'rejection_reason': ['E203', 'E203; E305', 'E305']
        })
        error_counts = {'E203': 2, 'E305': 2}
        
        stats = StatisticsCalculator.calculate_stats(valid_df, invalid_df, error_counts, 0.1)
        
        assert stats['error_breakdown']['E203'] == 2
        assert stats['error_breakdown']['E305'] == 2


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestPipelineIntegration:
    """Test complete pipeline execution"""
    
    def test_end_to_end_pipeline_with_valid_data(self, valid_sample_data):
        """
        VERIFY: Complete pipeline processes valid data correctly
        
        Data: 3 rows - all valid
        Expected: 3 rows in valid_df, 0 in invalid_df, quality_score=100%
        This confirms the entire pipeline flow works end-to-end
        """
        valid_df, invalid_df, stats = run_pipeline(valid_sample_data)
        
        assert len(valid_df) == 3
        assert len(invalid_df) == 0
        assert stats['ingestion_summary']['data_quality_score_percent'] == 100.0
    
    def test_end_to_end_pipeline_mixed_data(self):
        """
        VERIFY: Pipeline correctly handles mix of valid and invalid rows
        
        Data: 3 rows - 1 valid, 1 with negative amount, 1 with future date
        Expected: 1 valid, 2 invalid, quality_score=33.33%
        This confirms mixed data is properly separated
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC', 'TXN_002_DEF', 'TXN_003_GHI'],
            'amount': ['100.50', '-50.00', '250.75'],
            'timestamp': ['2025-01-13T14:30:00Z', '2025-01-12T10:15:00', '2050-01-01T00:00:00'],
            'country': ['US', 'GB', 'JP']
        })
        
        valid_df, invalid_df, stats = run_pipeline(df)
        
        assert len(valid_df) == 1
        assert len(invalid_df) == 2
        assert pytest.approx(stats['ingestion_summary']['data_quality_score_percent'], 0.1) == 33.33
    
    def test_pipeline_rejects_invalid_schema(self):
        """
        VERIFY: Pipeline raises error on invalid schema
        
        Data: DataFrame missing 'timestamp' column
        Expected: ValueError raised
        This ensures pipeline fails early on structural issues
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['100.50'],
            'country': ['US']
            # Missing 'timestamp'
        })
        
        with pytest.raises(ValueError, match="Schema validation failed"):
            run_pipeline(df)
    
    def test_pipeline_cleans_valid_rows(self):
        """
        VERIFY: Pipeline cleans valid rows during processing
        
        Data: Valid row with proper formatting (validation passes)
        Expected: Cleaned row has trimmed strings and proper types
        This confirms cleaning is applied during pipeline execution
        Note: Validation happens BEFORE cleaning, so IDs must be valid format
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['100.5'],
            'timestamp': ['2025-01-13T14:30:00Z'],
            'country': ['US']
        })
        
        valid_df, invalid_df, stats = run_pipeline(df)
        
        assert len(valid_df) == 1
        assert valid_df.iloc[0]['transaction_id'] == 'TXN_001_ABC'
        assert valid_df.iloc[0]['amount'] == 100.50
        assert valid_df.iloc[0]['country'] == 'US'
    
    def test_pipeline_generates_statistics(self):
        """
        VERIFY: Pipeline generates complete statistics report
        
        Data: Any valid data
        Expected: Statistics dict contains all required sections
        This ensures reporting structure is correct
        """
        df = pd.DataFrame({
            'transaction_id': ['TXN_001_ABC'],
            'amount': ['100.50'],
            'timestamp': ['2025-01-13T14:30:00Z'],
            'country': ['US']
        })
        
        valid_df, invalid_df, stats = run_pipeline(df)
        
        assert 'execution_metadata' in stats
        assert 'ingestion_summary' in stats
        assert 'error_breakdown' in stats
        assert 'column_statistics' in stats
        assert stats['execution_metadata']['processing_duration_seconds'] >= 0


# ============================================================================
# RUN TESTS
# ============================================================================

if __name__ == "__main__":
    # Run with: pytest test_pipeline.py -v
    pytest.main([__file__, "-v", "--tb=short"])