"""
Data Analysis Tool Implementation
Provides data analysis, visualization, and transformation capabilities
"""

import logging
from typing import Dict, List, Any, Optional, Union, Tuple
import json
import re
import math
from datetime import datetime

logger = logging.getLogger(__name__)

class DataAnalyzerTool:
    """
    Data analysis tool providing capabilities for analyzing structured data,
    generating insights, and basic visualizations.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize data analyzer tool with configuration."""
        self.config = config or {}
        
        # Check for optional visualization package
        try:
            import matplotlib
            matplotlib.use('agg')  # Non-interactive backend
            self.visualization_available = True
        except ImportError:
            logger.warning("Matplotlib not available, visualization features will be limited")
            self.visualization_available = False
            
    def analyze_numerical_data(self, 
                              data: List[float], 
                              operation: str = "basic_stats") -> Dict[str, Any]:
        """
        Analyze numerical data with various statistical operations.
        
        Args:
            data: List of numerical values
            operation: Type of analysis to perform
                Options: basic_stats, distribution, outliers
                
        Returns:
            Dictionary containing analysis results
        """
        if not data:
            return {"error": "No data provided"}
            
        # Filter out non-numerical values
        try:
            numeric_data = [float(x) for x in data if isinstance(x, (int, float)) or 
                          (isinstance(x, str) and re.match(r'^-?\d+(\.\d+)?$', x))]
        except (ValueError, TypeError):
            return {"error": "Data contains invalid numerical values"}
            
        if not numeric_data:
            return {"error": "No valid numerical data found"}
            
        if operation == "basic_stats":
            return self._calculate_basic_stats(numeric_data)
        elif operation == "distribution":
            return self._analyze_distribution(numeric_data)
        elif operation == "outliers":
            return self._find_outliers(numeric_data)
        else:
            return {"error": f"Unknown operation: {operation}"}
            
    def _calculate_basic_stats(self, data: List[float]) -> Dict[str, Any]:
        """Calculate basic statistical measures."""
        n = len(data)
        
        # Sort data for easier calculations
        sorted_data = sorted(data)
        
        # Basic measures
        total = sum(data)
        mean = total / n
        minimum = sorted_data[0]
        maximum = sorted_data[-1]
        
        # Median
        if n % 2 == 0:
            median = (sorted_data[n//2-1] + sorted_data[n//2]) / 2
        else:
            median = sorted_data[n//2]
            
        # Variance and standard deviation
        squared_diffs = [(x - mean) ** 2 for x in data]
        variance = sum(squared_diffs) / n
        std_dev = math.sqrt(variance)
        
        # Range and quartiles
        data_range = maximum - minimum
        q1_index = n // 4
        q3_index = 3 * n // 4
        q1 = sorted_data[q1_index]
        q3 = sorted_data[q3_index]
        iqr = q3 - q1
        
        return {
            "count": n,
            "mean": mean,
            "median": median,
            "min": minimum,
            "max": maximum,
            "range": data_range,
            "q1": q1,
            "q3": q3,
            "iqr": iqr,
            "variance": variance,
            "std_dev": std_dev,
            "sum": total
        }
        
    def _analyze_distribution(self, data: List[float]) -> Dict[str, Any]:
        """Analyze the distribution of numerical data."""
        n = len(data)
        
        # Calculate basic stats
        basic_stats = self._calculate_basic_stats(data)
        
        # Create histogram bins
        num_bins = min(10, n // 5) if n > 10 else 5
        min_val = basic_stats["min"]
        max_val = basic_stats["max"]
        bin_width = (max_val - min_val) / num_bins if max_val > min_val else 1.0
        
        # Count values in each bin
        bins = []
        bin_counts = [0] * num_bins
        
        for i in range(num_bins):
            bin_start = min_val + i * bin_width
            bin_end = min_val + (i + 1) * bin_width
            bins.append((bin_start, bin_end))
            
            # Last bin includes the max value
            if i == num_bins - 1:
                bin_counts[i] = sum(1 for x in data if bin_start <= x <= bin_end)
            else:
                bin_counts[i] = sum(1 for x in data if bin_start <= x < bin_end)
                
        # Determine distribution type based on skewness
        skewness = self._calculate_skewness(data)
        
        if abs(skewness) < 0.5:
            distribution_type = "approximately normal"
        elif skewness < -0.5:
            distribution_type = "negatively skewed"
        else:
            distribution_type = "positively skewed"
            
        # Check for bimodality
        if num_bins >= 3:
            middle_bins = bin_counts[1:-1]
            edge_bins = [bin_counts[0], bin_counts[-1]]
            if max(middle_bins) > max(edge_bins) and min(middle_bins) < max(middle_bins) / 2:
                possible_modes = []
                for i, count in enumerate(bin_counts):
                    if i > 0 and i < len(bin_counts) - 1:
                        if count > bin_counts[i-1] and count > bin_counts[i+1]:
                            possible_modes.append(i)
                if len(possible_modes) > 1:
                    distribution_type = "possibly multimodal"
            
        return {
            "basic_stats": basic_stats,
            "bin_count": num_bins,
            "bins": [{"range": [round(start, 2), round(end, 2)], "count": count} 
                    for (start, end), count in zip(bins, bin_counts)],
            "skewness": skewness,
            "distribution_type": distribution_type,
            "histogram_data": {
                "counts": bin_counts,
                "bin_edges": [b[0] for b in bins] + [bins[-1][1]]
            }
        }
        
    def _calculate_skewness(self, data: List[float]) -> float:
        """Calculate the skewness of a distribution."""
        n = len(data)
        if n < 3:
            return 0.0
            
        mean = sum(data) / n
        m2 = sum((x - mean) ** 2 for x in data) / n
        m3 = sum((x - mean) ** 3 for x in data) / n
        
        if m2 == 0:
            return 0.0
            
        return m3 / (m2 ** (3/2))
        
    def _find_outliers(self, data: List[float]) -> Dict[str, Any]:
        """Find outliers in the data using IQR method."""
        stats = self._calculate_basic_stats(data)
        
        q1 = stats["q1"]
        q3 = stats["q3"]
        iqr = stats["iqr"]
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = []
        non_outliers = []
        
        for value in data:
            if value < lower_bound or value > upper_bound:
                outliers.append(value)
            else:
                non_outliers.append(value)
                
        return {
            "outlier_count": len(outliers),
            "outliers": sorted(outliers),
            "non_outliers_count": len(non_outliers),
            "bounds": {
                "lower": lower_bound,
                "upper": upper_bound
            },
            "percent_outliers": len(outliers) / len(data) * 100 if data else 0
        }
        
    def analyze_time_series(self, 
                          timestamps: List[str], 
                          values: List[float],
                          operation: str = "trend_analysis") -> Dict[str, Any]:
        """
        Analyze time series data.
        
        Args:
            timestamps: List of timestamps in ISO format
            values: List of values corresponding to timestamps
            operation: Type of analysis to perform
                Options: trend_analysis, seasonality, forecasting
                
        Returns:
            Dictionary containing analysis results
        """
        if len(timestamps) != len(values):
            return {"error": "Timestamps and values must have the same length"}
            
        if not timestamps or not values:
            return {"error": "No data provided"}
            
        # Parse timestamps
        try:
            parsed_timestamps = []
            for ts in timestamps:
                if isinstance(ts, str):
                    parsed_timestamps.append(datetime.fromisoformat(ts.replace('Z', '+00:00')))
                elif isinstance(ts, (int, float)):
                    parsed_timestamps.append(datetime.fromtimestamp(ts))
                else:
                    return {"error": "Invalid timestamp format"}
        except ValueError:
            return {"error": "Invalid timestamp format"}
            
        # Ensure data is ordered by time
        time_value_pairs = sorted(zip(parsed_timestamps, values))
        ordered_times = [t for t, _ in time_value_pairs]
        ordered_values = [v for _, v in time_value_pairs]
        
        if operation == "trend_analysis":
            return self._analyze_trend(ordered_times, ordered_values)
        elif operation == "seasonality":
            return {"error": "Seasonality analysis not implemented yet"}
        elif operation == "forecasting":
            return {"error": "Forecasting not implemented yet"}
        else:
            return {"error": f"Unknown operation: {operation}"}
            
    def _analyze_trend(self, timestamps: List[datetime], values: List[float]) -> Dict[str, Any]:
        """Analyze trends in time series data."""
        n = len(values)
        
        # Basic stats on values
        value_stats = self._calculate_basic_stats(values)
        
        # Calculate overall change
        first_value = values[0]
        last_value = values[-1]
        absolute_change = last_value - first_value
        
        if first_value != 0:
            percent_change = (absolute_change / abs(first_value)) * 100
        else:
            percent_change = float('inf') if absolute_change > 0 else float('-inf') if absolute_change < 0 else 0
            
        # Calculate time range
        start_time = timestamps[0]
        end_time = timestamps[-1]
        duration_seconds = (end_time - start_time).total_seconds()
        
        # Determine direction
        if absolute_change > 0:
            direction = "increasing"
        elif absolute_change < 0:
            direction = "decreasing"
        else:
            direction = "stable"
            
        # Calculate simple moving average (last 5 points or fewer)
        sma_window = min(5, n)
        sma = sum(values[-sma_window:]) / sma_window
        
        # Linear regression for trend line
        x_values = [(ts - start_time).total_seconds() / duration_seconds for ts in timestamps]
        slope, intercept = self._linear_regression(x_values, values)
        
        # Volatility
        if n > 1:
            differences = [abs(values[i] - values[i-1]) for i in range(1, n)]
            volatility = sum(differences) / (n - 1)
        else:
            volatility = 0
            
        # Rate of change (per day)
        if duration_seconds > 0:
            rate_per_day = absolute_change / (duration_seconds / 86400)  # 86400 seconds per day
        else:
            rate_per_day = 0
            
        return {
            "value_stats": value_stats,
            "trend": {
                "direction": direction,
                "absolute_change": absolute_change,
                "percent_change": percent_change,
                "slope": slope,
                "intercept": intercept
            },
            "time_range": {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "duration_days": duration_seconds / 86400
            },
            "moving_average": sma,
            "volatility": volatility,
            "rate_of_change_per_day": rate_per_day
        }
        
    def _linear_regression(self, x: List[float], y: List[float]) -> Tuple[float, float]:
        """Calculate slope and intercept for linear regression."""
        n = len(x)
        if n < 2:
            return 0, 0
            
        sum_x = sum(x)
        sum_y = sum(y)
        sum_xy = sum(x[i] * y[i] for i in range(n))
        sum_xx = sum(x[i] ** 2 for i in range(n))
        
        # Calculate slope (m) and intercept (b) for y = mx + b
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x ** 2) if (n * sum_xx - sum_x ** 2) != 0 else 0
        intercept = (sum_y - slope * sum_x) / n
        
        return slope, intercept

    def visualize_data(self, 
                     data: Dict[str, Any], 
                     chart_type: str, 
                     options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create data visualizations as base64-encoded images.
        
        Args:
            data: Data to visualize
            chart_type: Type of chart to create (bar, line, pie, scatter, etc.)
            options: Visualization options
            
        Returns:
            Dictionary with visualization results and metadata
        """
        if not self.visualization_available:
            return {"error": "Visualization requires matplotlib which is not available"}
            
        options = options or {}
        
        # Import here so initialization doesn't require matplotlib
        try:
            import matplotlib.pyplot as plt
            import base64
            import io
            
            # Set up figure
            width = options.get("width", 8)
            height = options.get("height", 5)
            fig = plt.figure(figsize=(width, height))
            plt.clf()
            
            # Set title and labels
            title = options.get("title", "")
            x_label = options.get("x_label", "")
            y_label = options.get("y_label", "")
            
            if title:
                plt.title(title)
            if x_label:
                plt.xlabel(x_label)
            if y_label:
                plt.ylabel(y_label)
                
            # Create the requested chart
            if chart_type == "bar":
                self._create_bar_chart(data, options)
            elif chart_type == "line":
                self._create_line_chart(data, options)
            elif chart_type == "pie":
                self._create_pie_chart(data, options)
            elif chart_type == "scatter":
                self._create_scatter_chart(data, options)
            else:
                return {"error": f"Unsupported chart type: {chart_type}"}
                
            # Add grid if requested
            if options.get("grid", False):
                plt.grid(True, alpha=0.3)
                
            # Add legend if applicable
            if options.get("show_legend", True) and (chart_type != "pie"):
                plt.legend()
                
            # Convert plot to base64-encoded image
            buf = io.BytesIO()
            plt.tight_layout()
            plt.savefig(buf, format="png")
            buf.seek(0)
            img_data = base64.b64encode(buf.getvalue()).decode("utf-8")
            
            plt.close()
            
            return {
                "base64_image": f"data:image/png;base64,{img_data}",
                "chart_type": chart_type,
                "title": title
            }
            
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            return {"error": f"Error creating visualization: {str(e)}"}
            
    def _create_bar_chart(self, data: Dict[str, Any], options: Dict[str, Any]) -> None:
        """Create a bar chart."""
        import matplotlib.pyplot as plt
        
        # Extract data
        categories = data.get("categories", [])
        values = data.get("values", [])
        
        if not categories or not values or len(categories) != len(values):
            raise ValueError("Bar chart requires equal length categories and values lists")
            
        # Set colors
        colors = options.get("colors", ["#1f77b4"])
        if len(colors) < len(categories):
            colors = colors * (len(categories) // len(colors) + 1)
            
        # Create bars
        plt.bar(
            range(len(categories)), 
            values, 
            color=colors[:len(categories)], 
            alpha=options.get("alpha", 0.8),
            width=options.get("bar_width", 0.8)
        )
        
        # Set x-axis labels
        plt.xticks(range(len(categories)), categories, rotation=options.get("x_rotation", 0))
        
        # Add value labels
        if options.get("show_values", False):
            for i, v in enumerate(values):
                plt.text(i, v, str(round(v, 1)), ha="center", va="bottom")
                
    def _create_line_chart(self, data: Dict[str, Any], options: Dict[str, Any]) -> None:
        """Create a line chart."""
        import matplotlib.pyplot as plt
        
        # Handle single or multiple series
        if "series" in data:
            # Multiple series
            series_list = data["series"]
            for series in series_list:
                x_values = series.get("x", list(range(len(series.get("y", [])))))
                y_values = series.get("y", [])
                
                if not y_values:
                    continue
                    
                plt.plot(
                    x_values, 
                    y_values, 
                    label=series.get("name", ""),
                    marker=series.get("marker", options.get("marker", "o")),
                    linestyle=series.get("linestyle", options.get("linestyle", "-")),
                    linewidth=series.get("linewidth", options.get("linewidth", 2)),
                    color=series.get("color")
                )
        else:
            # Single series
            x_values = data.get("x", list(range(len(data.get("y", [])))))
            y_values = data.get("y", [])
            
            if not y_values:
                raise ValueError("Line chart requires y values")
                
            plt.plot(
                x_values, 
                y_values, 
                marker=options.get("marker", "o"),
                linestyle=options.get("linestyle", "-"),
                linewidth=options.get("linewidth", 2),
                label=options.get("label", "")
            )
            
        # Add horizontal/vertical lines if specified
        if "h_line" in options:
            plt.axhline(y=options["h_line"], color='r', linestyle='--')
        if "v_line" in options:
            plt.axvline(x=options["v_line"], color='r', linestyle='--')
            
    def _create_pie_chart(self, data: Dict[str, Any], options: Dict[str, Any]) -> None:
        """Create a pie chart."""
        import matplotlib.pyplot as plt
        
        # Extract data
        labels = data.get("labels", [])
        values = data.get("values", [])
        
        if not values:
            raise ValueError("Pie chart requires values")
            
        # Handle missing or incomplete labels
        if not labels or len(labels) != len(values):
            labels = [f"Item {i}" for i in range(len(values))]
            
        # Set colors
        colors = options.get("colors")
        
        # Create pie chart
        plt.pie(
            values, 
            labels=None,
            colors=colors,
            autopct=options.get("show_percentages", True) and '%1.1f%%' or None,
            shadow=options.get("shadow", False),
            startangle=options.get("start_angle", 90)
        )
        
        # Equal aspect ratio ensures circular pie
        plt.axis('equal')
        
        # Add legend
        if options.get("show_legend", True):
            plt.legend(labels, loc=options.get("legend_location", "best"))
            
    def _create_scatter_chart(self, data: Dict[str, Any], options: Dict[str, Any]) -> None:
        """Create a scatter chart."""
        import matplotlib.pyplot as plt
        
        # Handle single or multiple series
        if "series" in data:
            # Multiple series
            series_list = data["series"]
            for series in series_list:
                x_values = series.get("x", [])
                y_values = series.get("y", [])
                
                if not x_values or not y_values or len(x_values) != len(y_values):
                    continue
                    
                plt.scatter(
                    x_values, 
                    y_values, 
                    label=series.get("name", ""),
                    alpha=series.get("alpha", options.get("alpha", 0.7)),
                    s=series.get("size", options.get("size", 50)),
                    c=series.get("color")
                )
        else:
            # Single series
            x_values = data.get("x", [])
            y_values = data.get("y", [])
            
            if not x_values or not y_values or len(x_values) != len(y_values):
                raise ValueError("Scatter chart requires equal length x and y values")
                
            plt.scatter(
                x_values, 
                y_values, 
                alpha=options.get("alpha", 0.7),
                s=options.get("size", 50),
                label=options.get("label", "")
            )
            
        # Add trend line if requested
        if options.get("trend_line", False):
            slope, intercept = self._linear_regression(x_values, y_values)
            x_min, x_max = min(x_values), max(x_values)
            plt.plot(
                [x_min, x_max],
                [x_min * slope + intercept, x_max * slope + intercept],
                'r--',
                label=f"Trend: y = {slope:.2f}x + {intercept:.2f}"
            )
