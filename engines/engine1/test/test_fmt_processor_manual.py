#!/usr/bin/env python3
"""
Manual test script for FMT Processor functionality
"""
import sys
import os

# Add the parent directory to the path so we can import the FMTProcessor
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.fmt_processor import FMTProcessor

def test_simple_template():
    fmt = FMTProcessor()
    
    # Create a test template
    template = {
        'id': 'test',
        'template_text': 'Hello {{target.name}}, I am {{character.name}}. You mentioned your interest in {{target.interests[0]}}. I find that fascinating!'
    }
    
    # Load the template
    fmt.load_template('test', template)
    
    # Define variables
    variables = {
        'character': {'name': 'Alex'},
        'target': {'name': 'Jordan', 'interests': ['photography', 'travel']}
    }
    
    # Process the template
    result = fmt.process_template('test', variables)
    print("\n--- Template Processing Test ---")
    print("Original template:")
    print(template['template_text'])
    print("\nProcessed template:")
    print(result)
    print("\nExpected result:")
    print("Hello Jordan, I am Alex. You mentioned your interest in photography. I find that fascinating!")
    
    assert "Hello Jordan, I am Alex" in result, "Name replacement failed"
    assert "photography" in result, "Interest replacement failed"
    
    print("\nTest passed! ✅")

if __name__ == "__main__":
    test_simple_template()
