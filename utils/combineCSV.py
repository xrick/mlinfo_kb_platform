# utils/combineCSV.py
#!/usr/bin/env python3
"""
combineCSV.py - Combine CSV files into a single file

This script combines all CSV files from the data/raw/EM_New TTL_241104_AllModelsParsed folder
into a single CSV file named all_nbinfo_v3.csv.
"""

import csv
import os
import glob
from pathlib import Path


def combine_csv_files():
    """
    Combine all CSV files from the source directory into a single output file.
    """
    # Define paths
    source_dir = "data/raw/corrected_csv_20250924"
    output_file = "all_nbinfo_v5_20250926.csv"

    # Get current script directory and project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    source_path = project_root / source_dir
    output_path = project_root / output_file

    try:
        # Get all CSV files in sorted order
        csv_pattern = str(source_path / "*.csv")
        csv_files = sorted(glob.glob(csv_pattern))

        if not csv_files:
            print(f"No CSV files found in {source_path}")
            return False

        print(f"Found {len(csv_files)} CSV files to combine")

        # Open output file for writing
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            writer = None
            header_written = False
            rows_written = 0

            for i, csv_file in enumerate(csv_files):
                print(f"Processing {os.path.basename(csv_file)} ({i+1}/{len(csv_files)})")

                try:
                    with open(csv_file, 'r', encoding='utf-8') as infile:
                        reader = csv.reader(infile)

                        # Read header
                        header = next(reader, None)
                        if header is None:
                            print(f"Warning: {csv_file} is empty, skipping")
                            continue

                        # Write header only for the first file
                        if not header_written:
                            writer = csv.writer(outfile)
                            writer.writerow(header)
                            header_written = True

                        # Process data rows
                        for row in reader:
                            if row:  # Skip empty rows
                                writer.writerow(row)
                                rows_written += 1

                except Exception as e:
                    print(f"Error processing {csv_file}: {e}")
                    continue

        print(f"\nSuccessfully combined {len(csv_files)} files")
        print(f"Total data rows written: {rows_written}")
        print(f"Output file: {output_path}")
        return True

    except Exception as e:
        print(f"Error during file combination: {e}")
        return False


def main():
    """Main function to run the CSV combination process."""
    print("Starting CSV file combination...")
    print("=" * 50)

    success = combine_csv_files()

    print("=" * 50)
    if success:
        print("CSV combination completed successfully!")
    else:
        print("CSV combination failed!")

    return success


if __name__ == "__main__":
    main()