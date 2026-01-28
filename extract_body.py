#!/usr/bin/env python3
"""
Script to extract the 'body' field from Payload in JSONL files.
Parses each entry, extracts the body from the Payload JSON string, and writes to output file.
"""

import json
import sys
import os


def extract_body_from_jsonl(input_file, output_file=None):
    """
    Extract the 'body' field from Payload in each JSONL entry.
    
    Args:
        input_file: Path to input JSONL file
        output_file: Path to output JSONL file (default: input_file with '_body' suffix)
    """
    if output_file is None:
        base_name = os.path.splitext(input_file)[0]
        output_file = f"{base_name}_body.jsonl"
    
    output_lines = []
    entries_processed = 0
    
    # Read the entire file
    with open(input_file, 'r') as f:
        content = f.read()
    
    # Parse multi-line JSON entries
    entries = []
    current_entry = ""
    brace_count = 0
    
    for line in content.split('\n'):
        if line.strip():
            current_entry += line + '\n'
            brace_count += line.count('{') - line.count('}')
            if brace_count == 0 and current_entry.strip():
                entries.append(current_entry.strip())
                current_entry = ""
    
    if current_entry.strip():
        entries.append(current_entry.strip())
    
    # Process each entry
    for entry_str in entries:
        if not entry_str:
            continue
        
        try:
            # Parse the outer JSON
            entry = json.loads(entry_str)
            
            # Parse the Payload JSON string
            payload_str = entry.get('Payload', '{}')
            payload = json.loads(payload_str)
            
            # Extract the body
            body = payload.get('body', {})
            
            # Write body as JSON line
            output_lines.append(json.dumps(body))
            entries_processed += 1
            
        except json.JSONDecodeError as e:
            print(f"Error parsing entry: {e}", file=sys.stderr)
            continue
        except Exception as e:
            print(f"Error processing entry: {e}", file=sys.stderr)
            continue
    
    # Write output file
    with open(output_file, 'w') as f:
        for line in output_lines:
            f.write(line + '\n')
    
    print(f"Processed {entries_processed} entries")
    print(f"Output written to: {output_file}")
    return output_file


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python extract_body.py <input_file> [output_file]")
        print("Example: python extract_body.py aws-ap-south.jsonl")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found", file=sys.stderr)
        sys.exit(1)
    
    extract_body_from_jsonl(input_file, output_file)

