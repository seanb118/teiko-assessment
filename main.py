"""
Main Analysis Script for Teiko Clinical Trial Assessment

This script orchestrates the complete analysis workflow:
1. Database initialization and data loading
2. Summary table generation
3. Statistical analysis
4. Data subset queries
5. Results export

Author: Technical Assessment Submission
Date: October 2025
"""

import sys
from pathlib import Path
import pandas as pd
import json

from database import initialize_database, ClinicalTrialDB
from analysis import analyze_treatment_response, ImmunePopulationAnalyzer
from visualization import create_all_visualizations


def print_section_header(title: str) -> None:
    """Print formatted section header."""
    print("\n" + "=" * 80)
    print(f" {title}")
    print("=" * 80 + "\n")


def main():
    """Execute complete analysis workflow."""
    
    print_section_header("TEIKO TECHNICAL ASSESSMENT - CLINICAL TRIAL ANALYSIS")
    
    # Configuration
    CSV_PATH = "./data/cell-count.csv"
    DB_PATH = "clinical_trial.db"
    OUTPUT_DIR = Path("./outputs")
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # ========================================================================
    # PART 1: DATA MANAGEMENT
    # ========================================================================
    print_section_header("PART 1: DATA MANAGEMENT")
    
    print("Initializing database and loading data...")
    db = initialize_database(CSV_PATH, DB_PATH)
    print("\n✓ Database initialization complete")
    
    # ========================================================================
    # PART 2: INITIAL ANALYSIS - DATA OVERVIEW
    # ========================================================================
    print_section_header("PART 2: INITIAL ANALYSIS - DATA OVERVIEW")
    
    print("Generating summary table of cell population frequencies...")
    summary_df = db.get_sample_summary()
    
    print(f"\n✓ Generated summary table with {len(summary_df)} rows")
    print(f"  - {summary_df['sample'].nunique()} unique samples")
    print(f"  - {summary_df['population'].nunique()} cell populations")
    
    # Display sample of summary table
    print("\nSample of summary table (first 10 rows):")
    print(summary_df.head(10).to_string(index=False))
    
    # Export summary table
    summary_output = OUTPUT_DIR / "part2_summary_table.csv"
    summary_df.to_csv(summary_output, index=False)
    print(f"\n✓ Summary table saved to: {summary_output}")
    
    # ========================================================================
    # PART 3: STATISTICAL ANALYSIS
    # ========================================================================
    print_section_header("PART 3: STATISTICAL ANALYSIS")
    
    print("Retrieving melanoma PBMC samples treated with miraclib...")
    response_data = db.get_melanoma_pbmc_responder_data()
    
    print(f"\n✓ Retrieved {len(response_data)} records")
    print(f"  - {response_data['sample'].nunique()} unique samples")
    print(f"  - Responders: {(response_data[response_data['response'] == 'yes']['sample'].nunique())}")
    print(f"  - Non-responders: {(response_data[response_data['response'] == 'no']['sample'].nunique())}")
    
    print("\nPerforming statistical analysis...")
    statistical_results, report = analyze_treatment_response(response_data, alpha=0.05)
    
    # Print statistical report
    print("\n" + report)
    
    # Export statistical results
    stats_output = OUTPUT_DIR / "part3_statistical_results.csv"
    statistical_results.to_csv(stats_output, index=False)
    print(f"\n✓ Statistical results saved to: {stats_output}")
    
    # Export detailed report
    report_output = OUTPUT_DIR / "part3_statistical_report.txt"
    with open(report_output, 'w') as f:
        f.write(report)
    print(f"✓ Statistical report saved to: {report_output}")
    
    # Create visualizations
    print("\nGenerating visualizations...")
    figures = create_all_visualizations(summary_df, response_data, statistical_results)
    
    # Export visualizations as HTML
    for name, fig in figures.items():
        fig_output = OUTPUT_DIR / f"part3_{name}.html"
        fig.write_html(str(fig_output))
        print(f"  ✓ Saved {name} to: {fig_output}")
    
    # ========================================================================
    # PART 4: DATA SUBSET ANALYSIS
    # ========================================================================
    print_section_header("PART 4: DATA SUBSET ANALYSIS")
    
    print("Querying baseline melanoma PBMC samples treated with miraclib...")
    baseline_summary = db.get_baseline_melanoma_miraclib_summary()
    
    print("\n✓ Baseline melanoma PBMC samples (time_from_treatment_start = 0):")
    print("\nSamples by Project:")
    for project, count in baseline_summary['samples_by_project'].items():
        print(f"  - {project}: {count} samples")
    
    print("\nSubjects by Response:")
    for response, count in baseline_summary['subjects_by_response'].items():
        print(f"  - {response.capitalize()}: {count} subjects")
    
    print("\nSubjects by Sex:")
    for sex, count in baseline_summary['subjects_by_sex'].items():
        print(f"  - {sex}: {count} subjects")
    
    # Export detailed breakdown
    breakdown_df = pd.DataFrame(baseline_summary['detailed_breakdown'])
    breakdown_output = OUTPUT_DIR / "part4_baseline_summary.csv"
    breakdown_df.to_csv(breakdown_output, index=False)
    print(f"\n✓ Detailed breakdown saved to: {breakdown_output}")
    
    # Export as JSON for dashboard
    json_output = OUTPUT_DIR / "part4_baseline_summary.json"
    with open(json_output, 'w') as f:
        json.dump(baseline_summary, f, indent=2)
    print(f"✓ JSON summary saved to: {json_output}")
    
    # ========================================================================
    # SUMMARY
    # ========================================================================
    print_section_header("ANALYSIS COMPLETE")
    
    print("All outputs saved to:", OUTPUT_DIR)
    print("\nGenerated files:")
    for file in sorted(OUTPUT_DIR.glob("*")):
        print(f"  - {file.name}")
    
    # Close database connection
    db.close()
    print("\n✓ Database connection closed")
    print("\n" + "=" * 80)
    print("Analysis workflow completed successfully!")
    print("=" * 80 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
