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

### Design Rationale

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

### Scalability to Production

This schema is designed to scale to **hundreds of projects, thousands of samples, and millions of records**:

#### 1. **Horizontal Scaling**
- Narrow table design enables efficient partitioning by:
  - Project (for multi-tenant isolation)
  - Time period (for temporal queries)
  - Sample type (for different assay types)

#### 2. **Query Performance**
- Indexed foreign keys enable sub-second joins even with millions of rows
- Composite indexes optimize common analytical queries
- SQLite can handle 100+ million rows on modern hardware

#### 3. **Analytics Flexibility**
The schema supports diverse analytical needs:
- **Longitudinal analysis**: Time-series queries via `time_from_treatment_start`
- **Cohort analysis**: Easy filtering by demographics, treatment, response
- **Population-specific analysis**: Efficient filtering by cell type
- **Cross-project comparisons**: Project-level aggregations
- **Machine learning pipelines**: Direct export to pandas/numpy

#### 4. **Future Extensions**
Easy to extend for:
- Additional cell populations (just add rows to cell_counts)
- New metadata fields (add columns to appropriate tables)
- Multiple assay types (extend sample_type)
- Additional measurements (new tables with foreign keys to samples)

#### 5. **Production Considerations**
For production deployment with massive scale:
- **PostgreSQL/MySQL**: Replace SQLite for concurrent access
- **Partitioning**: Partition cell_counts by project or date
- **Materialized Views**: Pre-compute common aggregations
- **Caching Layer**: Redis for frequently accessed statistics
- **Time-series Database**: Consider TimescaleDB for temporal data

---

## Code Architecture

### Design Philosophy

The codebase follows **object-oriented design principles** with clear separation of concerns:

1. **Modularity**: Each module has a single, well-defined responsibility
2. **Reusability**: Classes and functions are designed for reuse across different analyses
3. **Testability**: Clear interfaces make unit testing straightforward
4. **Maintainability**: Comprehensive docstrings and type hints
5. **Scalability**: Efficient algorithms and data structures

### Module Responsibilities

#### `database.py` - Data Layer
**Purpose**: Encapsulates all database operations

**Key Features**:
- `ClinicalTrialDB` class manages database lifecycle
- Context manager support (`with` statements)
- Parameterized queries prevent SQL injection
- Efficient batch loading
- Type-safe query methods

**Why this design**:
- Separates data access from business logic
- Easy to swap SQLite for PostgreSQL
- Enables database mocking for tests
- Single source of truth for queries

#### `analysis.py` - Statistical Layer
**Purpose**: Performs hypothesis testing and statistical computations

**Key Features**:
- `ImmunePopulationAnalyzer` class for statistical tests
- Mann-Whitney U test (non-parametric)
- Effect size calculations (Cohen's d)
- Comprehensive reporting

**Why this design**:
- Domain-specific logic isolated from I/O
- Stateless design enables parallel processing
- Easy to add new statistical tests
- Scientific rigor with proper methodology

**Statistical Method Choice**:
- **Mann-Whitney U Test**: Selected because:
  - No assumption of normal distribution (biological data often skewed)
  - Robust to outliers
  - Widely accepted in clinical/immunology research
  - Appropriate for independent samples comparison

#### `visualization.py` - Presentation Layer
**Purpose**: Creates publication-quality visualizations

**Key Features**:
- `ImmunePopulationVisualizer` class for consistent styling
- Multiple chart types (boxplots, bar charts, p-value plots)
- Interactive Plotly figures
- Significance annotations

**Why this design**:
- Consistent visual style across all plots
- Easy to export to different formats (HTML, PNG, PDF)
- Separates visualization logic from data processing
- Reusable plotting functions

#### `main.py` - Orchestration Layer
**Purpose**: Coordinates the complete analysis workflow

**Key Features**:
- Sequential execution of all analysis parts
- Progress reporting
- Error handling
- Output management

**Why this design**:
- Clear workflow visibility
- Easy to run complete analysis
- Reproducible results
- Single entry point for automation

#### `dashboard.py` - Interaction Layer
**Purpose**: Provides interactive web interface

**Key Features**:
- Dash-based web application
- Multiple tabs for different analyses
- Interactive tables and charts
- Real-time data exploration

**Why this design**:
- User-friendly interface for non-technical stakeholders
- No installation required (web browser)
- Interactive exploration enables deeper insights
- Professional appearance suitable for client presentation

### Key Design Decisions

#### 1. **Object-Oriented vs Functional**
- Used **OOP for state management** (database connections, configurations)
- Used **functional programming for stateless operations** (statistical calculations)
- Best of both paradigms

#### 2. **Type Hints**
```python
def get_sample_summary(self) -> pd.DataFrame:
```
- Improves IDE autocomplete
- Catches type errors early
- Self-documenting code

#### 3. **Pandas Integration**
- SQLite → Pandas for analysis
- Leverages Pandas' powerful data manipulation
- Seamless integration with scientific Python ecosystem

#### 4. **Error Handling**
```python
if db_file.exists():
    db_file.unlink()
```
- Defensive programming practices
- Graceful degradation
- Clear error messages

---

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

---

## 🧪 Quality Assurance

### Code Quality
- **Type hints**: All functions have type annotations
- **Docstrings**: Comprehensive documentation for all modules
- **Comments**: Inline comments for complex logic
- **Naming**: Descriptive variable and function names
- **PEP 8**: Follows Python style guidelines

### Data Quality
- **Foreign key constraints**: Ensure referential integrity
- **Unique constraints**: Prevent duplicate records
- **Check constraints**: Validate categorical values
- **Indexes**: Optimize query performance

### Statistical Rigor
- **Appropriate test selection**: Non-parametric test for non-normal data
- **Effect size reporting**: Beyond just p-values
- **Two-sided testing**: Conservative approach
- **Multiple comparison awareness**: Documented in report

---


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
5. **Multivariate Analysis**: PCA, clustering, dimension reduction

### Dashboard Enhancements
1. **User Authentication**: Secure access control
2. **Export Functionality**: Direct export of filtered data
3. **Real-time Updates**: WebSocket for live data
4. **Custom Reports**: User-defined analysis parameters
5. **Collaboration**: Shared annotations and notes

## 📧 Contact

For questions about this assessment or technical implementation details, please contact the author Xiang at seanbai@berkeley.edu

---

## License

This code is submitted as part of a technical assessment for Teiko Bio.

---

**End of README**
