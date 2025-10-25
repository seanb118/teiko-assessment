"""
Database Module for Teiko Clinical Trial Analysis

This module handles database schema creation, data loading, and querying
for immune cell population analysis in clinical trials.

Author: Technical Assessment Submission
Date: October 2025
"""

import sqlite3
import pandas as pd
from typing import List, Dict, Any, Optional
from pathlib import Path


class ClinicalTrialDB:
    """
    Manages SQLite database operations for clinical trial immune cell data.
    
    This class implements a normalized relational database schema designed to:
    - Minimize data redundancy
    - Support efficient querying for various analytics
    - Scale to hundreds of projects and thousands of samples
    """
    
    def __init__(self, db_path: str = "clinical_trial.db"):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        
    def create_schema(self) -> None:
        """
        Create normalized relational database schema.
        
        Schema Design Rationale:
        ------------------------
        1. **projects**: Central registry of research projects
           - Allows easy filtering and aggregation by project
           - Supports project-level metadata
        
        2. **subjects**: Patient/subject information
           - Normalized to avoid redundancy (demographics stored once per subject)
           - Links to projects via foreign key
           - Supports subject-level analysis
        
        3. **samples**: Individual sample metadata
           - Links subjects to measurements
           - Captures temporal information (time_from_treatment_start)
           - Enables longitudinal analysis
        
        4. **cell_counts**: Actual measurement data
           - Narrow table design (one row per cell population per sample)
           - Highly efficient for aggregations and filtering
           - Easily extensible to new cell populations
        
        Scalability Considerations:
        ---------------------------
        - Indexed foreign keys for fast joins
        - Composite indexes on frequently queried columns
        - Normalized design prevents data duplication
        - Can handle millions of records with proper indexing
        - Narrow table design in cell_counts enables efficient analytics
        """
        cursor = self.conn.cursor()
        
        # Projects table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Subjects table (patient demographics and treatment info)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS subjects (
                subject_id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                condition TEXT NOT NULL,
                age INTEGER NOT NULL,
                sex TEXT NOT NULL,
                treatment TEXT NOT NULL,
                response TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(project_id),
                CHECK (sex IN ('M', 'F')),
                CHECK (response IN ('yes', 'no', NULL))
            )
        """)
        
        # Samples table (individual samples with temporal info)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS samples (
                sample_id TEXT PRIMARY KEY,
                subject_id TEXT NOT NULL,
                sample_type TEXT NOT NULL,
                time_from_treatment_start INTEGER NOT NULL,
                collection_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (subject_id) REFERENCES subjects(subject_id)
            )
        """)
        
        # Cell counts table (normalized: one row per population per sample)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cell_counts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sample_id TEXT NOT NULL,
                population TEXT NOT NULL,
                count INTEGER NOT NULL,
                FOREIGN KEY (sample_id) REFERENCES samples(sample_id),
                UNIQUE(sample_id, population)
            )
        """)
        
        # Create indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_subjects_project 
            ON subjects(project_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_subjects_condition_treatment 
            ON subjects(condition, treatment)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_samples_subject 
            ON samples(subject_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_samples_type_time 
            ON samples(sample_type, time_from_treatment_start)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cell_counts_sample 
            ON cell_counts(sample_id)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cell_counts_population 
            ON cell_counts(population)
        """)
        
        self.conn.commit()
        print("✓ Database schema created successfully")
        
    def load_data_from_csv(self, csv_path: str) -> None:
        """
        Load data from CSV file into normalized database tables.
        
        Args:
            csv_path: Path to the cell-count.csv file
        """
        print(f"Loading data from {csv_path}...")
        
        # Read CSV
        df = pd.read_csv(csv_path)
        print(f"✓ Loaded {len(df)} rows from CSV")
        
        # Cell population columns
        cell_populations = ['b_cell', 'cd8_t_cell', 'cd4_t_cell', 'nk_cell', 'monocyte']
        
        # Insert projects
        projects = df[['project']].drop_duplicates()
        projects.columns = ['project_id']
        projects.to_sql('projects', self.conn, if_exists='append', index=False)
        print(f"✓ Loaded {len(projects)} projects")
        
        # Insert subjects
        subjects = df[[
            'subject', 'project', 'condition', 'age', 'sex', 'treatment', 'response'
        ]].drop_duplicates(subset=['subject'])
        subjects.columns = [
            'subject_id', 'project_id', 'condition', 'age', 'sex', 'treatment', 'response'
        ]
        subjects.to_sql('subjects', self.conn, if_exists='append', index=False)
        print(f"✓ Loaded {len(subjects)} subjects")
        
        # Insert samples
        samples = df[['sample', 'subject', 'sample_type', 'time_from_treatment_start']].copy()
        samples.columns = ['sample_id', 'subject_id', 'sample_type', 'time_from_treatment_start']
        samples.to_sql('samples', self.conn, if_exists='append', index=False)
        print(f"✓ Loaded {len(samples)} samples")
        
        # Insert cell counts (normalized format)
        cell_count_records = []
        for _, row in df.iterrows():
            for population in cell_populations:
                cell_count_records.append({
                    'sample_id': row['sample'],
                    'population': population,
                    'count': row[population]
                })
        
        cell_counts_df = pd.DataFrame(cell_count_records)
        cell_counts_df.to_sql('cell_counts', self.conn, if_exists='append', index=False)
        print(f"✓ Loaded {len(cell_count_records)} cell count records")
        
        self.conn.commit()
        print("✓ All data loaded successfully")
        
    def get_sample_summary(self) -> pd.DataFrame:
        """
        Generate summary table of relative frequencies for each cell population.
        
        Returns:
            DataFrame with columns: sample, total_count, population, count, percentage
        """
        query = """
            SELECT 
                s.sample_id as sample,
                SUM(cc.count) OVER (PARTITION BY s.sample_id) as total_count,
                cc.population,
                cc.count,
                ROUND(100.0 * cc.count / SUM(cc.count) OVER (PARTITION BY s.sample_id), 2) as percentage
            FROM samples s
            JOIN cell_counts cc ON s.sample_id = cc.sample_id
            ORDER BY s.sample_id, cc.population
        """
        
        df = pd.read_sql_query(query, self.conn)
        return df
    
    def get_melanoma_pbmc_responder_data(self) -> pd.DataFrame:
        """
        Get PBMC samples from melanoma patients treated with miraclib,
        including response status for statistical analysis.
        
        Returns:
            DataFrame with sample data including response status
        """
        query = """
            SELECT 
                s.sample_id as sample,
                subj.response,
                cc.population,
                cc.count,
                ROUND(100.0 * cc.count / SUM(cc.count) OVER (PARTITION BY s.sample_id), 2) as percentage
            FROM samples s
            JOIN subjects subj ON s.subject_id = subj.subject_id
            JOIN cell_counts cc ON s.sample_id = cc.sample_id
            WHERE subj.condition = 'melanoma'
                AND subj.treatment = 'miraclib'
                AND s.sample_type = 'PBMC'
            ORDER BY s.sample_id, cc.population
        """
        
        df = pd.read_sql_query(query, self.conn)
        return df
    
    def get_baseline_melanoma_miraclib_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for baseline melanoma PBMC samples treated with miraclib.
        
        Returns:
            Dictionary with counts by project, response, and sex
        """
        query = """
            SELECT 
                subj.project_id,
                subj.response,
                subj.sex,
                COUNT(DISTINCT s.sample_id) as sample_count,
                COUNT(DISTINCT subj.subject_id) as subject_count
            FROM samples s
            JOIN subjects subj ON s.subject_id = subj.subject_id
            WHERE subj.condition = 'melanoma'
                AND subj.treatment = 'miraclib'
                AND s.sample_type = 'PBMC'
                AND s.time_from_treatment_start = 0
            GROUP BY subj.project_id, subj.response, subj.sex
            ORDER BY subj.project_id, subj.response, subj.sex
        """
        
        df = pd.read_sql_query(query, self.conn)
        
        # Calculate summary statistics
        summary = {
            'samples_by_project': df.groupby('project_id')['sample_count'].sum().to_dict(),
            'subjects_by_response': df.groupby('response')['subject_count'].sum().to_dict(),
            'subjects_by_sex': df.groupby('sex')['subject_count'].sum().to_dict(),
            'detailed_breakdown': df.to_dict('records')
        }
        
        return summary
    
    def close(self) -> None:
        """Close database connection."""
        self.conn.close()
        
    def __enter__(self):
        """Context manager entry."""
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()


def initialize_database(csv_path: str, db_path: str = "clinical_trial.db") -> ClinicalTrialDB:
    """
    Initialize database with schema and load data from CSV.
    
    Args:
        csv_path: Path to cell-count.csv file
        db_path: Path for SQLite database file
        
    Returns:
        Initialized ClinicalTrialDB instance
    """
    # Remove existing database if it exists
    db_file = Path(db_path)
    if db_file.exists():
        db_file.unlink()
        print(f"✓ Removed existing database: {db_path}")
    
    # Create and initialize database
    db = ClinicalTrialDB(db_path)
    db.create_schema()
    db.load_data_from_csv(csv_path)
    
    return db
