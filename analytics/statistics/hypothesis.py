import os
import pandas as pd
import numpy as np
import scipy.stats as stats
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)

class HypothesisTestingEngine:
    """
    A rigorous inferential statistics engine that programmatically selects tests
    based on assumption evaluations (Normality and Variance).
    """
    def __init__(self, alpha: float = 0.05, economic_threshold: float = 0.2):
        self.alpha = alpha
        self.economic_threshold = economic_threshold # |Effect Size| > 0.2 is considered economically significant

    def _check_normality(self, data: pd.Series) -> bool:
        """
        Uses Shapiro-Wilk for N < 5000, otherwise falls back to Jarque-Bera.
        Returns True if NORMAL (fails to reject H0).
        """
        data = data.dropna()
        n = len(data)
        if n < 30:
            return False # Too small to assume normality safely
            
        if n < 5000:
            stat, p = stats.shapiro(data)
        else:
            stat, p = stats.jarque_bera(data)
            
        return p >= self.alpha # If p >= alpha, we fail to reject normality

    def _check_equal_variance(self, sample_a: pd.Series, sample_b: pd.Series) -> bool:
        """
        Uses Levene's test for equal variances (more robust to non-normality than Bartlett's).
        Returns True if EQUAL VARIANCES (fails to reject H0).
        """
        stat, p = stats.levene(sample_a.dropna(), sample_b.dropna())
        return p >= self.alpha

    def _cohens_d(self, x: pd.Series, y: pd.Series) -> float:
        """Calculates standardized mean difference (Cohen's d)."""
        nx, ny = len(x), len(y)
        dof = nx + ny - 2
        pool_sd = np.sqrt(((nx - 1) * x.var(ddof=1) + (ny - 1) * y.var(ddof=1)) / dof)
        d = (x.mean() - y.mean()) / pool_sd
        return d

    def _cliffs_delta(self, x: pd.Series, y: pd.Series) -> float:
        """
        Calculates Cliff's Delta (non-parametric effect size).
        Approximated efficiently using Mann-Whitney U statistic.
        delta = (2U / (nx * ny)) - 1
        """
        nx, ny = len(x), len(y)
        u, _ = stats.mannwhitneyu(x, y, alternative='two-sided')
        delta = (2 * u / (nx * ny)) - 1
        return delta

    def run_two_sample_test(self, sample_a: pd.Series, sample_b: pd.Series) -> Dict[str, Any]:
        """
        Dynamically selects and executes the correct two-sample test based on assumptions.
        """
        a, b = sample_a.dropna(), sample_b.dropna()
        n_a, n_b = len(a), len(b)
        
        if n_a < 30 or n_b < 30:
            raise ValueError(f"Insufficient sample sizes (A={n_a}, B={n_b}). Minimum 30 required.")

        # 1. Evaluate Assumptions
        a_normal = self._check_normality(a)
        b_normal = self._check_normality(b)
        equal_var = self._check_equal_variance(a, b)
        
        # 2. Dynamic Test Selection
        if a_normal and b_normal:
            if equal_var:
                test_name = "Student's t-test (Independent)"
                stat, p_value = stats.ttest_ind(a, b, equal_var=True)
            else:
                test_name = "Welch's t-test (Unequal Variances)"
                stat, p_value = stats.ttest_ind(a, b, equal_var=False)
                
            effect_name = "Cohen's d"
            effect_val = self._cohens_d(a, b)
            
        else:
            test_name = "Mann-Whitney U (Non-Parametric)"
            stat, p_value = stats.mannwhitneyu(a, b, alternative='two-sided')
            
            effect_name = "Cliff's Delta"
            effect_val = self._cliffs_delta(a, b)
            
        is_stat_sig = p_value < self.alpha
        is_econ_sig = abs(effect_val) >= self.economic_threshold
        
        return {
            "test_used": test_name,
            "sample_a_size": n_a,
            "sample_b_size": n_b,
            "p_value": p_value,
            "is_statistically_significant": is_stat_sig,
            "effect_size_metric": effect_name,
            "effect_size_value": effect_val,
            "is_economically_significant": is_econ_sig
        }
