### script to check only the end of each line for 'X' or 'O'

# Initialize counters
total_lines = 0
correct_lines = 0
file_path = "./queries.txt"

# Read the file and count lines
with open(file_path, 'r') as file:
    for line in file:
        total_lines += 1
        if not line.rstrip().endswith(('X', 'O')):  # Line is correct if it doesn't end with 'X' or 'O'
            correct_lines += 1

# Calculate the percentage of correct queries
percentage_correct = (correct_lines / total_lines) * 100 if total_lines > 0 else 0

print(total_lines, correct_lines, percentage_correct)