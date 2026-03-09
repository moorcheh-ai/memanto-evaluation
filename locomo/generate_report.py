import os
import json
import glob
import pandas as pd
import argparse
from datetime import datetime

def get_latest_result(directory, prefix):
    pattern = os.path.join(directory, f"{prefix}*.json")
    files = glob.glob(pattern)
    if not files:
        return None
    files = [f for f in files if not os.path.basename(f).endswith("_report.json")]
    if not files:
        return None
    return max(files, key=os.path.getctime)

def load_results(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def generate_locomo_report(filepath):
    if not filepath:
        return {"error": "No Locomo results found."}
    
    data = load_results(filepath)
    df = pd.DataFrame(data)
    
    filename = os.path.basename(filepath)
    
    overall_acc = df["score"].mean()
    
    report = {
        "report_type": "Locomo Evaluation",
        "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "source_file": filename,
        "total_samples": len(df),
        "overall_accuracy": round(float(overall_acc), 4),
        "accuracy_by_category": {},
        "accuracy_by_sample": {}
    }
    
    category_map = {
        1: "Single-Hop", 1.0: "Single-Hop", "1": "Single-Hop", "1.0": "Single-Hop",
        2: "Temporal", 2.0: "Temporal", "2": "Temporal", "2.0": "Temporal",
        3: "Multi-Hop", 3.0: "Multi-Hop", "3": "Multi-Hop", "3.0": "Multi-Hop",
        4: "Open Domain", 4.0: "Open Domain", "4": "Open Domain", "4.0": "Open Domain"
    }
    
    if "category" in df.columns:
        summary = df.groupby("category")["score"].agg(["mean", "count", "sum"]).reset_index()
        summary = summary.sort_values("category")
        for _, row in summary.iterrows():
            raw_cat = row['category']
            cat = category_map.get(raw_cat, str(raw_cat))
            
            count = int(row['count'])
            correct = int(row['sum'])
            wrong = count - correct
            
            report["accuracy_by_category"][cat] = {
                "accuracy": round(float(row['mean']), 4),
                "count": count,
                "correct": correct,
                "wrong": wrong
            }
            
    if "sample_id" in df.columns:
        sample_summary = df.groupby("sample_id")["score"].agg(["mean", "count", "sum"]).reset_index()
        sample_summary = sample_summary.sort_values("mean", ascending=False)
        for _, row in sample_summary.iterrows():
            sample_id = str(row['sample_id'])
            count = int(row['count'])
            correct = int(row['sum'])
            wrong = count - correct
            
            report["accuracy_by_sample"][sample_id] = {
                "accuracy": round(float(row['mean']), 4),
                "count": count,
                "correct": correct,
                "wrong": wrong
            }
            
    return report

def main():
    parser = argparse.ArgumentParser(description="Generate Locomo Evaluation Report")
    parser.add_argument("--output", type=str, default=None, help="Output file path (e.g., locomo_report.json)")
    parser.add_argument("--file", type=str, default=None, help="Specific locomo results file")
    args = parser.parse_args()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results", "baselines")
    
    input_file = args.file if args.file else get_latest_result(results_dir, "locomo_results_")
    
    report_content = generate_locomo_report(input_file)
    output_file = args.output if args.output else os.path.join(results_dir, "locomo_report.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report_content, f, indent=4)
        
    print(f"Report successfully saved to {output_file}")
    print(json.dumps(report_content, indent=4))

if __name__ == "__main__":
    main()
