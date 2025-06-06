"""
Example of extending the document processor with custom logic.
"""
from core.rag_system.document_processors.document_processor import DocumentProcessor
from config.rag_config import get_config, DocumentProcessorConfig
from langchain_community.document_loaders import PyPDFLoader
import argparse

class CustomDocumentProcessor(DocumentProcessor):
    """Custom document processor with advanced pre-processing"""
    def __init__(self, config):
        super().__init__(config)
        # Add custom initialization here
    
    def _preprocess_text(self, text):
        """Custom text preprocessing logic"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        # Replace common abbreviations
        abbreviations = {
            "e.g.": "for example",
            "i.e.": "that is",
            "etc.": "and so on",
        }
        for abbr, full in abbreviations.items():
            text = text.replace(abbr, full)
        return text
    
    def process_file(self, file_path):
        """Override to add custom processing for specific file types"""
        doc_type = self._get_document_type(file_path)
        if doc_type == "pdf":
            loader = PyPDFLoader(file_path)
            documents = loader.load()
            # Apply custom preprocessing to each page
            for doc in documents:
                doc.page_content = self._preprocess_text(doc.page_content)
            # Add custom metadata
            for i, doc in enumerate(documents):
                doc.metadata["page_number"] = i + 1
                doc.metadata["total_pages"] = len(documents)
            # Use standard chunking
            return self._chunk_documents(documents, file_path)
        else:
            # Use default processing for other file types
            return super().process_file(file_path)

def main():
    parser = argparse.ArgumentParser(description="Custom processor example")
    parser.add_argument("--file", type=str, required=True, help="File to process")
    args = parser.parse_args()
    # Get config and create custom processor
    config = get_config()
    processor_config = DocumentProcessorConfig(chunk_size=800, chunk_overlap=100)
    custom_processor = CustomDocumentProcessor(config=processor_config)
    # Process file
    chunks = custom_processor.process_file(args.file)
    # Display results
    print(f"Processed file: {args.file}")
    print(f"Generated {len(chunks)} chunks")
    for i, chunk in enumerate(chunks[:3]):  # Show first 3 chunks
        print(f"\n--- Chunk {i+1} ---")
        print(f"Content: {chunk.page_content[:150]}...")
        print(f"Metadata: {chunk.metadata}")

if __name__ == "__main__":
    main()
