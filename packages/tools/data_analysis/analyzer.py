"""Data analysis tool for the space project."""

from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
from utils.logging import logger
from utils.metrics import collector

class DataAnalyzer:
    """Analyzes data and generates insights."""
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        cache_size: int = 1000
    ):
        self.config = config or {}
        self.cache_size = cache_size
        self.logger = logger
        self.metrics = collector
        self._cache: Dict[str, Any] = {}
    
    async def analyze_text_data(
        self,
        texts: List[str],
        analysis_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze a collection of texts."""
        analysis_types = analysis_types or ["basic", "sentiment", "topics"]
        results = {}
        
        with self.metrics.measure_time("text_analysis"):
            try:
                if "basic" in analysis_types:
                    results["basic"] = await self._basic_text_analysis(texts)
                if "sentiment" in analysis_types:
                    results["sentiment"] = await self._analyze_sentiment(texts)
                if "topics" in analysis_types:
                    results["topics"] = await self._extract_topics(texts)
                    
                return results
                
            except Exception as e:
                self.logger.error(f"Error in text analysis: {e}")
                return {}
    
    async def analyze_numeric_data(
        self,
        data: Union[List[float], np.ndarray],
        analysis_types: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze numeric data."""
        analysis_types = analysis_types or ["statistics", "distribution"]
        results = {}
        
        with self.metrics.measure_time("numeric_analysis"):
            try:
                data_array = np.array(data)
                
                if "statistics" in analysis_types:
                    results["statistics"] = self._compute_statistics(data_array)
                if "distribution" in analysis_types:
                    results["distribution"] = self._analyze_distribution(data_array)
                    
                return results
                
            except Exception as e:
                self.logger.error(f"Error in numeric analysis: {e}")
                return {}
    
    async def find_correlations(
        self,
        data: Dict[str, List[float]],
        threshold: float = 0.5
    ) -> List[Dict[str, Any]]:
        """Find correlations between numeric variables."""
        with self.metrics.measure_time("correlation_analysis"):
            try:
                variables = list(data.keys())
                correlations = []
                
                for i, var1 in enumerate(variables):
                    for var2 in variables[i+1:]:
                        correlation = np.corrcoef(
                            data[var1],
                            data[var2]
                        )[0, 1]
                        
                        if abs(correlation) >= threshold:
                            correlations.append({
                                "variables": (var1, var2),
                                "correlation": correlation,
                                "strength": self._correlation_strength(correlation)
                            })
                
                return correlations
                
            except Exception as e:
                self.logger.error(f"Error in correlation analysis: {e}")
                return []
    
    async def detect_anomalies(
        self,
        data: Union[List[float], np.ndarray],
        method: str = "zscore",
        threshold: float = 3.0
    ) -> List[Dict[str, Any]]:
        """Detect anomalies in numeric data."""
        with self.metrics.measure_time("anomaly_detection"):
            try:
                data_array = np.array(data)
                anomalies = []
                
                if method == "zscore":
                    z_scores = np.abs(
                        (data_array - np.mean(data_array))
                        / np.std(data_array)
                    )
                    anomaly_indices = np.where(z_scores > threshold)[0]
                    
                    for idx in anomaly_indices:
                        anomalies.append({
                            "index": int(idx),
                            "value": float(data_array[idx]),
                            "zscore": float(z_scores[idx])
                        })
                
                return anomalies
                
            except Exception as e:
                self.logger.error(f"Error in anomaly detection: {e}")
                return []
    
    async def _basic_text_analysis(
        self,
        texts: List[str]
    ) -> Dict[str, Any]:
        """Perform basic text analysis."""
        try:
            total_chars = sum(len(text) for text in texts)
            total_words = sum(len(text.split()) for text in texts)
            
            return {
                "document_count": len(texts),
                "total_characters": total_chars,
                "total_words": total_words,
                "average_length": total_chars / len(texts),
                "average_words": total_words / len(texts)
            }
        except Exception as e:
            self.logger.error(f"Error in basic text analysis: {e}")
            return {}
    
    async def _analyze_sentiment(
        self,
        texts: List[str]
    ) -> List[Dict[str, float]]:
        """Analyze sentiment of texts."""
        # TODO: Implement proper sentiment analysis
        return [{"positive": 0.0, "negative": 0.0, "neutral": 1.0}] * len(texts)
    
    async def _extract_topics(
        self,
        texts: List[str]
    ) -> List[Dict[str, float]]:
        """Extract topics from texts."""
        # TODO: Implement proper topic extraction
        return [{"topic1": 1.0}] * len(texts)
    
    def _compute_statistics(
        self,
        data: np.ndarray
    ) -> Dict[str, float]:
        """Compute basic statistics for numeric data."""
        return {
            "mean": float(np.mean(data)),
            "median": float(np.median(data)),
            "std": float(np.std(data)),
            "min": float(np.min(data)),
            "max": float(np.max(data))
        }
    
    def _analyze_distribution(
        self,
        data: np.ndarray
    ) -> Dict[str, Any]:
        """Analyze the distribution of numeric data."""
        return {
            "skewness": float(self._compute_skewness(data)),
            "kurtosis": float(self._compute_kurtosis(data)),
            "is_normal": self._test_normality(data)
        }
    
    def _compute_skewness(self, data: np.ndarray) -> float:
        """Compute skewness of data."""
        n = len(data)
        mean = np.mean(data)
        std = np.std(data)
        return (
            np.sum((data - mean) ** 3)
            / (n * std ** 3) if std > 0 else 0
        )
    
    def _compute_kurtosis(self, data: np.ndarray) -> float:
        """Compute kurtosis of data."""
        n = len(data)
        mean = np.mean(data)
        std = np.std(data)
        return (
            np.sum((data - mean) ** 4)
            / (n * std ** 4) if std > 0 else 0
        ) - 3
    
    def _test_normality(self, data: np.ndarray) -> bool:
        """Test if data follows normal distribution."""
        # Simple normality test based on skewness and kurtosis
        skewness = abs(self._compute_skewness(data))
        kurtosis = abs(self._compute_kurtosis(data))
        return skewness < 0.5 and kurtosis < 0.5
    
    def _correlation_strength(self, correlation: float) -> str:
        """Interpret correlation strength."""
        abs_corr = abs(correlation)
        if abs_corr >= 0.8:
            return "very strong"
        elif abs_corr >= 0.6:
            return "strong"
        elif abs_corr >= 0.4:
            return "moderate"
        elif abs_corr >= 0.2:
            return "weak"
        else:
            return "very weak"