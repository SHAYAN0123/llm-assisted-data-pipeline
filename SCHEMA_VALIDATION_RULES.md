# CSV Schema Validation Rules & Data Quality Analysis

**Schema Reviewed**: Transaction Pipeline  
**Date**: January 13, 2026  
**Version**: 1.0  

---

## 1. Schema Overview

| Column | Data Type | Current Status | Recommendation |
|--------|-----------|-----------------|-----------------|
| transaction_id | String | ⚠️ Needs clarification | Define format, length, uniqueness |
| amount | Float | ✓ Clear | Define range, precision |
| timestamp | ISO DateTime | ✓ Clear | Define timezone, range |
| country | String | ⚠️ Needs clarification | Define format (code vs name), validation |

---

## 2. Validation Rules by Column

### 2.1 transaction_id (String)

**Recommended Rules:**

```
Rule ID: V_TXN_001
Field: transaction_id
Type: String
Required: YES
Unique: YES (within file)
Format: Alphanumeric, optional hyphens/underscores
Pattern: ^[A-Z0-9_-]{8,32}$
Length: 8-32 characters
Examples: TXN123456789, TXN-2026-0001, TXN_ABC_12345

Validation Checks:
✓ Non-empty and non-null
✓ Matches alphanumeric pattern (uppercase letters, numbers, hyphen, underscore)
✓ Length between 8-32 characters
✓ No special characters except hyphen and underscore
✓ Unique within file (no duplicates)
✓ No leading/trailing whitespace

Error Code: E101 - Invalid transaction_id format
Error Code: E102 - Duplicate transaction_id
Error Code: E103 - transaction_id null or empty
```

**Constraint Definition:**
```yaml
transaction_id:
  type: string
  required: true
  unique: true
  min_length: 8
  max_length: 32
  pattern: '^[A-Z0-9_-]{8,32}$'
  allow_null: false
```

---

### 2.2 amount (Float)

**Recommended Rules:**

```
Rule ID: V_AMT_001
Field: amount
Type: Float (numeric, decimal)
Required: YES
Range: 0.01 - 999,999,999.99 (configurable)
Decimal Places: 2 (currency precision)
Format: Positive decimal numbers

Validation Checks:
✓ Non-empty and non-null
✓ Valid numeric value (parseable to float)
✓ Positive value (> 0)
✓ Within acceptable range
✓ Maximum 2 decimal places (when applicable)
✓ No currency symbols ($, €, £)
✓ No thousands separators (1000, not 1,000)

Error Code: E201 - Invalid amount format
Error Code: E202 - Amount out of range (negative or exceeds max)
Error Code: E203 - Amount is zero or negative
Error Code: E204 - Amount null or empty
Error Code: E205 - Excessive decimal precision (> 2 places)
```

**Constraint Definition:**
```yaml
amount:
  type: float
  required: true
  allow_null: false
  min_value: 0.01
  max_value: 999999999.99
  decimal_places: 2
  allow_negative: false
  allow_zero: false
```

**Edge Cases:**
```
Case: "100.5" → VALID (auto-pad to 100.50)
Case: "100.555" → REJECT (E205)
Case: "100" → VALID (auto-convert to 100.00)
Case: "$100.00" → REJECT (E201)
Case: "1,000.00" → REJECT (E201)
Case: "-50.00" → REJECT (E203)
Case: "0.00" → REJECT (E203)
Case: "" or NULL → REJECT (E204)
Case: "abc" → REJECT (E201)
Case: "999999999999.99" → REJECT (E202)
```

---

### 2.3 timestamp (ISO DateTime)

**Recommended Rules:**

```
Rule ID: V_TS_001
Field: timestamp
Type: DateTime (ISO 8601)
Required: YES
Timezone: UTC (assumed)
Format: YYYY-MM-DDTHH:MM:SS or YYYY-MM-DDTHH:MM:SSZ
Range: 1970-01-01 to 2030-12-31 (configurable)

Validation Checks:
✓ Non-empty and non-null
✓ Valid ISO 8601 datetime format
✓ Valid date components (month 1-12, day 1-31, etc.)
✓ Valid time components (hour 0-23, minute 0-59, second 0-59)
✓ Not a future date (beyond current date or cutoff)
✓ Not before epoch (e.g., before 1970-01-01)
✓ Matches one of: YYYY-MM-DD, YYYY-MM-DDTHH:MM:SS, YYYY-MM-DDTHH:MM:SSZ

Error Code: E301 - Invalid timestamp format
Error Code: E302 - Invalid date/time components
Error Code: E303 - Future timestamp (exceeds cutoff)
Error Code: E304 - Timestamp before epoch
Error Code: E305 - Timestamp null or empty
Error Code: E306 - Ambiguous or missing timezone
```

**Constraint Definition:**
```yaml
timestamp:
  type: datetime
  required: true
  allow_null: false
  format: 'ISO8601'
  allowed_formats:
    - 'YYYY-MM-DD'
    - 'YYYY-MM-DDTHH:MM:SS'
    - 'YYYY-MM-DDTHH:MM:SSZ'
  min_date: '1970-01-01T00:00:00Z'
  max_date: '2030-12-31T23:59:59Z'
  timezone: 'UTC'
```

**Edge Cases:**
```
Case: "2025-01-13T14:30:00Z" → VALID
Case: "2025-01-13T14:30:00" → VALID (assume UTC)
Case: "2025-01-13" → VALID (midnight assumed)
Case: "2025-01-13 14:30:00" → REJECT (E301, space not T)
Case: "13-01-2025T14:30:00" → REJECT (E301, wrong order)
Case: "2025-13-01T14:30:00" → REJECT (E302, month > 12)
Case: "2025-01-32T14:30:00" → REJECT (E302, day > 31)
Case: "2025-01-13T25:30:00" → REJECT (E302, hour > 23)
Case: "1969-12-31T23:59:59" → REJECT (E304, before epoch)
Case: "2035-01-01T00:00:00" → REJECT (E303, future cutoff)
Case: "" or NULL → REJECT (E305)
Case: "2025-01-13T14:30:00+05:00" → REJECT (E306, non-UTC timezone)
```

---

### 2.4 country (String)

**Recommended Rules:**

```
Rule ID: V_CTR_001
Field: country
Type: String
Required: YES / NO (CLARIFY)
Format: ISO 3166-1 alpha-2 code (2-letter country code)
Examples: US, GB, DE, JP, CN, IN, CA, AU
Pattern: ^[A-Z]{2}$

Alternative Format (if full names):
Pattern: ^[A-Za-z\s\-']{2,60}$
Examples: United States, United Kingdom, South Korea

Validation Checks (ISO Code Format):
✓ Exactly 2 uppercase letters
✓ Valid ISO 3166-1 alpha-2 country code
✓ No numbers, special characters, or spaces
✓ Matches against whitelist of 249 valid country codes

Validation Checks (Full Name Format):
✓ Non-empty (if required)
✓ 2-60 characters
✓ Letters, spaces, hyphens, apostrophes only
✓ Matches against validated country names list

Error Code: E401 - Invalid country code format
Error Code: E402 - Country code not recognized (not in ISO 3166-1)
Error Code: E403 - Country name invalid or not recognized
Error Code: E404 - Country field null or empty (if required)
```

**Constraint Definition (ISO Code):**
```yaml
country:
  type: string
  required: true
  allow_null: false
  format: 'ISO3166-1-alpha2'
  pattern: '^[A-Z]{2}$'
  length: 2
  valid_values: [list of 249 ISO country codes]
  case_sensitive: true
```

**Constraint Definition (Full Name):**
```yaml
country:
  type: string
  required: true
  allow_null: false
  min_length: 2
  max_length: 60
  pattern: '^[A-Za-z\s\-\']{2,60}$'
  valid_values: [list of 249 country names]
```

**Edge Cases:**
```
Case (ISO Code Format):
"US" → VALID
"GB" → VALID
"us" → REJECT (E401, lowercase)
"USA" → REJECT (E401, 3 letters)
"U.S." → REJECT (E401, contains periods)
"U S" → REJECT (E401, contains space)
"ZZ" → REJECT (E402, not valid ISO code)
"" or NULL → REJECT (E404, if required)

Case (Full Name Format):
"United States" → VALID
"South Korea" → VALID
"United Kingdom" → VALID
"St. Helena" → REJECT (E401, period)
"USA" → REJECT (E403, abbreviation)
"123" → REJECT (E401, numbers)
"United-States" → VALID (hyphen allowed)
"" or NULL → REJECT (E404, if required)
```

---

## 3. Data Quality Issues & Concerns

### 3.1 Identified Issues

| Issue | Severity | Impact | Recommendation |
|-------|----------|--------|-----------------|
| **Ambiguous transaction_id format** | 🔴 HIGH | Validation failures | Define exact format/pattern |
| **Amount precision inconsistency** | 🔴 HIGH | Rounding errors | Enforce 2 decimal places |
| **Timestamp timezone ambiguity** | 🔴 HIGH | Data misinterpretation | Always require Z or explicit TZ |
| **Country format undefined** | 🟡 MEDIUM | Validation failures | Choose ISO-2 or full names |
| **No row-level deduplication** | 🟡 MEDIUM | Duplicate transactions | Add check for (txn_id, amount, timestamp) combos |
| **Missing transaction amount bounds** | 🟡 MEDIUM | Outlier data | Define min/max amount ranges |
| **No timestamp range validation** | 🟡 MEDIUM | Invalid historical data | Define min/max dates |

---

### 3.2 Transaction-Specific Concerns

```yaml
Data Quality Checks:

1. Duplicate Detection (MEDIUM RISK):
   Issue: Same transaction_id appearing multiple times
   Check: Flag rows with duplicate transaction_id (keep first, reject others)
   Error Code: E102
   
2. Amount Anomalies (MEDIUM RISK):
   Issue: Extremely high or low amounts
   Check: Flag amounts < $0.01 or > $999M
   Warn: Amounts that are statistical outliers (3+ standard deviations)
   Error Code: E202, WARNING code W201
   
3. Timestamp Sequencing (LOW RISK):
   Issue: Transactions with timestamps out of logical order
   Check: No validation required (transactions can occur in any order)
   Note: Out-of-order timestamps are normal in distributed systems
   
4. Country-to-Amount Correlation (LOW RISK):
   Issue: Unusual transaction amounts for specific countries
   Check: Not validated at schema level (business logic concern)
   Note: Should be handled in downstream analysis
   
5. Temporal Clustering (INFORMATIONAL):
   Issue: Unusual clustering of transactions at same timestamp
   Check: Report frequency of identical timestamps
   Note: May indicate batch processing or system issues

6. Amount Precision Issues (MEDIUM RISK):
   Issue: Amounts with > 2 decimal places (e.g., 100.555)
   Check: Reject or round to 2 places based on config
   Error Code: E205
```

---

## 4. Pipeline Failure Criteria

### 4.1 Critical Failures (Stop Processing)

```
❌ PIPELINE STOPS if:

1. File-Level Failures:
   ✗ Input file not found
   ✗ File cannot be read (permission denied)
   ✗ File encoding is not UTF-8 (cannot be converted)
   ✗ CSV is malformed (cannot parse headers)
   ✗ Headers missing or empty

2. Schema Failures:
   ✗ Missing required column: transaction_id
   ✗ Missing required column: amount
   ✗ Missing required column: timestamp
   ✗ Missing required column: country
   ✗ Column count mismatch (extra columns OK, missing columns NOT OK)

3. Data Type Failures:
   ✗ 100% of amount values are unparseable as float
   ✗ 100% of timestamp values are unparseable as datetime
   ✗ Cannot determine country format (all values invalid)

4. Resource Failures:
   ✗ Out of memory during processing
   ✗ Disk full (cannot write output)
   ✗ Read timeout after 3 retries
```

**Exit Code**: `1` (Schema Error) or `2` (Runtime Error)

---

### 4.2 Conditional Failures (Configurable)

```
⚠️ PIPELINE STOPS if configured threshold exceeded:

1. Row Rejection Threshold:
   Threshold: > 50% of rows rejected (configurable)
   Reason: Data quality too poor to proceed
   Config: max_rejection_rate: 0.50
   Exit Code: 7
   
2. Column Error Threshold:
   Threshold: > 3 columns with > 30% error rate
   Reason: Multiple columns severely corrupted
   Config: max_failed_columns: 3
   Exit Code: 8

3. Critical Error Count:
   Threshold: > 1000 critical errors (E1xx, E2xx, E3xx, E4xx)
   Reason: Too many structural issues
   Config: max_critical_errors: 1000
   Exit Code: 9
```

**Default Behavior**: Log warnings but continue (warnings are non-fatal)

---

### 4.3 Non-Fatal Issues (Continue Processing)

```
⚠️ WARNINGS (Processing Continues):

1. Row-Level Warnings:
   W101 - transaction_id close to max length (>28 chars)
   W102 - amount is extremely large (> $100M)
   W103 - amount is very small (< $0.10)
   W104 - timestamp is recent (within last hour)
   W105 - timestamp is very old (> 10 years ago)
   W201 - country not in typical transaction markets
   W202 - High frequency of transactions same timestamp
   
2. File-Level Warnings:
   W301 - File size unusually large (> 50 MB)
   W302 - High duplicate rate (> 5%)
   W303 - Suspicious patterns detected
   
Action: Log to warnings, include in rejected data (optional), continue processing
```

---

## 5. Validation Rule Summary Table

### 5.1 By Severity

| Field | Rule | Severity | Action | Error Code |
|-------|------|----------|--------|-----------|
| transaction_id | Non-empty | CRITICAL | REJECT | E103 |
| transaction_id | Valid format | CRITICAL | REJECT | E101 |
| transaction_id | Unique in file | CRITICAL | REJECT | E102 |
| amount | Non-null | CRITICAL | REJECT | E204 |
| amount | Numeric | CRITICAL | REJECT | E201 |
| amount | Positive (> 0) | CRITICAL | REJECT | E203 |
| amount | Valid range | CRITICAL | REJECT | E202 |
| amount | Precision <= 2 | HIGH | REJECT | E205 |
| timestamp | Non-null | CRITICAL | REJECT | E305 |
| timestamp | Valid format | CRITICAL | REJECT | E301 |
| timestamp | Valid components | CRITICAL | REJECT | E302 |
| timestamp | Within date range | HIGH | REJECT | E303/E304 |
| country | Non-empty (if required) | CRITICAL | REJECT | E404 |
| country | Valid code/name | HIGH | REJECT | E401/E402/E403 |

---

## 6. Configuration Recommendations

```yaml
# filepath: config/schema_validation.yaml

schema:
  version: "1.0"
  fields:
    transaction_id:
      type: "string"
      required: true
      unique: true
      min_length: 8
      max_length: 32
      pattern: '^[A-Z0-9_-]{8,32}$'
      
    amount:
      type: "float"
      required: true
      min_value: 0.01
      max_value: 999999999.99
      decimal_places: 2
      
    timestamp:
      type: "datetime"
      required: true
      format: "ISO8601"
      min_date: "1970-01-01T00:00:00Z"
      max_date: "2030-12-31T23:59:59Z"
      timezone: "UTC"
      
    country:
      type: "string"
      required: true
      format: "ISO3166-1-alpha2"  # or "country_name"
      length: 2
      pattern: '^[A-Z]{2}$'

validation_strategy:
  stop_on_critical_error: true
  max_rejection_rate: 0.50
  max_failed_columns: 3
  max_critical_errors: 1000
  
error_handling:
  duplicate_strategy: "reject_subsequent"  # keep first occurrence
  unknown_country_strategy: "reject_row"
  malformed_amount_strategy: "reject_row"
  future_timestamp_strategy: "reject_row"

warnings:
  enable: true
  include_in_rejected_data: true
  log_level: "WARNING"
```

---

## 7. Testing Scenarios

### 7.1 Valid Records (Should Pass)

```csv
transaction_id,amount,timestamp,country
TXN_001_ABC,100.50,2025-01-13T14:30:00Z,US
TXN-2025-00001,999999999.99,2025-01-12,GB
TXN123456789,0.01,2024-01-01T00:00:00Z,JP
```

### 7.2 Invalid Records (Should Reject)

```csv
transaction_id,amount,timestamp,country
,100.50,2025-01-13T14:30:00Z,US  # E103 - missing txn_id
TXN_001,100.50,2025-01-13,XX  # E402 - invalid country
TXN_001_ABC,-50.00,2025-01-13T14:30:00Z,US  # E203 - negative amount
TXN_001_ABC,100.555,2025-01-13T14:30:00Z,US  # E205 - too many decimals
TXN_001_ABC,100.50,2050-01-13T14:30:00Z,US  # E303 - future date
```

---

## 8. Schema Clarification Questions

Before finalizing validation rules, please confirm:

1. **transaction_id Format**
   - [ ] Should be alphanumeric only?
   - [ ] Is underscore/hyphen allowed?
   - [ ] Min/max length requirements?
   - [ ] Auto-generated or source-provided?

2. **amount Field**
   - [ ] Always positive, never zero?
   - [ ] Always has currency units (USD, GBP, etc.)?
   - [ ] Maximum transaction limit?
   - [ ] Minimum transaction limit?

3. **timestamp Field**
   - [ ] Always UTC timezone?
   - [ ] Can contain milliseconds/microseconds?
   - [ ] What's the valid date range?
   - [ ] How to handle duplicate timestamps?

4. **country Field**
   - [ ] ISO 3166-1 alpha-2 codes (US, GB, JP) or full names?
   - [ ] Can be NULL/optional?
   - [ ] Specific countries allowed or all?

---

**Document Version**: 1.0  
**Last Updated**: January 13, 2026  
**Status**: Ready for Review