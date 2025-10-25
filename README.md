# Teiko Bio Assessment
## Overview

This project provides a comprehensive analysis platform for immune cell population data from clinical trials. It includes database management, statistical analysis, and an interactive dashboard for exploring treatment response patterns in melanoma patients.

**Author**: Xiang B 

---

## Quick Start

### Prerequisites
- Python 3.9 or higher
- UV for environment


### Installation & Running
Prerequisite is UV for env

```bash
uv venv
source .venv/bin/activate
uv pip install pandas numpy scipy plotly dash
```

The dashboard will be available at `http://localhost:8050`

---

## Project Structure

```
teiko-assessment/
├── main.py                # Main analysis orchestration script
├── database.py            # Database schema and data management
├── analysis.py            # Statistical analysis module
├── visualization.py       # Visualization generation
├── dashboard.py           # Interactive Dash web application
├── requirements.txt       # Python dependencies
├── README.md              # Current file/ reference
├── data/cell-count.csv    # Input data (provided)
└── outputs/               # Generated analysis outputs
    ├── part2_summary_table.csv
    ├── part3_statistical_results.csv
    ├── part3_statistical_report.txt
    ├── part3_boxplot_comparison.html
    ├── part3_mean_comparison.html
    ├── part3_p_value_plot.html
    ├── part3_population_distribution.html
    ├── part4_baseline_summary.csv
    └── part4_baseline_summary.json
```

---

## Database Schema Design

### Schema Overview

The database uses a **normalized relational design** with four main tables:

```sql
projects
  ├── project_id (PK)
  └── created_at

subjects
  ├── subject_id (PK)
  ├── project_id (FK → projects)
  ├── condition
  ├── age
  ├── sex
  ├── treatment
  └── response

samples
  ├── sample_id (PK)
  ├── subject_id (FK → subjects)
  ├── sample_type
  ├── time_from_treatment_start
  └── collection_date

cell_counts
  ├── id (PK)
  ├── sample_id (FK → samples)
  ├── population
  └── count
```

### Database Design Philosophy/Thoughts

#### 1. **Normalization Benefits**
- **Eliminates Redundancy**: Subject demographics (age, sex, condition) stored once per subject, not repeated for every sample
- **Data Integrity**: Foreign key constraints ensure referential integrity
- **Easy Updates**: Changes to subject information update in one place

Future considerations: For large amounts of data and future projects/partnerships where data formats are similar/condensed, it may be more reasonable to employ a more denormalized/OLAP design. This is especially true if storage is not the major concern and can be scaled in a cost efficient manner. This will allow ETL to be more efficient. If we are considering further scaling beyond that, a data mesh ideology could be implemented to give each study group/research team more governance in their data products.


#### 2. **Narrow Table Design (cell_counts)**
The cell_counts table uses a **narrow/long format** instead of wide format:
- **Wide format** (original CSV): One row per sample with columns for each cell type
- **Narrow format** (database): One row per cell population per sample

**Advantages**:
- Highly efficient for aggregations (SUM, AVG, etc.)
- Easy to add new cell populations without schema changes
- Optimal for filtering by population type
- Better query performance for analytical workloads
- Reduces storage with proper indexing

#### 3. **Indexing Strategy**
Strategic indexes on frequently queried columns:
```sql
-- Foreign key indexes for fast joins
idx_subjects_project (project_id)
idx_samples_subject (subject_id)
idx_cell_counts_sample (sample_id)

-- Analytical query indexes
idx_subjects_condition_treatment (condition, treatment)
idx_samples_type_time (sample_type, time_from_treatment_start)
idx_cell_counts_population (population)
```

**Scalability to Production**
This schema is designed to scale to hundreds of projects, thousands of samples, and millions of records:

1. Horizontal Scaling
Narrow table design enables efficient partitioning by:
Project (for multi-tenant isolation)
Time period (for temporal queries)
Sample type (for different assay types)

2. Query Performance
Indexed foreign keys enable sub-second joins even with millions of rows
Composite indexes optimize common analytical queries
SQLite can handle 100+ million rows on modern hardware; though for productionized analysis something like Snowflake or Redshift can be considered

3. Analytics Flexibility
The schema supports diverse analytical needs:

Longitudinal analysis: Time-series queries via time_from_treatment_start
Cohort analysis: Easy filtering by demographics, treatment, response
Population-specific analysis: Efficient filtering by cell type
Cross-project comparisons: Project-level aggregations



## Analysis Outputs

### Part 1: Data Management
- **Database**: `clinical_trial.db` (SQLite database with normalized schema)
- **Schema**: Documented in code and this README

### Part 2: Data Overview
- **`part2_summary_table.csv`**: Complete summary table with relative frequencies
  - Columns: sample, total_count, population, count, percentage
  - 52,500 rows (10,500 samples × 5 populations)

### Part 3: Statistical Analysis
- **`part3_statistical_results.csv`**: Detailed statistical test results
  - Descriptive statistics (mean, median, SD) for each group
  - Mann-Whitney U statistic and p-values
  - Effect sizes (Cohen's d)
  - Significance indicators

- **`part3_statistical_report.txt`**: Comprehensive written report
  - Executive summary of findings
  - Detailed results for all populations
  - Statistical methodology explanation

- **Visualizations** (HTML files):
  - `part3_boxplot_comparison.html`: Distribution comparison
  - `part3_mean_comparison.html`: Mean frequencies with error bars
  - `part3_p_value_plot.html`: Significance visualization
  - `part3_population_distribution.html`: Sample-wise distributions

### Part 4: Data Subset Analysis
- **`part4_baseline_summary.csv`**: Detailed breakdown by project/response/sex
- **`part4_baseline_summary.json`**: Structured summary for dashboard

---

## Statistical Methodology

### Hypothesis Testing Approach

**Null Hypothesis (H₀)**: No difference in cell population frequencies between responders and non-responders

**Alternative Hypothesis (H₁)**: Significant difference exists

**Test**: Mann-Whitney U Test (Wilcoxon rank-sum test)
- **Type**: Non-parametric, two-sided
- **Significance level**: α = 0.05
- **Rationale**: 
  - Does not assume normal distribution
  - Robust to outliers common in biological data
  - Appropriate for independent samples
  - Widely accepted in immunology research

**Effect Size**: Cohen's d
- Quantifies magnitude of difference
- Independent of sample size
- Interpretation: |d| < 0.2 (small), 0.2-0.8 (medium), > 0.8 (large)

### Key Findings

The analysis identifies cell populations with statistically significant differences in relative frequencies between treatment responders and non-responders in melanoma patients receiving miraclib. See the statistical report for detailed results.

---

## Dashboard Features

### Interactive Components

1. **Data Overview Tab**
   - Key metrics (total samples, populations, records)
   - Interactive summary table with pagination
   - Search and filter capabilities

2. **Statistical Analysis Tab**
   - Summary of significant findings
   - Detailed results table
   - Interpretation guide

3. **Visualizations Tab**
   - Interactive boxplots
   - Mean comparison charts
   - P-value visualization
   - All charts support zoom, pan, export

4. **Data Subset Tab**
   - Baseline sample summaries
   - Breakdown by project, response, sex
   - Interactive data tables

### Accessing the Dashboard

```bash
# Start the dashboard
python dashboard.py

# Open browser to:
http://localhost:8050
```

## Future Enhancements

### Technical Improvements
1. **Unit Tests**: pytest suite for all modules
2. **Integration Tests**: End-to-end workflow validation
3. **CI/CD Pipeline**: Automated testing and deployment
4. **Docker**: Containerization for portability
5. **API Layer**: REST API for programmatic access

### Analytical Extensions
1. **Machine Learning**: Predictive models for treatment response
2. **Longitudinal Analysis**: Time-series analysis of immune dynamics
3. **Batch Effects**: Account for project-level variation
4. **Sample Size Calculations**: Power analysis for study design

### Dashboard Enhancements
1. **User Authentication**: Secure access control
2. **Export Functionality**: Direct export of filtered data
3. **Real-time Updates**: WebSocket for live data
4. **Custom Reports**: User-defined analysis parameters
5. **UI Filter Functions**: Create custom filters for scientists/stakeholders

## Contact

For questions about this assessment or technical implementation details, please contact the author Xiang at seanbai@berkeley.edu

---

## License

This code is submitted as part of a technical assessment for Teiko Bio.

---

**End of README**
