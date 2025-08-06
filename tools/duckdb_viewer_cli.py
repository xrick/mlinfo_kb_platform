import re
import argparse
import pandas as pd
from tabulate import tabulate
import sys

def parse_spec_file(file_path):
    """
    Parses a semi-structured text file containing product specifications.

    Args:
        file_path (str): The path to the spec file.

    Returns:
        dict: A nested dictionary where keys are model names and values are
              dictionaries of their specifications.
              e.g., {'MODEL_A': {'CPU': 'Intel', 'RAM': '16GB'}}
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"錯誤：找不到檔案 '{file_path}'。請檢查檔案路徑是否正確。")
        sys.exit(1)
    except Exception as e:
        print(f"讀取檔案時發生錯誤：{e}")
        sys.exit(1)

    # Regex to identify model names which act as delimiters for sections.
    # This pattern looks for capitalized words followed by numbers and an optional suffix, ending with a colon.
    # e.g., "AHP819:", "ARB819-S:", "AG958V v1.0"
    # We also treat lines with many model names as a potential source of models.
    model_delimiter_pattern = re.compile(r'\b([A-Z]{2,4}[0-9]{3,4}(?:[-_][A-Z0-9_]+)?(?:\s+v[0-9.]+)?:)')
    
    # Pre-scan for all possible model names to ensure we catch them all
    all_models = set(m.strip(':') for m in model_delimiter_pattern.findall(content))

    # Split the content by these delimiters. The result is a list like
    # ['intro text', 'MODEL_A:', 'specs for A', 'MODEL_B:', 'specs for B', ...]
    parts = model_delimiter_pattern.split(content)
    
    data = {}
    current_model = None

    # We iterate through the split parts, two at a time (delimiter, content).
    for i in range(1, len(parts), 2):
        model_name = parts[i].strip(': ')
        model_content = parts[i+1]
        
        if model_name not in data:
            data[model_name] = {}

        # Regex patterns to find key-value pairs. Due to the messy format,
        # we use several patterns to capture as much as possible.
        # Pattern 1: Lines starting with "- Key: Value"
        spec_pattern_1 = re.compile(r'-\s*([^:]+?)\s*:\s*(.+)')
        # Pattern 2: Lines with "Key Value" structure for things like CPU models
        spec_pattern_2 = re.compile(r'\b(Ryzen\s*[0-9PRO\s]+[A-Z0-9]+)\s*\((.+)\)')
        # Pattern 3: Simple "Key: Value" on its own line
        spec_pattern_3 = re.compile(r'^([A-Za-z\s/&]+):\s*(.+)', re.MULTILINE)

        for line in model_content.splitlines():
            line = line.strip()
            if not line:
                continue
            
            # Try patterns in order
            match = spec_pattern_1.match(line)
            if not match:
                match = spec_pattern_2.match(line)
            if not match:
                 match = spec_pattern_3.match(line)

            if match:
                key = match.group(1).strip()
                value = match.group(2).strip()
                
                # Avoid adding nonsensical keys
                if len(key) > 50 or 'nodata' in key.lower():
                    continue

                if key not in data[model_name]:
                    data[model_name][key] = value

    # Clean up empty models
    data = {k: v for k, v in data.items() if v}
    return data

def main():
    """
    Main function to run the CLI.
    """
    # Note for the user about installing dependencies
    try:
        import pandas
        import tabulate
    except ImportError:
        print("請先安裝必要的函式庫：pip install pandas openpyxl tabulate")
        sys.exit(1)

    parser = argparse.ArgumentParser(
        description="一個用來解析、顯示和匯出產品規格資料的命令列工具。",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("file_path", help="要解析的 sales_specs.db 檔案路徑。")
    
    subparsers = parser.add_subparsers(dest="command", required=True, help="可用的命令")

    # Info command
    info_parser = subparsers.add_parser("info", help="顯示檔案中所有偵測到的產品型號。")

    # Show command
    show_parser = subparsers.add_parser("show", help="以表格格式顯示產品規格。")
    show_parser.add_argument("model", nargs="?", default=None, help="要顯示的特定產品型號 (可選)。")

    # Export command
    export_parser = subparsers.add_parser("export", help="將所有規格資料匯出成 CSV 或 XLSX 檔案。")
    export_parser.add_argument("--format", choices=["csv", "xlsx"], required=True, help="匯出的檔案格式。")
    export_parser.add_argument("--output", required=True, help="匯出的檔案路徑與檔名 (例如: 'output.xlsx')。")

    args = parser.parse_args()

    # --- Command Logic ---
    data = parse_spec_file(args.file_path)

    if not data:
        print("無法從檔案中解析出任何有效的資料。請檢查檔案內容和格式。")
        return

    if args.command == "info":
        print("在檔案中偵測到的產品型號：")
        for model in sorted(data.keys()):
            print(f"- {model}")

    elif args.command == "show":
        models_to_show = [args.model] if args.model else sorted(data.keys())
        for model in models_to_show:
            if model in data:
                print(f"\n--- {model} 規格 ---")
                specs = data[model]
                if specs:
                    # Prepare data for tabulate: list of [key, value]
                    table_data = [[k, v] for k, v in specs.items()]
                    print(tabulate(table_data, headers=["Specification", "Value"], tablefmt="grid"))
                else:
                    print("找不到此型號的詳細規格。")
            else:
                print(f"\n錯誤：找不到型號 '{model}'。")
    
    elif args.command == "export":
        output_file = args.output
        if args.format == "csv":
            # Flatten data for CSV: Model, Specification, Value
            csv_data = []
            for model, specs in data.items():
                for key, value in specs.items():
                    csv_data.append({"Model": model, "Specification": key, "Value": value})
            df = pd.DataFrame(csv_data)
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            print(f"成功將所有資料匯出至 CSV 檔案：{output_file}")

        elif args.format == "xlsx":
            with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
                for model, specs in data.items():
                    # Sanitize model name for sheet name (max 31 chars, no invalid chars)
                    sheet_name = re.sub(r'[\\/*?:\[\]]', '_', model)[:31]
                    df = pd.DataFrame(list(specs.items()), columns=["Specification", "Value"])
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
            print(f"成功將所有資料匯出至 XLSX 檔案：{output_file}")


if __name__ == "__main__":
    main()