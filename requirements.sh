#!/bin/bash
# Define array of directories to exclude
exclude_dirs=("__pycache__" ".asset_space" ".logs" ".pytest_cache" ".vscode" ".work_space" "domains_tests" "Wav2Lip" "BasicSR" "GFPGAN")

# Build find command exclusion arguments
find_exclude_args=()
for dir in "${exclude_dirs[@]}"; do
    find_exclude_args+=( "-o" "-path" "./$dir" "-o" "-path" "./$dir/*" )
done

# Use find command to locate all .py files excluding specified directories and test files
if [ ${#find_exclude_args[@]} -gt 0 ]; then
    # Remove the first "-o" from the arguments
    find_exclude_args=("${find_exclude_args[@]:1}")
    find . -name "*.py" \( "${find_exclude_args[@]}" \) -prune -o -type f -name "*.py" ! -name "*test*" -print > files_to_scan.txt
else
    find . -name "*.py" -type f ! -name "*test*" -print > files_to_scan.txt
fi

# Generate requirements.txt using pipreqs with the filtered file list, suppressing warnings
pipreqs --ignore="dummy_value" --encoding=utf-8 --savepath requirements.txt < files_to_scan.txt

# Append gunicorn==23.0.0 to requirements.txt
echo "gunicorn==23.0.0" >> requirements.txt

# Clean up temporary file
rm files_to_scan.txt

# Export conda environment to yaml file 
conda env export --no-builds > environment.yml

echo "Requirements generated in requirements.txt, excluding specified directories and test files."
echo "Added gunicorn==23.0.0 to requirements.txt"。