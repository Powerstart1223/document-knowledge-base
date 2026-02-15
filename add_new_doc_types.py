"""
Script to add new document types to document_generator.py
"""
import json

# Load the generated document types
with open('document_types_generated.json', 'r', encoding='utf-8') as f:
    new_types = json.load(f)

# Convert to the format needed for EXTENDED_DOCUMENT_TYPES
extended_types_additions = {}

for doc_type in new_types:
    name = doc_type['name']
    fields = doc_type['fields']

    # Convert fields to the format needed
    converted_fields = []
    for field in fields:
        converted_field = {
            'key': field['key'],
            'label': field['label'],
            'type': field['type'],
            'placeholder': field['placeholder'],
            'help': field['help']
        }
        converted_fields.append(converted_field)

    extended_types_additions[name] = converted_fields

# Print the Python code
print('# Add to EXTENDED_DOCUMENT_TYPES dictionary in document_generator.py:')
print()
for name, fields in extended_types_additions.items():
    print(f'            "{name}": [')
    for field in fields:
        print(f'                {field},')
    print('            ],')
