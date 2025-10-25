"""
Visualization Module for Teiko Clinical Trial

This module creates publication-quality visualizations for immune cell
population analysis.

Author: Technical Assessment Submission
Date: October 2025
"""

import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import Dict, List, Optional


class ImmunePopulationVisualizer:
    """
    Creates professional visualizations for immune cell population data.
    """
    
    # Color schemes for consistency
    RESPONDER_COLOR = '#2E86AB'  # Blue
    NON_RESPONDER_COLOR = '#A23B72'  # Purple/Pink
    POPULATION_COLORS = {
        'b_cell': '#E63946',
        'cd8_t_cell': '#F4A261',
        'cd4_t_cell': '#2A9D8F',
        'nk_cell': '#264653',
        'monocyte': '#E76F51'
    }
    
    def __init__(self):
        """Initialize visualizer with default styling."""
        self.template = 'plotly_white'
        
    def create_boxplot_comparison(
        self, 
        data: pd.DataFrame, 
        statistical_results: pd.DataFrame,
        show_significance: bool = True
    ) -> go.Figure:
        """
        Create boxplot comparing responders vs non-responders for all populations.
        
        Args:
            data: Sample data with response and percentage information
            statistical_results: DataFrame with p-values and significance
            show_significance: Whether to show significance markers
            
        Returns:
            Plotly Figure object
        """
        populations = sorted(data['population'].unique())
        
        # Create subplots
        fig = make_subplots(
            rows=1, 
            cols=len(populations),
            subplot_titles=[pop.replace('_', ' ').title() for pop in populations],
            horizontal_spacing=0.05
        )
        
        for idx, population in enumerate(populations, 1):
            pop_data = data[data['population'] == population].copy()
            
            # Add responders
            responders = pop_data[pop_data['response'] == 'yes']
            fig.add_trace(
                go.Box(
                    y=responders['percentage'],
                    name='Responders',
                    marker_color=self.RESPONDER_COLOR,
                    showlegend=(idx == 1),
                    boxmean='sd',
                ),
                row=1, 
                col=idx
            )
            
            # Add non-responders
            non_responders = pop_data[pop_data['response'] == 'no']
            fig.add_trace(
                go.Box(
                    y=non_responders['percentage'],
                    name='Non-responders',
                    marker_color=self.NON_RESPONDER_COLOR,
                    showlegend=(idx == 1),
                    boxmean='sd',
                ),
                row=1, 
                col=idx
            )
            
            # Add significance markers if requested
            if show_significance:
                pop_result = statistical_results[statistical_results['population'] == population]
                if not pop_result.empty:
                    sig_level = pop_result.iloc[0]['significance_level']
                    if sig_level != 'ns':
                        # Get max y value for annotation placement
                        max_y = max(pop_data['percentage'].max(), 
                                  responders['percentage'].max(),
                                  non_responders['percentage'].max())
                        
                        fig.add_annotation(
                            text=sig_level,
                            x=0.5,
                            y=max_y * 1.1,
                            xref=f'x{idx}',
                            yref=f'y{idx}',
                            showarrow=False,
                            font=dict(size=14, color='black'),
                            xanchor='center'
                        )
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Cell Population Frequencies: Responders vs Non-responders<br><sub>Melanoma Patients Treated with Miraclib (PBMC Samples)</sub>',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 18}
            },
            template=self.template,
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            font=dict(size=11)
        )
        
        # Update axes
        for i in range(1, len(populations) + 1):
            fig.update_yaxes(title_text="Relative Frequency (%)", row=1, col=i)
            fig.update_xaxes(showticklabels=False, row=1, col=i)
        
        return fig
    
    def create_population_distribution(self, summary_data: pd.DataFrame) -> go.Figure:
        """
        Create stacked bar chart showing population distribution across samples.
        
        Args:
            summary_data: Summary table with sample, population, and percentage
            
        Returns:
            Plotly Figure object
        """
        # Pivot data for stacked bar chart
        pivot_data = summary_data.pivot(
            index='sample', 
            columns='population', 
            values='percentage'
        ).reset_index()
        
        # Sample subset for visualization (too many samples would be cluttered)
        sample_size = min(50, len(pivot_data))
        pivot_subset = pivot_data.sample(n=sample_size, random_state=42)
        pivot_subset = pivot_subset.sort_values('sample')
        
        populations = [col for col in pivot_subset.columns if col != 'sample']
        
        fig = go.Figure()
        
        for population in populations:
            fig.add_trace(go.Bar(
                name=population.replace('_', ' ').title(),
                x=pivot_subset['sample'],
                y=pivot_subset[population],
                marker_color=self.POPULATION_COLORS.get(population, '#808080')
            ))
        
        fig.update_layout(
            title='Cell Population Distribution Across Samples',
            xaxis_title='Sample ID',
            yaxis_title='Relative Frequency (%)',
            barmode='stack',
            template=self.template,
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        fig.update_xaxes(showticklabels=False)
        
        return fig
    
    def create_mean_comparison_bar(
        self, 
        statistical_results: pd.DataFrame
    ) -> go.Figure:
        """
        Create grouped bar chart comparing mean frequencies between groups.
        
        Args:
            statistical_results: Statistical test results with means
            
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        populations = statistical_results['population'].values
        x_labels = [pop.replace('_', ' ').title() for pop in populations]
        
        # Responders
        fig.add_trace(go.Bar(
            name='Responders',
            x=x_labels,
            y=statistical_results['responders_mean'],
            error_y=dict(
                type='data',
                array=statistical_results['responders_std'],
                visible=True
            ),
            marker_color=self.RESPONDER_COLOR,
            text=statistical_results['responders_mean'].round(1),
            textposition='outside',
            texttemplate='%{text}%'
        ))
        
        # Non-responders
        fig.add_trace(go.Bar(
            name='Non-responders',
            x=x_labels,
            y=statistical_results['non_responders_mean'],
            error_y=dict(
                type='data',
                array=statistical_results['non_responders_std'],
                visible=True
            ),
            marker_color=self.NON_RESPONDER_COLOR,
            text=statistical_results['non_responders_mean'].round(1),
            textposition='outside',
            texttemplate='%{text}%'
        ))
        
        # Add significance markers
        for idx, row in statistical_results.iterrows():
            if row['significance_level'] != 'ns':
                fig.add_annotation(
                    text=row['significance_level'],
                    x=idx,
                    y=max(row['responders_mean'] + row['responders_std'],
                          row['non_responders_mean'] + row['non_responders_std']) * 1.15,
                    showarrow=False,
                    font=dict(size=16, color='black')
                )
        
        fig.update_layout(
            title='Mean Cell Population Frequencies with Statistical Significance',
            xaxis_title='Cell Population',
            yaxis_title='Mean Relative Frequency (%) ± SD',
            barmode='group',
            template=self.template,
            height=500,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    def create_pvalue_plot(self, statistical_results: pd.DataFrame) -> go.Figure:
        """
        Create visualization of p-values with significance threshold.
        
        Args:
            statistical_results: Statistical test results
            
        Returns:
            Plotly Figure object
        """
        fig = go.Figure()
        
        populations = statistical_results['population'].values
        x_labels = [pop.replace('_', ' ').title() for pop in populations]
        p_values = statistical_results['p_value'].values
        
        # Use negative log10 scale for better visualization
        neg_log_p = -np.log10(p_values)
        
        # Color by significance
        colors = [
            self.RESPONDER_COLOR if p < 0.05 else '#CCCCCC' 
            for p in p_values
        ]
        
        fig.add_trace(go.Bar(
            x=x_labels,
            y=neg_log_p,
            marker_color=colors,
            text=[f'p={p:.4f}' for p in p_values],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>-log10(p) = %{y:.2f}<br>p-value = %{text}<extra></extra>'
        ))
        
        # Add significance threshold line
        fig.add_hline(
            y=-np.log10(0.05), 
            line_dash="dash", 
            line_color="red",
            annotation_text="α = 0.05",
            annotation_position="right"
        )
        
        fig.update_layout(
            title='Statistical Significance of Cell Population Differences',
            xaxis_title='Cell Population',
            yaxis_title='-log₁₀(p-value)',
            template=self.template,
            height=400,
            showlegend=False
        )
        
        return fig


def create_all_visualizations(
    summary_data: pd.DataFrame,
    response_data: pd.DataFrame,
    statistical_results: pd.DataFrame
) -> Dict[str, go.Figure]:
    """
    Generate all visualizations for the analysis.
    
    Args:
        summary_data: Complete sample summary table
        response_data: Data for responder vs non-responder comparison
        statistical_results: Statistical test results
        
    Returns:
        Dictionary of figure names to Plotly figures
    """
    visualizer = ImmunePopulationVisualizer()
    
    figures = {
        'boxplot_comparison': visualizer.create_boxplot_comparison(
            response_data, 
            statistical_results
        ),
        'mean_comparison': visualizer.create_mean_comparison_bar(
            statistical_results
        ),
        'p_value_plot': visualizer.create_pvalue_plot(
            statistical_results
        ),
        'population_distribution': visualizer.create_population_distribution(
            summary_data
        )
    }
    
    return figures
