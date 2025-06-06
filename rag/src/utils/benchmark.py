"""
Benchmarking Utility for RAG System

This module provides tools for measuring and analyzing performance of the RAG system,
including document processing, vector storage, and query operations.
"""

import time
import psutil
import json
import logging
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

try:
    import matplotlib.pyplot as plt
    import numpy as np
    PLOTTING_AVAILABLE = True
except ImportError:
    logger.warning("Matplotlib/Numpy not installed. Plotting functionality disabled.")
    PLOTTING_AVAILABLE = False


@dataclass
class BenchmarkResult:
    """Individual benchmark result data"""
    test_name: str
    operation: str
    dataset_size: int
    duration_seconds: float
    throughput: float  # operations per second
    memory_usage_mb: float
    timestamp: str = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary format"""
        return asdict(self)


class RAGBenchmark:
    """
    Benchmarking tool for measuring RAG system performance
    
    This class provides utilities for:
    - Measuring function performance (time, memory usage)
    - Recording results for comparison
    - Generating performance reports and visualizations
    """
    
    def __init__(self, results_dir: str = "./benchmark_results"):
        """
        Initialize benchmark tool
        
        Args:
            results_dir: Directory to store benchmark results
        """
        self.results_dir = results_dir
        os.makedirs(results_dir, exist_ok=True)
        self.results: List[BenchmarkResult] = []
        
    def measure(
        self, 
        test_name: str, 
        operation: str, 
        dataset_size: int, 
        func: Callable, 
        *args, 
        **kwargs
    ) -> tuple:
        """
        Measure performance of a function
        
        Args:
            test_name: Name of the benchmark test
            operation: Type of operation being performed
            dataset_size: Size of the dataset (documents, queries, etc.)
            func: Function to benchmark
            *args, **kwargs: Arguments to pass to the function
            
        Returns:
            Tuple of (function result, benchmark result)
        """
        # Record start time and memory
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
        
        # Execute operation
        result = func(*args, **kwargs)
        
        # Record end time and memory
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / (1024 * 1024)  # MB
        
        # Calculate metrics
        duration = end_time - start_time
        throughput = dataset_size / duration if duration > 0 else 0
        memory_usage = end_memory - start_memory
        
        # Create result
        benchmark_result = BenchmarkResult(
            test_name=test_name,
            operation=operation,
            dataset_size=dataset_size,
            duration_seconds=duration,
            throughput=throughput,
            memory_usage_mb=memory_usage
        )
        
        # Log and store result
        logger.info(f"Benchmark '{test_name}': {duration:.2f}s, {throughput:.2f} ops/s, {memory_usage:.2f} MB")
        self.results.append(benchmark_result)
        
        return result, benchmark_result
           
    def save_results(self, filename: Optional[str] = None) -> str:
        """
        Save benchmark results to JSON file
        
        Args:
            filename: Optional custom filename, defaults to timestamp-based name
            
        Returns:
            Path to the saved file
        """
        if filename is None:
            filename = f"benchmark_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.results_dir, filename)
        
        with open(filepath, 'w') as f:
            json.dump([r.to_dict() for r in self.results], f, indent=2)
        
        logger.info(f"Saved benchmark results to {filepath}")
        return filepath
               
    def generate_report(self, show_plots: bool = True) -> Optional[str]:
        """
        Generate performance report with plots
        
        Args:
            show_plots: Whether to display plots interactively
            
        Returns:
            Path to the saved plot image, or None if plotting is unavailable
        """
        if not self.results:
            logger.warning("No benchmark results available to generate report")
            return "No benchmark results available."
        
        if not PLOTTING_AVAILABLE:
            logger.warning("Matplotlib not available. Cannot generate visual report.")
            return None
            
        # Group by operation
        operations = {}
        for result in self.results:
            if result.operation not in operations:
                operations[result.operation] = []
            operations[result.operation].append(result)
               
        # Create plots
        plt.figure(figsize=(15, 10))
        
        # Plot 1: Duration by operation and dataset size
        plt.subplot(2, 2, 1)
        for op, results in operations.items():
            sizes = [r.dataset_size for r in results]
            durations = [r.duration_seconds for r in results]
            plt.plot(sizes, durations, 'o-', label=op)
        plt.xlabel('Dataset Size')
        plt.ylabel('Duration (seconds)')
        plt.title('Duration by Dataset Size')
        plt.legend()
        plt.grid(True)
        
        # Plot 2: Throughput by operation
        plt.subplot(2, 2, 2)
        op_names = list(operations.keys())
        avg_throughput = [np.mean([r.throughput for r in results]) 
                        for results in operations.values()]
        plt.bar(op_names, avg_throughput)
        plt.xlabel('Operation')
        plt.ylabel('Avg. Throughput (ops/sec)')
        plt.title('Average Throughput by Operation')
        plt.grid(True)
        
        # Plot 3: Memory usage
        plt.subplot(2, 2, 3)
        for op, results in operations.items():
            sizes = [r.dataset_size for r in results]
            memory = [r.memory_usage_mb for r in results]
            plt.plot(sizes, memory, 'o-', label=op)
        plt.xlabel('Dataset Size')
        plt.ylabel('Memory Usage (MB)')
        plt.title('Memory Usage by Dataset Size')
        plt.legend()
        plt.grid(True)
        
        plt.tight_layout()
        
        # Save plot
        plot_path = os.path.join(self.results_dir, 
                               f"benchmark_plots_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png")
        plt.savefig(plot_path)
        logger.info(f"Saved benchmark plots to {plot_path}")
        
        if show_plots:
            plt.show()
            
        return plot_path