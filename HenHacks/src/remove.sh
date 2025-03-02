!/bin/bash
# Define the output directory
OUTPUT_DIR="output"
# Check if the directory exists
if [ -d "$OUTPUT_DIR" ]; then
    echo "Removing all files in $OUTPUT_DIR..."
    rm -f "$OUTPUT_DIR"/*
    echo "Cleanup complete."
else
    echo "Error: Directory $OUTPUT_DIR does not exist."
fi