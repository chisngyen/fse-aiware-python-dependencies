import os
import glob

def analyze():
    log_dir = r"D:\fse-aiware-python-dependencies\output\run_1\logs"
    success_files = []
    for log_path in glob.glob(os.path.join(log_dir, "*.log")):
        with open(log_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "Result: SUCCESS" in content:
                success_files.append(content)
    
    total_success = len(success_files)
    print(f"Total Success: {total_success}")
    
    stats = {
        "Oracle/Session Memory": 0,
        "Shortcut/Self-Evolving": 0,
        "Python 2 Heuristic (No LLM)": 0,
        "LLM Invoked": 0,
        "Runtime Pass (System/Local)": 0,
        "Other Deterministic": 0
    }
    
    for content in success_files:
        if "Oracle SUCCESS!" in content or "Oracle RUNTIME PASS" in content:
            stats["Oracle/Session Memory"] += 1
        elif "SHORTCUT SUCCESS!" in content or "SHORTCUT RUNTIME PASS" in content:
            stats["Shortcut/Self-Evolving"] += 1
        else:
            # Check what happened in the main pipeline
            is_runtime_pass = "RUNTIME PASS" in content
            called_llm = "Calling LLM evaluate_file" in content
            py2_skip = "Skipping LLM: Python 2 code" in content
            
            if is_runtime_pass:
                stats["Runtime Pass (System/Local)"] += 1
                if called_llm:
                    stats["LLM Invoked"] += 1 # technically called LLM but passed via runtime pass rules
            elif py2_skip:
                stats["Python 2 Heuristic (No LLM)"] += 1
            elif called_llm:
                stats["LLM Invoked"] += 1
            else:
                stats["Other Deterministic"] += 1

    print("\n--- Breakdown ---")
    for k, v in stats.items():
        pct = (v / total_success) * 100 if total_success > 0 else 0
        print(f"{k}: {v} ({pct:.1f}%)")

if __name__ == '__main__':
    analyze()
