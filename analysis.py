"""
Statistical Analysis Module for Teiko Clinical Trial

This module performs statistical comparisons of immune cell populations
between treatment responders and non-responders.

Author: Technical Assessment Submission
Date: October 2025
"""

import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')


class ImmunePopulationAnalyzer:
    """
    Statistical analyzer for immune cell population frequencies.
    
    Performs hypothesis testing to identify cell populations with
    significant differences between treatment responders and non-responders.
    """
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize analyzer with sample data.
        
        Args:
            data: DataFrame with columns: sample, response, population, count, percentage
        """
        self.data = data
        self.populations = sorted(data['population'].unique())
        
    def compare_responders_vs_nonresponders(self, alpha: float = 0.05) -> pd.DataFrame:
        """
        Compare cell population frequencies between responders and non-responders.
        
        Uses Mann-Whitney U test (non-parametric) as it doesn't assume normal
        distribution, which is appropriate for biological data that may be skewed.
        
        Args:
            alpha: Significance level (default: 0.05)
            
        Returns:
            DataFrame with statistical test results for each population
        """
        results = []
        
        for population in self.populations:
            # Filter data for this population
            pop_data = self.data[self.data['population'] == population]
            
            # Separate responders and non-responders
            responders = pop_data[pop_data['response'] == 'yes']['percentage'].values
            non_responders = pop_data[pop_data['response'] == 'no']['percentage'].values
            
            # Calculate descriptive statistics
            resp_mean = np.mean(responders)
            resp_median = np.median(responders)
            resp_std = np.std(responders, ddof=1)
            resp_n = len(responders)
            
            nonresp_mean = np.mean(non_responders)
            nonresp_median = np.median(non_responders)
            nonresp_std = np.std(non_responders, ddof=1)
            nonresp_n = len(non_responders)
            
            statistic, p_value = stats.mannwhitneyu(
                responders, 
                non_responders, 
                alternative='two-sided'
            )
            
            pooled_std = np.sqrt(
                ((resp_n - 1) * resp_std**2 + (nonresp_n - 1) * nonresp_std**2) / 
                (resp_n + nonresp_n - 2)
            )
            cohens_d = (resp_mean - nonresp_mean) / pooled_std if pooled_std > 0 else 0
            
            is_significant = p_value < alpha
            
            results.append({
                'population': population,
                'responders_mean': round(resp_mean, 2),
                'responders_median': round(resp_median, 2),
                'responders_std': round(resp_std, 2),
                'responders_n': resp_n,
                'non_responders_mean': round(nonresp_mean, 2),
                'non_responders_median': round(nonresp_median, 2),
                'non_responders_std': round(nonresp_std, 2),
                'non_responders_n': nonresp_n,
                'mean_difference': round(resp_mean - nonresp_mean, 2),
                'mann_whitney_u': round(statistic, 2),
                'p_value': round(p_value, 4),
                'cohens_d': round(cohens_d, 3),
                'significant': is_significant,
                'significance_level': '***' if p_value < 0.001 else '**' if p_value < 0.01 else '*' if p_value < 0.05 else 'ns'
            })
        
        results_df = pd.DataFrame(results)
        results_df = results_df.sort_values('p_value')
        
        return results_df
    
    def get_significant_populations(self, alpha: float = 0.05) -> List[str]:
        """
        Identify cell populations with significant differences.
        
        Args:
            alpha: Significance level
            
        Returns:
            List of population names with significant differences
        """
        results = self.compare_responders_vs_nonresponders(alpha)
        significant = results[results['significant'] == True]['population'].tolist()
        
        return significant
    
    def generate_statistical_report(self, alpha: float = 0.05) -> str:
        """
        Generate a comprehensive statistical report.
        
        Args:
            alpha: Significance level
            
        Returns:
            Formatted string report
        """
        results = self.compare_responders_vs_nonresponders(alpha)
        significant_pops = self.get_significant_populations(alpha)
        
        report = []
        report.append("=" * 80)
        report.append("STATISTICAL ANALYSIS: RESPONDERS VS NON-RESPONDERS")
        report.append("=" * 80)
        report.append("")
        report.append(f"Analysis: Melanoma patients treated with miraclib (PBMC samples only)")
        report.append(f"Statistical Test: Mann-Whitney U Test (two-sided, α = {alpha})")
        report.append("")
        report.append("Rationale for Mann-Whitney U Test:")
        report.append("  • Non-parametric test (no assumption of normal distribution)")
        report.append("  • Robust to outliers in biological data")
        report.append("  • Compares distributions between two independent groups")
        report.append("  • Widely accepted in clinical and immunology research")
        report.append("")
        report.append("-" * 80)
        report.append("SUMMARY OF FINDINGS")
        report.append("-" * 80)
        report.append("")
        
        if significant_pops:
            report.append(f"Found {len(significant_pops)} cell population(s) with significant differences:")
            report.append("")
            for pop in significant_pops:
                pop_result = results[results['population'] == pop].iloc[0]
                report.append(f"• {pop.upper().replace('_', ' ')}")
                report.append(f"  - Responders: {pop_result['responders_mean']}% ± {pop_result['responders_std']}%")
                report.append(f"  - Non-responders: {pop_result['non_responders_mean']}% ± {pop_result['non_responders_std']}%")
                report.append(f"  - Difference: {pop_result['mean_difference']}%")
                report.append(f"  - p-value: {pop_result['p_value']:.4f} {pop_result['significance_level']}")
                report.append(f"  - Effect size (Cohen's d): {pop_result['cohens_d']:.3f}")
                report.append("")
        else:
            report.append("No cell populations showed significant differences at α = {alpha}.")
            report.append("")
        
        report.append("-" * 80)
        report.append("DETAILED RESULTS FOR ALL POPULATIONS")
        report.append("-" * 80)
        report.append("")
        
        # Format as table
        report.append(f"{'Population':<15} {'Resp Mean':<12} {'Non-Resp Mean':<15} {'Diff':<8} {'p-value':<10} {'Sig':<5}")
        report.append("-" * 80)
        
        for _, row in results.iterrows():
            pop_name = row['population'].replace('_', ' ').title()
            report.append(
                f"{pop_name:<15} "
                f"{row['responders_mean']:>6.2f}% ± {row['responders_std']:.2f}  "
                f"{row['non_responders_mean']:>6.2f}% ± {row['non_responders_std']:.2f}  "
                f"{row['mean_difference']:>6.2f}%  "
                f"{row['p_value']:<10.4f} "
                f"{row['significance_level']:<5}"
            )
        
        report.append("")
        report.append("Significance levels: *** p<0.001, ** p<0.01, * p<0.05, ns = not significant")
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)
    
    def get_boxplot_data(self) -> Dict[str, pd.DataFrame]:
        """
        Prepare data for boxplot visualization.
        
        Returns:
            Dictionary mapping population names to DataFrames with percentage data
        """
        boxplot_data = {}
        
        for population in self.populations:
            pop_data = self.data[self.data['population'] == population][['response', 'percentage']].copy()
            pop_data['response_label'] = pop_data['response'].map({'yes': 'Responders', 'no': 'Non-responders'})
            boxplot_data[population] = pop_data
        
        return boxplot_data


def analyze_treatment_response(data: pd.DataFrame, alpha: float = 0.05) -> Tuple[pd.DataFrame, str]:
    """
    Perform complete statistical analysis of treatment response.
    
    Args:
        data: Sample data with response information
        alpha: Significance level
        
    Returns:
        Tuple of (results DataFrame, report string)
    """
    analyzer = ImmunePopulationAnalyzer(data)
    results = analyzer.compare_responders_vs_nonresponders(alpha)
    report = analyzer.generate_statistical_report(alpha)
    
    return results, report
