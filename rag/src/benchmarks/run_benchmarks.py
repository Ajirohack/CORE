"""
RAG System Benchmark Runner

This script runs performance benchmarks for the RAG system, including document processing,
search, and (optionally) answer generation. Results are saved and a report is generated.
"""

import argparse
import os
import random
import string
from core.rag_system.utils.benchmark import RAGBenchmark
from core.rag_system.rag_system import RAGSystem
from config.rag_config import get_config

def generate_random_text(num_words: int, avg_word_length: int = 5) -> str:
    """Generate random text with specified number of words"""
    result = []
    for _ in range(num_words):
        word_len = max(1, int(random.gauss(avg_word_length, 2)))
        word = ''.join(random.choice(string.ascii_lowercase) for _ in range(word_len))
        result.append(word)
    return ' '.join(result)

def prepare_test_data(num_docs: int, words_per_doc: int, output_dir: str):
    """Prepare test data for benchmarking"""
    os.makedirs(output_dir, exist_ok=True)
    for i in range(num_docs):
        content = generate_random_text(words_per_doc)
        with open(os.path.join(output_dir, f"doc_{i}.txt"), 'w') as f:
            f.write(content)
    return output_dir

def run_benchmarks():
    parser = argparse.ArgumentParser(description="Run RAG system benchmarks")
    parser.add_argument("--num_docs", type=int, default=100, help="Number of test documents")
    parser.add_argument("--words_per_doc", type=int, default=200, help="Words per document")
    parser.add_argument("--output_dir", type=str, default="./benchmark_data", help="Directory for test data")
    parser.add_argument("--results_dir", type=str, default="./benchmark_results", help="Directory for results")
    args = parser.parse_args()

    # Initialize benchmark
    benchmark = RAGBenchmark(results_dir=args.results_dir)

    # Prepare test data
    data_dir = prepare_test_data(args.num_docs, args.words_per_doc, args.output_dir)

    # Initialize RAG system with in-memory vector store for faster testing
    config = get_config("test")
    config.vector_store.store_type = "in_memory"
    rag = RAGSystem(config=config)

    # Benchmark 1: Document processing
    _, result = benchmark.measure(
        "document_processing", 
        "process_documents", 
        args.num_docs,
        rag.process_and_add_directory,
        data_dir
    )
    print(f"Document processing: {result.duration_seconds:.2f} seconds")

    # Benchmark 2: Search operations with varying k values
    for k in [1, 5, 10, 20]:
        query = "test query example"
        _, result = benchmark.measure(
            f"search_k{k}",
            "search",
            k,
            rag.search,
            query,
            k=k
        )
        print(f"Search (k={k}): {result.duration_seconds:.2f} seconds")

    # Save and generate report
    benchmark.save_results()
    plot_path = benchmark.generate_report()
    print(f"Benchmark report saved to: {plot_path}")

if __name__ == "__main__":
    run_benchmarks()
