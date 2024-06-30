import os
import re

def replace_slashes_in_line(line):
    # Pattern to match content within quotes (single or double)
    pattern = r'(\'[^\']*\'|"[^"]*")'
    
    def replace_slash(match):
        # Replace forward slashes with double backslashes within the matched quotes
        return match.group(0).replace('/', '\\\\')
    
    # Replace slashes only within quoted strings
    return re.sub(pattern, replace_slash, line)

def process_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        lines = file.readlines()

    modified = False
    new_lines = []
    for line in lines:
        new_line = replace_slashes_in_line(line)
        if new_line != line:
            modified = True
        new_lines.append(new_line)

    if modified:
        print(f"Modifying: {file_path}")
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(new_lines)
    else:
        print(f"No changes needed in: {file_path}")

def process_directory(directory):
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                process_file(file_path)

# Specify the directory containing your Python files
directory = 'z'
process_directory(directory)





# #repalce .\\'s with \\'s but avoiud ..\\s
# (?<!\.)\.(?=\\)
# \\
#     read_pickle(root_dir + '\\' + f'
# to_pickle(root_dir + '\\' + f'