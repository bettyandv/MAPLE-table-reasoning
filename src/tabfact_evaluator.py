import pandas as pd
import json
import string
import os
import argparse
from tqdm import tqdm
tqdm.pandas()


def evaluate_accuracy_from_jsonl(file_path: str, save_path: str = None) -> float:
    # Create the result folder if it doesn't exist
    result_folder = os.path.dirname(save_path)
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)
    
    # with open(file_path, "r", encoding="utf-8") as file:
    #     data = [json.loads(line) for line in file]
    with open(file_path, "r", encoding="utf-8") as file:
        data = [json.loads(line) for line in tqdm(file, desc="Loading JSONL")]

    df = pd.DataFrame(data)

    def clean(text):
        if not isinstance(text, str):
            return ""
        text = text.strip().lower()
        text = text.replace("\n", "").replace("\t", "")
        text = text.strip(string.punctuation)

        if text in ["yes", "true", "True", "correct", "Yes", "YES"]:
            return "true"
        elif text in ["no", "false",'False',"No", "NO"]:
            return "false"
        return text  

    tqdm.pandas(desc="Evaluating")
    df["clean_answer"] = df['answer'].progress_apply(clean)
    # df["clean_answer"] = df['answer'].apply(clean)

    df["is_correct"] = df["clean_answer"] == df["ground_truth"]
    accuracy = df["is_correct"].mean()

    print(f"Total: {len(df)}, Correct: {df['is_correct'].sum()}, Accuracy: {accuracy:.2%}")

    if save_path:
        df.to_csv(save_path, index=False)
        print(f"Saved evaluate results to CSV: {save_path}")

    return accuracy

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate JSONL accuracy")
    parser.add_argument(
        "--file_path", type=str, required=True,
        help="Path to the .jsonl file with model predictions"
    )
    parser.add_argument(
        "--save_path", type=str, default=None,
        help="Optional path to save augmented JSONL with clean_answer and is_correct"
    )
    args = parser.parse_args()

    acc = evaluate_accuracy_from_jsonl(args.file_path, args.save_path)
    print(f"Final Accuracy: {acc:.5f}")