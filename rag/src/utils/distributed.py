"""
Distributed document processing utility for the RAG system.
"""
import multiprocessing
import os
import logging
from typing import List, Dict, Any, Optional
from functools import partial

logger = logging.getLogger(__name__)

def process_file_worker(file_path: str, config: Dict[str, Any]):
    """Worker function for multiprocessing document processing."""
    from core.rag_system.document_processors.document_processor import DocumentProcessor
    processor = DocumentProcessor(config=config)
    try:
        return processor.process_file(file_path)
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {str(e)}")
        return []

class DistributedDocumentProcessor:
    """Distributed document processing using multiprocessing."""
    def __init__(self, config, num_workers=None):
        self.config = config
        self.num_workers = num_workers or multiprocessing.cpu_count()
    def process_directory(self, directory_path: str) -> List:
        all_files = []
        for root, _, files in os.walk(directory_path):
            for file in files:
                all_files.append(os.path.join(root, file))
        logger.info(f"Found {len(all_files)} files to process with {self.num_workers} workers")
        worker_func = partial(process_file_worker, config=self.config)
        with multiprocessing.Pool(processes=self.num_workers) as pool:
            results = pool.map(worker_func, all_files)
        all_documents = []
        for doc_list in results:
            if doc_list:
                all_documents.extend(doc_list)
        logger.info(f"Processed {len(all_documents)} documents from {len(all_files)} files")
        return all_documents
