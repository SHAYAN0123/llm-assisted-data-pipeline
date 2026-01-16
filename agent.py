"""
Intelligent Data Pipeline Agent
Provides autonomous analysis, recommendations, and insights for CSV data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any


class DataPipelineAgent:
    """Autonomous agent for intelligent data analysis and recommendations"""
    
    def __init__(self):
        self.data = None
        self.analysis = {}
        self.recommendations = []
        self.insights = []
    
    def analyze(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform comprehensive autonomous analysis"""
        self.data = df
        
        self._assess_data_quality()
        self._detect_patterns()
        self._generate_recommendations()
        self._extract_insights()
        
        return {
            'quality_score': self._calculate_quality_score(),
            'data_profile': self._profile_data(),
            'issues_detected': self._detect_issues(),
            'recommendations': self.recommendations,
            'insights': self.insights,
            'suggested_actions': self._suggest_actions()
        }
    
    def _assess_data_quality(self) -> None:
        """Assess overall data quality"""
        if self.data is None or self.data.empty:
            return
        
        total_cells = self.data.shape[0] * self.data.shape[1]
        missing_cells = self.data.isna().sum().sum()
        duplicate_rows = len(self.data) - len(self.data.drop_duplicates())
        
        self.analysis['missing_pct'] = (missing_cells / total_cells * 100) if total_cells > 0 else 0
        self.analysis['duplicate_pct'] = (duplicate_rows / len(self.data) * 100) if len(self.data) > 0 else 0
        self.analysis['completeness'] = 100 - self.analysis['missing_pct']
    
    def _detect_patterns(self) -> None:
        """Detect patterns and correlations in data"""
        if self.data is None or self.data.empty:
            return
        
        # Numeric columns analysis
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in numeric_cols:
            series = self.data[col].dropna()
            if len(series) > 0:
                skewness = series.skew()
                if abs(skewness) > 1:
                    self.insights.append(f"Column '{col}' has skewed distribution (skewness: {skewness:.2f})")
        
        # Categorical patterns
        categorical_cols = self.data.select_dtypes(include=['object']).columns.tolist()
        for col in categorical_cols:
            unique_ratio = len(self.data[col].unique()) / len(self.data)
            if unique_ratio > 0.9:
                self.insights.append(f"Column '{col}' has high cardinality ({len(self.data[col].unique())} unique values)")
    
    def _generate_recommendations(self) -> None:
        """Generate intelligent recommendations"""
        if self.data is None or self.data.empty:
            return
        
        # Missing value recommendations
        if self.analysis.get('missing_pct', 0) > 10:
            missing_cols = self.data.columns[self.data.isna().any()].tolist()
            self.recommendations.append({
                'type': 'missing_values',
                'severity': 'high',
                'message': f"High missing data ({self.analysis['missing_pct']:.1f}%) in columns: {missing_cols}",
                'action': 'Consider imputation or removal of rows with missing values'
            })
        
        # Duplicate recommendations
        if self.analysis.get('duplicate_pct', 0) > 5:
            self.recommendations.append({
                'type': 'duplicates',
                'severity': 'medium',
                'message': f"Found {self.analysis['duplicate_pct']:.1f}% duplicate rows",
                'action': 'Remove duplicates before further analysis'
            })
        
        # Data type recommendations
        for col in self.data.columns:
            if self.data[col].dtype == 'object':
                # Check if it looks like numeric
                try:
                    pd.to_numeric(self.data[col].dropna())
                    self.recommendations.append({
                        'type': 'data_type',
                        'severity': 'low',
                        'message': f"Column '{col}' appears to be numeric but stored as text",
                        'action': 'Convert to numeric for better analysis'
                    })
                except:
                    pass
    
    def _extract_insights(self) -> None:
        """Extract meaningful business insights"""
        if self.data is None or self.data.empty:
            return
        
        # Size insight
        self.insights.append(f"Dataset contains {len(self.data):,} rows and {len(self.data.columns)} columns")
        
        # Numeric summary
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            self.insights.append(f"Numeric columns: {', '.join(numeric_cols.tolist())}")
        
        # Categorical summary
        categorical_cols = self.data.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            self.insights.append(f"Categorical columns: {', '.join(categorical_cols.tolist())}")
    
    def _calculate_quality_score(self) -> float:
        """Calculate data quality score 0-100"""
        if self.data is None or self.data.empty:
            return 0
        
        completeness = self.analysis.get('completeness', 0)
        duplicates_penalty = self.analysis.get('duplicate_pct', 0) * 0.5
        
        score = completeness - duplicates_penalty
        return max(0, min(100, score))
    
    def _profile_data(self) -> Dict[str, Any]:
        """Generate data profile"""
        if self.data is None:
            return {}
        
        return {
            'rows': len(self.data),
            'columns': len(self.data.columns),
            'memory_usage_mb': self.data.memory_usage(deep=True).sum() / 1024 / 1024,
            'numeric_columns': len(self.data.select_dtypes(include=[np.number]).columns),
            'categorical_columns': len(self.data.select_dtypes(include=['object']).columns),
            'datetime_columns': len(self.data.select_dtypes(include=['datetime64']).columns),
        }
    
    def _detect_issues(self) -> List[str]:
        """Detect specific data quality issues"""
        issues = []
        
        if self.data is None:
            return issues
        
        # Check for all-null columns
        for col in self.data.columns:
            if self.data[col].isna().all():
                issues.append(f"Column '{col}' is completely empty")
        
        # Check for outliers in numeric columns
        numeric_cols = self.data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            series = self.data[col].dropna()
            if len(series) > 0:
                Q1 = series.quantile(0.25)
                Q3 = series.quantile(0.75)
                IQR = Q3 - Q1
                outliers = series[(series < Q1 - 1.5*IQR) | (series > Q3 + 1.5*IQR)]
                if len(outliers) > 0:
                    issues.append(f"Column '{col}' contains {len(outliers)} potential outliers")
        
        return issues
    
    def _suggest_actions(self) -> List[str]:
        """Suggest next actions for data processing"""
        actions = []
        
        if self.analysis.get('missing_pct', 0) > 0:
            actions.append("Handle missing values (impute or remove)")
        
        if self.analysis.get('duplicate_pct', 0) > 0:
            actions.append("Remove duplicate records")
        
        if len(self._detect_issues()) > 0:
            actions.append("Investigate and handle detected issues")
        
        actions.append("Validate data against business rules")
        actions.append("Export cleaned data for further analysis")
        
        return actions


def analyze_csv_intelligently(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Intelligent CSV analysis using autonomous agent
    
    Args:
        df: Pandas DataFrame to analyze
    
    Returns:
        Dict with comprehensive analysis and recommendations
    """
    agent = DataPipelineAgent()
    return agent.analyze(df)
