"""
Script to update all card border-radius values in the templates to match the navbar.
"""
import os
import re

# Define the templates directory
TEMPLATES_DIR = 'greenbyte/templates'

# Define the new border-radius value
NEW_RADIUS = '1.5rem'

# Regular expressions to match different border-radius patterns
PATTERNS = [
    # Match border-radius: Xrem !important;
    (r'border-radius:\s*[\d\.]+rem\s*!important;', f'border-radius: {NEW_RADIUS} !important;'),
    
    # Match border-radius: Xrem;
    (r'border-radius:\s*[\d\.]+rem;', f'border-radius: {NEW_RADIUS};'),
    
    # Match border-radius: 0.Xrem !important;
    (r'border-radius:\s*0\.[\d]+rem\s*!important;', f'border-radius: {NEW_RADIUS} !important;'),
    
    # Match border-radius: 0.Xrem;
    (r'border-radius:\s*0\.[\d]+rem;', f'border-radius: {NEW_RADIUS};'),
    
    # Match border-radius: Xpx !important;
    (r'border-radius:\s*[\d\.]+px\s*!important;', f'border-radius: {NEW_RADIUS} !important;'),
    
    # Match border-radius: Xpx;
    (r'border-radius:\s*[\d\.]+px;', f'border-radius: {NEW_RADIUS};'),
    
    # Match style="... border-radius: Xrem !important; ..."
    (r'(style="[^"]*border-radius:\s*)[\d\.]+rem(\s*!important;[^"]*")', r'\1' + NEW_RADIUS + r'\2'),
    
    # Match style="... border-radius: Xrem; ..."
    (r'(style="[^"]*border-radius:\s*)[\d\.]+rem(;[^"]*")', r'\1' + NEW_RADIUS + r'\2'),
    
    # Match style="... border-radius: 0.Xrem !important; ..."
    (r'(style="[^"]*border-radius:\s*)0\.[\d]+rem(\s*!important;[^"]*")', r'\1' + NEW_RADIUS + r'\2'),
    
    # Match style="... border-radius: 0.Xrem; ..."
    (r'(style="[^"]*border-radius:\s*)0\.[\d]+rem(;[^"]*")', r'\1' + NEW_RADIUS + r'\2'),
]

# Special case for specific elements that should keep their original border-radius
EXCEPTIONS = [
    'rounded-circle',  # Profile pictures and circular elements
    'border-radius: 50%',  # Another way to specify circular elements
    'border-radius: 0.5rem 0 0 0.5rem',  # Left side of search box
    'border-radius: 0 0.5rem 0.5rem 0',  # Right side of search box
]

def should_skip_line(line):
    """Check if the line contains any exceptions that should be skipped."""
    return any(exception in line for exception in EXCEPTIONS)

def update_template_file(file_path):
    """Update border-radius values in a single template file."""
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Keep track of original content to check if changes were made
    original_content = content
    
    # Apply each pattern
    for pattern, replacement in PATTERNS:
        # Split content into lines
        lines = content.split('\n')
        updated_lines = []
        
        for line in lines:
            # Skip lines with exceptions
            if should_skip_line(line):
                updated_lines.append(line)
                continue
            
            # Apply the pattern replacement
            updated_line = re.sub(pattern, replacement, line)
            updated_lines.append(updated_line)
        
        # Join lines back into content
        content = '\n'.join(updated_lines)
    
    # Check if content was modified
    if content != original_content:
        with open(file_path, 'w') as file:
            file.write(content)
        return True
    
    return False

def update_all_templates():
    """Update border-radius values in all template files."""
    modified_files = []
    
    # Walk through the templates directory
    for root, _, files in os.walk(TEMPLATES_DIR):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                if update_template_file(file_path):
                    modified_files.append(file_path)
    
    return modified_files

if __name__ == '__main__':
    modified_files = update_all_templates()
    
    if modified_files:
        print(f"Updated {len(modified_files)} template files:")
        for file in modified_files:
            print(f"  - {file}")
    else:
        print("No files were modified.")
