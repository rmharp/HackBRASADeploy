import os

# Get the directory of the current script
script_dir = os.path.dirname(os.path.realpath(__file__))

# Construct the full path to the file
file_path = os.path.join(script_dir, '3.5-queries.txt')

# Initialize counters
total_lines = 0
correct_lines = 0

# Read the file and count lines
try:
    with open(file_path, 'r') as file:
        for line in file:
            total_lines += 1
            if not line.rstrip().endswith(('X', 'O')):  # Line is correct if it doesn't end with 'X' or 'O'
                correct_lines += 1

    # Calculate the percentage of correct queries
    percentage_correct = (correct_lines / total_lines) * 100 if total_lines > 0 else 0

    print(total_lines, correct_lines, percentage_correct)

except FileNotFoundError:
    print(f"File not found: {file_path}")