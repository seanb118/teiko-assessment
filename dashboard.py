"""
Interactive Dashboard for Teiko Clinical Trial Analysis

This Dash application provides an interactive interface for exploring
immune cell population data and statistical results.

Author: Technical Assessment Submission
Date: October 2025
"""

import dash
from dash import dcc, html, dash_table
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import json
from pathlib import Path

from database import ClinicalTrialDB
from analysis import ImmunePopulationAnalyzer
from visualization import ImmunePopulationVisualizer


# Initialize Dash app
app = dash.Dash(
    __name__,
    title="Teiko Clinical Trial Dashboard",
    update_title="Loading...",
    suppress_callback_exceptions=True
)

# Load data
DB_PATH = "clinical_trial.db"
OUTPUT_DIR = Path("./outputs")

# Initialize database connection
db = ClinicalTrialDB(DB_PATH)

# Load pre-computed data
summary_df = db.get_sample_summary()
response_data = db.get_melanoma_pbmc_responder_data()
baseline_summary = db.get_baseline_melanoma_miraclib_summary()

# Perform analysis
analyzer = ImmunePopulationAnalyzer(response_data)
statistical_results = analyzer.compare_responders_vs_nonresponders()

# Initialize visualizer
visualizer = ImmunePopulationVisualizer()

# App layout
app.layout = html.Div([
    # Header
    html.Div([
        html.H1("Teiko Clinical Trial Analysis Dashboard", 
                style={'textAlign': 'center', 'color': '#2E86AB', 'marginBottom': '10px'}),
        html.H3("Immune Cell Population Analysis: Melanoma Treatment Response",
                style={'textAlign': 'center', 'color': '#666', 'marginBottom': '30px'}),
    ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '10px'}),
    
    # Navigation tabs
    dcc.Tabs(id='tabs', value='overview', children=[
        dcc.Tab(label='📊 Data Overview', value='overview'),
        dcc.Tab(label='🔬 Statistical Analysis', value='statistics'),
        dcc.Tab(label='📈 Visualizations', value='visualizations'),
        dcc.Tab(label='🔍 Data Subset', value='subset'),
    ], style={'marginTop': '20px', 'marginBottom': '20px'}),
    
    # Content area
    html.Div(id='tab-content', style={'padding': '20px'})
    
], style={'padding': '20px', 'maxWidth': '1400px', 'margin': '0 auto', 'fontFamily': 'Arial, sans-serif'})


# Callback for tab content
@app.callback(
    Output('tab-content', 'children'),
    Input('tabs', 'value')
)
def render_tab_content(tab):
    if tab == 'overview':
        return render_overview_tab()
    elif tab == 'statistics':
        return render_statistics_tab()
    elif tab == 'visualizations':
        return render_visualizations_tab()
    elif tab == 'subset':
        return render_subset_tab()


def render_overview_tab():
    """Render the data overview tab."""
    
    # Summary statistics
    total_samples = summary_df['sample'].nunique()
    total_populations = summary_df['population'].nunique()
    
    return html.Div([
        html.H2("Data Overview", style={'color': '#2E86AB', 'borderBottom': '2px solid #2E86AB', 'paddingBottom': '10px'}),
        
        # Key metrics
        html.Div([
            html.Div([
                html.H3(f"{total_samples}", style={'color': '#2E86AB', 'fontSize': '48px', 'margin': '0'}),
                html.P("Total Samples", style={'color': '#666', 'fontSize': '18px'}),
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8f9fa', 
                     'borderRadius': '10px', 'flex': '1', 'margin': '10px'}),
            
            html.Div([
                html.H3(f"{total_populations}", style={'color': '#A23B72', 'fontSize': '48px', 'margin': '0'}),
                html.P("Cell Populations", style={'color': '#666', 'fontSize': '18px'}),
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8f9fa', 
                     'borderRadius': '10px', 'flex': '1', 'margin': '10px'}),
            
            html.Div([
                html.H3(f"{len(summary_df):,}", style={'color': '#2A9D8F', 'fontSize': '48px', 'margin': '0'}),
                html.P("Total Records", style={'color': '#666', 'fontSize': '18px'}),
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#f8f9fa', 
                     'borderRadius': '10px', 'flex': '1', 'margin': '10px'}),
        ], style={'display': 'flex', 'justifyContent': 'space-around', 'marginTop': '20px'}),
        
        # Summary table
        html.H3("Sample Summary Table", style={'marginTop': '40px', 'color': '#333'}),
        html.P("Showing relative frequencies of each cell population for all samples", 
               style={'color': '#666', 'fontSize': '14px'}),
        
        dash_table.DataTable(
            data=summary_df.head(100).to_dict('records'),
            columns=[{'name': i, 'id': i} for i in summary_df.columns],
            page_size=20,
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'left',
                'padding': '10px',
                'fontSize': '12px'
            },
            style_header={
                'backgroundColor': '#2E86AB',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ]
        ),
        
        html.P(f"Showing first 100 of {len(summary_df)} total records", 
               style={'marginTop': '10px', 'fontSize': '12px', 'color': '#666'}),
    ])


def render_statistics_tab():
    """Render the statistical analysis tab."""
    
    significant_pops = analyzer.get_significant_populations()
    
    return html.Div([
        html.H2("Statistical Analysis: Responders vs Non-responders", 
                style={'color': '#2E86AB', 'borderBottom': '2px solid #2E86AB', 'paddingBottom': '10px'}),
        
        # Key findings
        html.Div([
            html.H3("Key Findings", style={'color': '#333'}),
            html.P(f"Analysis includes melanoma patients treated with miraclib (PBMC samples only)", 
                   style={'fontSize': '14px', 'color': '#666'}),
            html.P(f"Statistical method: Mann-Whitney U Test (two-sided, α = 0.05)", 
                   style={'fontSize': '14px', 'color': '#666'}),
            
            html.Div([
                html.H4(f"{len(significant_pops)}", 
                       style={'color': '#E63946', 'fontSize': '36px', 'margin': '0'}),
                html.P("Cell populations with significant differences", 
                      style={'color': '#666', 'fontSize': '16px'}),
            ], style={'textAlign': 'center', 'padding': '20px', 'backgroundColor': '#fff5f5', 
                     'borderRadius': '10px', 'margin': '20px 0', 'border': '2px solid #E63946'}),
            
            html.Ul([
                html.Li(f"{pop.replace('_', ' ').title()}", style={'fontSize': '16px', 'margin': '10px 0'})
                for pop in significant_pops
            ]) if significant_pops else html.P("No significant differences found", 
                                                style={'fontSize': '16px', 'fontStyle': 'italic'}),
        ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '10px', 'marginTop': '20px'}),
        
        # Statistical results table
        html.H3("Detailed Statistical Results", style={'marginTop': '40px', 'color': '#333'}),
        
        dash_table.DataTable(
            data=statistical_results.to_dict('records'),
            columns=[
                {'name': 'Population', 'id': 'population'},
                {'name': 'Resp. Mean (%)', 'id': 'responders_mean'},
                {'name': 'Resp. SD', 'id': 'responders_std'},
                {'name': 'Non-Resp. Mean (%)', 'id': 'non_responders_mean'},
                {'name': 'Non-Resp. SD', 'id': 'non_responders_std'},
                {'name': 'Difference (%)', 'id': 'mean_difference'},
                {'name': 'p-value', 'id': 'p_value'},
                {'name': "Cohen's d", 'id': 'cohens_d'},
                {'name': 'Significance', 'id': 'significance_level'},
            ],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '12px',
                'fontSize': '12px'
            },
            style_header={
                'backgroundColor': '#2E86AB',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                },
                {
                    'if': {
                        'filter_query': '{significant} = true',
                    },
                    'backgroundColor': '#fff5f5',
                    'fontWeight': 'bold'
                }
            ]
        ),
        
        # Interpretation guide
        html.Div([
            html.H4("Interpretation Guide", style={'color': '#333', 'marginTop': '20px'}),
            html.Ul([
                html.Li("*** p < 0.001: Extremely significant"),
                html.Li("** p < 0.01: Very significant"),
                html.Li("* p < 0.05: Significant"),
                html.Li("ns: Not significant"),
            ], style={'fontSize': '14px', 'color': '#666'}),
            html.P("Cohen's d effect size: |d| < 0.2 (small), 0.2-0.8 (medium), > 0.8 (large)", 
                   style={'fontSize': '14px', 'color': '#666', 'fontStyle': 'italic'}),
        ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '10px', 'marginTop': '20px'}),
    ])


def render_visualizations_tab():
    """Render the visualizations tab."""
    
    # Create visualizations
    boxplot_fig = visualizer.create_boxplot_comparison(response_data, statistical_results)
    mean_comparison_fig = visualizer.create_mean_comparison_bar(statistical_results)
    pvalue_fig = visualizer.create_pvalue_plot(statistical_results)
    
    return html.Div([
        html.H2("Interactive Visualizations", 
                style={'color': '#2E86AB', 'borderBottom': '2px solid #2E86AB', 'paddingBottom': '10px'}),
        
        # Boxplot comparison
        html.H3("Cell Population Frequency Distributions", style={'marginTop': '30px', 'color': '#333'}),
        html.P("Boxplots showing distribution of cell population frequencies between responders and non-responders. " +
               "Stars indicate statistical significance.", 
               style={'fontSize': '14px', 'color': '#666'}),
        dcc.Graph(figure=boxplot_fig),
        
        # Mean comparison
        html.H3("Mean Frequency Comparison", style={'marginTop': '40px', 'color': '#333'}),
        html.P("Bar chart comparing mean frequencies with standard deviations. " +
               "Stars indicate statistically significant differences.", 
               style={'fontSize': '14px', 'color': '#666'}),
        dcc.Graph(figure=mean_comparison_fig),
        
        # P-value plot
        html.H3("Statistical Significance Overview", style={'marginTop': '40px', 'color': '#333'}),
        html.P("Visualization of p-values on -log₁₀ scale. Values above the red line are statistically significant (p < 0.05).", 
               style={'fontSize': '14px', 'color': '#666'}),
        dcc.Graph(figure=pvalue_fig),
    ])


def render_subset_tab():
    """Render the data subset analysis tab."""
    
    samples_by_project = baseline_summary['samples_by_project']
    subjects_by_response = baseline_summary['subjects_by_response']
    subjects_by_sex = baseline_summary['subjects_by_sex']
    
    return html.Div([
        html.H2("Baseline Melanoma PBMC Samples", 
                style={'color': '#2E86AB', 'borderBottom': '2px solid #2E86AB', 'paddingBottom': '10px'}),
        
        html.P("Analysis of melanoma patients treated with miraclib at baseline (time_from_treatment_start = 0)", 
               style={'fontSize': '14px', 'color': '#666', 'marginTop': '10px'}),
        
        # Summary cards
        html.Div([
            # Samples by project
            html.Div([
                html.H3("Samples by Project", style={'color': '#333', 'fontSize': '18px', 'marginBottom': '15px'}),
                html.Div([
                    html.Div([
                        html.Strong(project, style={'fontSize': '16px'}),
                        html.Span(f": {count} samples", style={'fontSize': '16px', 'marginLeft': '10px'})
                    ], style={'margin': '8px 0'})
                    for project, count in samples_by_project.items()
                ]),
                html.Div([
                    html.Strong("Total:", style={'fontSize': '18px', 'color': '#2E86AB'}),
                    html.Span(f" {sum(samples_by_project.values())} samples", 
                             style={'fontSize': '18px', 'marginLeft': '10px', 'color': '#2E86AB'})
                ], style={'marginTop': '15px', 'paddingTop': '15px', 'borderTop': '2px solid #ddd'})
            ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '10px', 
                     'flex': '1', 'margin': '10px'}),
            
            # Subjects by response
            html.Div([
                html.H3("Subjects by Response", style={'color': '#333', 'fontSize': '18px', 'marginBottom': '15px'}),
                html.Div([
                    html.Div([
                        html.Strong("Responders", style={'fontSize': '24px', 'color': '#2E86AB'}),
                        html.H2(str(subjects_by_response.get('yes', 0)), 
                               style={'color': '#2E86AB', 'margin': '10px 0'})
                    ], style={'textAlign': 'center', 'margin': '10px'}),
                    html.Div([
                        html.Strong("Non-responders", style={'fontSize': '24px', 'color': '#A23B72'}),
                        html.H2(str(subjects_by_response.get('no', 0)), 
                               style={'color': '#A23B72', 'margin': '10px 0'})
                    ], style={'textAlign': 'center', 'margin': '10px'}),
                ])
            ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '10px', 
                     'flex': '1', 'margin': '10px'}),
            
            # Subjects by sex
            html.Div([
                html.H3("Subjects by Sex", style={'color': '#333', 'fontSize': '18px', 'marginBottom': '15px'}),
                html.Div([
                    html.Div([
                        html.Strong("Male", style={'fontSize': '24px', 'color': '#264653'}),
                        html.H2(str(subjects_by_sex.get('M', 0)), 
                               style={'color': '#264653', 'margin': '10px 0'})
                    ], style={'textAlign': 'center', 'margin': '10px'}),
                    html.Div([
                        html.Strong("Female", style={'fontSize': '24px', 'color': '#E76F51'}),
                        html.H2(str(subjects_by_sex.get('F', 0)), 
                               style={'color': '#E76F51', 'margin': '10px 0'})
                    ], style={'textAlign': 'center', 'margin': '10px'}),
                ])
            ], style={'backgroundColor': '#f8f9fa', 'padding': '20px', 'borderRadius': '10px', 
                     'flex': '1', 'margin': '10px'}),
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'marginTop': '20px'}),
        
        # Detailed breakdown table
        html.H3("Detailed Breakdown", style={'marginTop': '40px', 'color': '#333'}),
        
        dash_table.DataTable(
            data=baseline_summary['detailed_breakdown'],
            columns=[
                {'name': 'Project', 'id': 'project_id'},
                {'name': 'Response', 'id': 'response'},
                {'name': 'Sex', 'id': 'sex'},
                {'name': 'Sample Count', 'id': 'sample_count'},
                {'name': 'Subject Count', 'id': 'subject_count'},
            ],
            style_table={'overflowX': 'auto'},
            style_cell={
                'textAlign': 'center',
                'padding': '12px',
                'fontSize': '14px'
            },
            style_header={
                'backgroundColor': '#2E86AB',
                'color': 'white',
                'fontWeight': 'bold'
            },
            style_data_conditional=[
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f8f9fa'
                }
            ]
        ),
    ])


# Run server
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=8050)