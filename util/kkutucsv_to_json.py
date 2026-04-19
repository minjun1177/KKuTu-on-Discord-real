'''
Converts a KKuTu CSV file to a JSON file matching the example.json format.
'''
import csv
import json
import sys
import os

def convert_csv_to_json(csv_file_path, json_file_path):
   
    data = {"kkutu_ko": []}
    
    print(f"Reading from: {csv_file_path}")
    try:
        with open(csv_file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            f.seek(0)
            if f.read(1) == '\ufeff':
                f.seek(0)
                reader = csv.DictReader(f, encoding='utf-8-sig')
            else:
                f.seek(0)
                reader = csv.DictReader(f)

            for row in reader:
                mean_text = row.get('mean', '')
                mean_list = [mean_text] if mean_text else []
                
                theme_raw = row.get('theme', '')
                theme_list = []
                if theme_raw:
                    parts = theme_raw.split(',')
                    for p in parts:
                        p = p.strip()
                        if p:
                            try:
                                theme_list.append(int(p))
                            except ValueError:
                                theme_list.append(p)
                
                entry = {
                    "_id": row.get('_id', ''),
                    "type": row.get('type', ''),
                    "mean": mean_list,
                    "hit": row.get('hit', '0'),
                    "flag": row.get('flag', '0'),
                    "theme": theme_list
                }
                data["kkutu_ko"].append(entry)
                
        print(f"Saving to: {json_file_path} (Total items: {len(data['kkutu_ko'])})")
        with open(json_file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent='\t')
            
        print("Success! The conversion is complete.")
        
    except FileNotFoundError:
        print(f"Error: File '{csv_file_path}' not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_files = sorted([f for f in os.listdir('.') if f.startswith('kkutu_ko_') and f.endswith('.csv')], reverse=True)
        if not csv_files:
            print("No 'kkutu_ko_*.csv' files found.")
            csv_file = input("Please enter the CSV filename to convert: ")
        else:
            print("Found the following CSV files (newest first):")
            for idx, name in enumerate(csv_files):
                print(f"[{idx + 1}] {name}")
            
            choice = input(f"Enter number (default is 1): ").strip()
            if not choice:
                csv_file = csv_files[0]
            else:
                try:
                    csv_file = csv_files[int(choice) - 1]
                except (ValueError, IndexError):
                    csv_file = choice

    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} does not exist.")
        sys.exit(1)

    output_json = os.path.splitext(csv_file)[0] + ".json"
    convert_csv_to_json(csv_file, output_json)
