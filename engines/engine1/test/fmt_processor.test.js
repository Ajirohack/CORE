// fmt_processor.test.js
/**
 * Tests for FMT processor functionality
 */
import { processTemplate } from '../src/fmt_processor';

describe('FMT Processor', () => {
    // Test basic template processing
    test('should replace variables in a template', () => {
        const template = {
            id: 'test-template',
            template_text: 'Hello {{target.name}}, I am {{character.name}}. How are you?'
        };

        const variables = {
            target: { name: 'John' },
            character: { name: 'AI Assistant' }
        };

        const processed = processTemplate(template, variables);
        expect(processed).toBe('Hello John, I am AI Assistant. How are you?');
    });

    // Test nested variable objects
    test('should handle nested object variables', () => {
        const template = {
            id: 'test-template',
            template_text: 'You mentioned that you are a {{target.profession}} in {{target.location.city}}.'
        };

        const variables = {
            target: {
                profession: 'doctor',
                location: {
                    city: 'New York',
                    country: 'USA'
                }
            }
        };

        const processed = processTemplate(template, variables);
        expect(processed).toBe('You mentioned that you are a doctor in New York.');
    });

    // Test missing variables
    test('should handle missing variables gracefully', () => {
        const template = {
            id: 'test-template',
            template_text: 'Hello {{target.name}}, welcome to {{platform.name}}!'
        };

        const variables = {
            target: { name: 'John' }
            // platform is missing
        };

        const processed = processTemplate(template, variables);
        expect(processed).toBe('Hello John, welcome to {{platform.name}}!');
    });

    // Test array variables
    test('should handle array variables', () => {
        const template = {
            id: 'test-template',
            template_text: 'You mentioned your interests include: {{target.interests}}'
        };

        const variables = {
            target: {
                interests: ['reading', 'travel', 'cooking']
            }
        };

        const processed = processTemplate(template, variables);
        expect(processed).toBe('You mentioned your interests include: reading,travel,cooking');
    });
});

/**
 * Process a template with variables
 * @param {Object} template - Template object
 * @param {Object} variables - Variables to substitute
 * @returns {string} Processed template text
 */
function processTemplate(template, variables) {
    let processedText = template.template_text;

    // Replace variables in the format {{variable}} or {{object.property}}
    const variableRegex = /\{\{([^}]+)\}\}/g;

    return processedText.replace(variableRegex, (match, path) => {
        const parts = path.trim().split('.');
        let value = variables;

        // Navigate through the object path
        for (const part of parts) {
            if (value && Object.prototype.hasOwnProperty.call(value, part)) {
                value = value[part];
            } else {
                // If path doesn't exist, return the original placeholder
                return match;
            }
        }

        return value !== undefined ? value : match;
    });
}
