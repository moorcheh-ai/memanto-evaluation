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

def generate_longmem_report(filepath):
    if not filepath:
        return {"error": "No LongMem results found."}
    
    data = load_results(filepath)
    df = pd.DataFrame(data)
    
    filename = os.path.basename(filepath)
    
    overall_acc = df["score"].mean()
    
    report = {
        "report_type": "LongMem Evaluation",
        "generated_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        "source_file": filename,
        "total_samples": len(df),
        "overall_accuracy": round(float(overall_acc), 4),
        "score_distribution": {},
        "accuracy_by_question_type": {}
    }
    
    if "score" in df.columns:
        score_counts = df["score"].value_counts().sort_index()
        for score, count in score_counts.items():
            report["score_distribution"][str(score)] = int(count)
    
    if "question_type" in df.columns:
        summary = df.groupby("question_type")["score"].agg(["mean", "count", "sum"]).reset_index()
        summary = summary.sort_values("mean", ascending=False)
        for _, row in summary.iterrows():
            qtype = str(row['question_type'])
            
            count = int(row['count'])
            correct = int(row['sum'])
            wrong = count - correct
            
            report["accuracy_by_question_type"][qtype] = {
                "accuracy": round(float(row['mean']), 4),
                "count": count,
                "correct": correct,
                "wrong": wrong
            }
            
    return report

def main():
    parser = argparse.ArgumentParser(description="Generate LongMem Evaluation Report")
    parser.add_argument("--output", type=str, default=None, help="Output file path (e.g., longmem_report.json)")
    parser.add_argument("--file", type=str, default=None, help="Specific longmem results file")
    args = parser.parse_args()
    
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results", "baselines")
    
    input_file = args.file if args.file else get_latest_result(results_dir, "longmem_")
    
    report_content = generate_longmem_report(input_file)
    output_file = args.output if args.output else os.path.join(results_dir, "longmem_report.json")
    
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report_content, f, indent=4)
        
    print(f"Report successfully saved to {output_file}")
    print(json.dumps(report_content, indent=4))

if __name__ == "__main__":
    main()
