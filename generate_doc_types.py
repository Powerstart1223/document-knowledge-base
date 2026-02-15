"""
Generate comprehensive document type definitions using OpenAI API.
"""
import os
from openai import OpenAI
from dotenv import load_dotenv
import json

load_dotenv()

client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

prompt = '''You are a legal document expert. Generate a comprehensive list of 25-30 common corporate and legal document types that professionals commonly need.

For EACH document type, provide:
1. A clear, professional name/label
2. A 1-2 sentence description
3. An appropriate emoji icon
4. A category (Corporate & Business, Employment & HR, Real Estate & Property, Intellectual Property, Litigation & Court, Financial & Investment, or General/Other)
5. 8-15 required fields with complete details

For each field, include:
- key (snake_case identifier)
- label (human-readable label)
- type (text, textarea, date, number, or select)
- placeholder (example value)
- help (brief tooltip explanation)
- section (group name like Parties, Terms, Financial, Legal Provisions, etc.)

Exclude these types as they already exist:
- Independent Contractor Agreement
- NDA / Confidentiality Agreement
- Employment Agreement
- Operating Agreement / LLC
- Letter / Correspondence
- Contract / Agreement (general)
- Legal Memorandum
- Legal Brief
- Corporate Filing

Return ONLY a valid JSON array. Each object should have this structure:
{
  "name": "Document Name",
  "description": "Brief description",
  "icon": "📄",
  "category": "Corporate & Business",
  "fields": [
    {
      "key": "field_name",
      "label": "Field Label",
      "type": "text",
      "placeholder": "Example value",
      "help": "Helpful explanation",
      "section": "Parties"
    }
  ]
}

Focus on commonly used document types across various industries and legal needs.'''

try:
    response = client.chat.completions.create(
        model='gpt-4o-mini',
        messages=[
            {'role': 'system', 'content': 'You are a legal document expert. Return only valid JSON.'},
            {'role': 'user', 'content': prompt}
        ],
        temperature=0.3,
        max_tokens=16000
    )

    output = response.choices[0].message.content

    # Try to extract JSON if wrapped in markdown
    if '```json' in output:
        start = output.find('```json') + 7
        end = output.find('```', start)
        output = output[start:end].strip()
    elif '```' in output:
        start = output.find('```') + 3
        end = output.find('```', start)
        output = output[start:end].strip()

    # Validate JSON
    data = json.loads(output)

    # Write to file
    with open('document_types_generated.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"✓ Successfully generated {len(data)} document types")
    print(json.dumps(data, indent=2, ensure_ascii=False))

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
