#!/usr/bin/env python3
"""
Unit tests for FMT Processor
"""
import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Add the parent directory to the path so we can import the FMTProcessor
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.fmt_processor import FMTProcessor

class TestFMTProcessor(unittest.TestCase):
    """Test suite for FMTProcessor class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.fmt_processor = FMTProcessor()
        
        # Load some test templates
        self.fmt_processor.load_template('basic', {
            'id': 'basic',
            'template_text': 'Hello {{target.name}}, I am {{character.name}}.'
        })
        
        self.fmt_processor.load_template('array', {
            'id': 'array',
            'template_text': 'You like {{target.interests[0]}} and {{target.interests[1]}}.'
        })
        
        self.fmt_processor.load_template('nested', {
            'id': 'nested',
            'template_text': 'You are from {{target.location.city}}, {{target.location.country}}.'
        })
        
        self.fmt_processor.load_template('character_specific', {
            'id': 'character_specific',
            'character_id': 'char1',
            'template_text': 'This is a character-specific template for {{character.name}}.'
        })
        
    def test_basic_variable_substitution(self):
        """Test basic variable substitution"""
        variables = {
            'target': {'name': 'Jordan'},
            'character': {'name': 'Alex'}
        }
        
        result = self.fmt_processor.process_template('basic', variables)
        self.assertEqual(result, 'Hello Jordan, I am Alex.')
        
    def test_array_indexing(self):
        """Test array indexing in templates"""
        variables = {
            'target': {'interests': ['photography', 'travel', 'music']}
        }
        
        result = self.fmt_processor.process_template('array', variables)
        self.assertEqual(result, 'You like photography and travel.')
        
    def test_nested_objects(self):
        """Test nested object properties"""
        variables = {
            'target': {
                'location': {
                    'city': 'New York',
                    'country': 'USA'
                }
            }
        }
        
        result = self.fmt_processor.process_template('nested', variables)
        self.assertEqual(result, 'You are from New York, USA.')
        
    def test_missing_variables(self):
        """Test graceful handling of missing variables"""
        variables = {
            'character': {'name': 'Alex'}
            # target is missing
        }
        
        result = self.fmt_processor.process_template('basic', variables)
        self.assertEqual(result, 'Hello {{target.name}}, I am Alex.')
        
    def test_character_template_organization(self):
        """Test that templates are organized by character"""
        # Check that the template was indexed by character_id
        self.assertIn('char1', self.fmt_processor.character_templates)
        self.assertIn('character_specific', self.fmt_processor.character_templates['char1'])
        
    def test_template_not_found(self):
        """Test error handling when template doesn't exist"""
        with self.assertRaises(ValueError):
            self.fmt_processor.process_template('nonexistent', {})
            
    def test_conversation_analysis(self):
        """Test conversation analysis functionality"""
        conversation = [
            {'content': 'Hello there!', 'is_character': True},
            {'content': 'Hi! How are you?', 'is_character': False},
            {'content': 'I am doing well, thank you for asking.', 'is_character': True},
            {'content': 'That\'s great to hear! I\'ve been enjoying photography lately.', 'is_character': False}
        ]
        
        analysis = self.fmt_processor.analyze_conversation(conversation)
        
        # Basic checks on the analysis results
        self.assertEqual(analysis['message_count'], 4)
        self.assertEqual(analysis['target_messages'], 2)
        self.assertEqual(analysis['character_messages'], 2)
        self.assertIn('trust_level', analysis)
        self.assertIn('estimated_sentiment', analysis)
        
    def test_recommend_template(self):
        """Test template recommendation based on conversation"""
        # Add test templates for recommendation
        self.fmt_processor.load_template('introduction', {
            'id': 'introduction',
            'character_id': 'test_char',
            'tags': ['introduction'],
            'step_number': 1,
            'template_text': 'Hello, nice to meet you!'
        })
        
        conversation = [{'content': 'Hello!', 'is_character': False}]
        profile = {'name': 'Test User'}
        
        recommendation = self.fmt_processor.recommend_template(
            'test_char', {'message_count': 1, 'estimated_sentiment': 'neutral'}, profile
        )
        
        # We expect it to recommend the introduction template
        self.assertEqual(recommendation, 'introduction')
        
if __name__ == '__main__':
    unittest.main()
