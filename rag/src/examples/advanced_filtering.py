"""
Example of advanced metadata filtering with the RAG system.
"""
from core.rag_system.rag_system import RAGSystem
from config.rag_config import get_config
import argparse
import datetime

def main():
    parser = argparse.ArgumentParser(description="Advanced filtering example")
    parser.add_argument("--query", type=str, required=True, help="Search query")
    parser.add_argument("--source", type=str, help="Filter by source")
    parser.add_argument("--date_after", type=str, help="Filter by date after (YYYY-MM-DD)")
    parser.add_argument("--date_before", type=str, help="Filter by date before (YYYY-MM-DD)")
    parser.add_argument("--file_type", type=str, help="Filter by file type")
    args = parser.parse_args()

    # Initialize RAG system
    config = get_config()
    rag = RAGSystem(config=config)
    
    # Build filter
    filter_dict = {}
    
    if args.source:
        filter_dict["source"] = {"$eq": args.source}
        
    if args.file_type:
        filter_dict["file_type"] = {"$eq": args.file_type}
        
    # Date filters
    if args.date_after or args.date_before:
        filter_dict["created_at"] = {}
        
    if args.date_after:
        date_after = datetime.datetime.strptime(args.date_after, "%Y-%m-%d").isoformat()
        filter_dict["created_at"]["$gte"] = date_after
        
    if args.date_before:
        date_before = datetime.datetime.strptime(args.date_before, "%Y-%m-%d").isoformat()
        filter_dict["created_at"]["$lte"] = date_before
        
    # Perform search with filter
    results = rag.search(args.query, k=5, filter=filter_dict)
    
    # Display results
    print(f"Search query: {args.query}")
    print(f"Applied filters: {filter_dict}")
    print(f"Found {len(results)} matching documents:")
    
    for i, doc in enumerate(results):
        print(f"\n--- Result {i+1} ---")
        print(f"Content: {doc['content'][:150]}...")
        print(f"Source: {doc['metadata']['source']}")
        print(f"Created: {doc['metadata'].get('created_at', 'unknown')}")
        print(f"Similarity: {doc.get('score', 'N/A')}")

if __name__ == "__main__":
    main()
