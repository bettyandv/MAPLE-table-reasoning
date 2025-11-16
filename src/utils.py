import pandas as pd
import json
from const import *
from transformers import AutoTokenizer
import tqdm
from pydantic import BaseModel
from typing import Dict
import re
import tiktoken
import string
from typing import List, Dict

def parse_baseline_response(response: str) -> str:
    """
    Extract the final answer after 'the answer is'. If not found, return the whole response.
    """
    matches = re.findall(r'(?i)the answer is\s*[:：]?\s*(.*?)(?:[\n\.!\r]|$)', response)

    if matches:
        return matches[-1].strip()
    else:
        return response.strip()
    
def extract_json_from_text(text: str) -> str:
    """Extract JSON from text that might contain markdown or natural language."""
    # Try to extract JSON from markdown code blocks
    if "```json" in text:
        parts = text.split("```json")
        json_part = parts[-1]
        json_text = json_part.split("```")[0]
        return json_text.strip()
    elif "```" in text:
        parts = text.split("```")
        if len(parts) >= 3:
            return parts[1].strip()

    # If no code blocks, try to find JSON by looking for { }
    text = text.strip()
    start_idx = text.find("{")
    if start_idx != -1:
        count = 0
        in_string = False
        escape_char = False

        for i in range(start_idx, len(text)):
            char = text[i]

            if char == "\\" and not escape_char:
                escape_char = True
                continue

            if char == '"' and not escape_char:
                in_string = not in_string

            if not in_string:
                if char == "{":
                    count += 1
                elif char == "}":
                    count -= 1
                    if count == 0:
                        return text[start_idx : i + 1]

            escape_char = False

    return text


def parse_json(output: str, dclass: BaseModel = None) -> Dict:
    """Try to parse and validate JSON output with enhanced error handling."""
    if not output:
        return {}, False

    # First, try to extract JSON from text
    output = post_process_output(output)
    json_str = extract_json_from_text(output)

    # List of potential fixes to try
    fixes = [
        lambda x: x,  # try original string
        lambda x: x.replace('\\"', '"'),  # fix escaped quotes
        lambda x: x.replace("'", '"'),  # replace single quotes with double quotes
        lambda x: x.replace("\n", "").replace("\r", ""),  # remove newlines
        lambda x: x.strip('"`'),  # remove any remaining markdown-style quotes
    ]

    # Try each fix until one works
    for fix in fixes:
        try:
            fixed_str = fix(json_str)
            result = json.loads(fixed_str)
            if not isinstance(result, dict):
                result = {"answer": result}
            # Validate against schema
            if dclass:
                validated_result = dclass.model_validate(result)
                return validated_result.model_dump()
            return result, True
        except Exception:
            continue

    return {}, False


def post_process_output(output):

    special_texts = [
        "<|start_header_id|>assistent<|end_header_id|>",
        "<|start_header_id|>assistant<|end_header_id|>",
        "<|im_start|>system",
        "<|im_start|>user",
        "<|im_start|>",
        "<|im_end|>",
        "<think>",
        "</think>",
    ]

    for special_text in special_texts:
        output = output.replace(special_text, "").strip()

    return output


def parse_json_old(text: str) -> dict:
    """
    Extracts and parses a JSON block from the given string.

    Parameters:
    - text (str): The input string containing a potential JSON block.

    Returns:
    - dict: The parsed JSON data if successful; otherwise, an empty dictionary.
    """
    # Locate the JSON block in the string
    start = text.find("```json")
    end = text.find("```", start + 7)

    # If a JSON block is found
    if start != -1 and end != -1:
        json_string = text[start + 7 : end]
        try:
            # Parse the JSON string
            json_data = json.loads(json_string)
            return json_data, True
            # valid = check_selector_response(json_data)  # Assumes a validation function
            # if valid:
            #     return json_data
            # else:
            #     return {}
        except:
            print(f"error: parse json error!\n")
            print(f"json_string: {json_string}\n\n")
            pass
    return {}, False

def clean_bool(text):
        # Handle real booleans
        if isinstance(text, bool):
            return "true" if text else "false"
        
        # Handle strings
        if isinstance(text, str):
            text = text.strip().lower()
            text = text.replace("\n", "").replace("\t", "")
            text = text.strip(string.punctuation)

            if text in ["yes", "true", "correct"]:
                return "true"
            elif text in ["no", "false","incorrect"]:
                return "false"
        return str(text)

def get_tokenizer(model_name: str):
    try:
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        encode = tokenizer.tokenize
    except Exception as e:
        print(f"Error loading tokenizer: {e}, maybe it's a commercial model.")
        tokenizer = tiktoken.encoding_for_model(model_name)
        encode = tokenizer.encode
    return encode

def load_wikiTQ_data(input_file: str) -> pd.DataFrame:
    wiki_data = pd.read_csv(input_file, sep="\t", on_bad_lines="skip")
    wiki_data["utterance"] = wiki_data["utterance"].apply(normalize_format)
    return wiki_data


def init_wikiTQ_messages(dataset: pd.DataFrame, starter: str) -> List[Dict]:
    dataset = dataset.rename(
        columns={
            "id": "qs_id",
            "utterance": "query",
            "table_markdown": "origin_table",
            "targetValue": "ground_truth",
        }
    )
    dataset["checker_result"] = [[] for _ in range(len(dataset))]
    dataset["reasoner_result"] = [[] for _ in range(len(dataset))]
    dataset["baseline_result"] = [[] for _ in range(len(dataset))]
    dataset["reflector_result"] = [[] for _ in range(len(dataset))]
    dataset["first_round_in_loop"] = True
    dataset["total_round"] = 0
    start_agent = AGENT_NAME_MAP[starter]
    dataset["send_to"] = start_agent
    dataset = dataset.drop(["context"], axis=1)
    return dataset.to_dict(orient="records")

def process_wiki_table(args, table_path: str, tokenizer) -> dict:
    """
    Process a single table to extract the required information.

    Args:
    - table_path (str): Path to the table to process.

    Returns:
    - dict: Extracted information as key-value pairs.
    """

    table_df = pd.read_csv(f"./data/WikiTableQuestions/{table_path}", escapechar="\\")
    
    before_clean = table_df.to_markdown(index=False)
    clean_table = normalize_format(before_clean)
    
    num_tokens = sum(count_tokens_advanced(cell, tokenizer) for _, row in table_df.iterrows() for cell in row)

    info = {
        "num_rows": len(table_df),
        "num_columns": len(table_df.columns),
        "num_tokens": num_tokens,
        "column_list": table_df.columns.tolist(),
        "table_markdown": clean_table,
    }
    return info


def preload_wiki_data(args, data):
    """
    Extract unique table addresses, process table information,
    and merge the results back into the original file.

    Args:
    - file_path (str): Path to the original TSV file containing table addresses.
    - output_path (str): Path to save the updated TSV file with additional information.

    Returns:
    - None: Saves the updated DataFrame to a file.
    """
    # # Step 1: Load the original TSV file
    # df = pd.read_csv(file_path, sep="\t")

    # Step 2: Extract the unique table addresses
    unique_tables = data["context"].unique()

    tokenizer = get_tokenizer(args.llm_in_use)
    # Step 3: Process each unique table
    processed_table_info = []
    for table_path in tqdm.tqdm(unique_tables, desc="Processing WikiTQ tables"):
        # Load and process the table (replace with actual logic)
        table_info = process_wiki_table(
            args, table_path, tokenizer=tokenizer
        )  # Custom function to extract info from a table
        processed_table_info.append({"context": table_path, **table_info})

    # Step 4: Create a DataFrame with the processed information
    table_info_df = pd.DataFrame(processed_table_info)

    # Step 5: Merge the processed table info back into the original DataFrame
    merged_df = data.merge(table_info_df, on="context", how="left")

    return merged_df

def normalize_format(text: str) -> str:
    # unify -
    text = text.replace("—", "-").replace("–", "-").replace("－", "-").replace("——", "-").replace("_", "-")
    
    # unify missing value
    text = re.sub(r"\b(nan|N/A|na|null|none)\b", "MISSING", text, flags=re.IGNORECASE)
    
    return text

def count_tokens_advanced(text, encode_function) -> int:
    """
    Tokenize a single text cell with a given tokenizer, return token count.
    Handles NaN and non-str gracefully.
    """
    if pd.isna(text):
        return 0
    return len(encode_function(str(text)))

def process_tabfact_table(args, tokenizer) -> list:
    # process tabfact table
    with open(args.input_file, "r", encoding="utf-8") as file:
        data = [json.loads(line) for line in file]

    unique_tables = {}
    for item in data:
        table_id = item["table_id"]
        table_text = item["table_text"]
        if table_id not in unique_tables:
            unique_tables[table_id] = table_text

    # transfer to list of dict
    unique_table_list = [{"table_id": k, "table_text": v} for k, v in unique_tables.items()]


    # process table
    for info in tqdm.tqdm(unique_table_list, desc="Processing TabFact tables"):

        # clean and change to markdown format
        header = info["table_text"][0]
        rows = info["table_text"][1:]
        table_df = pd.DataFrame(rows, columns=header)
        before_clean = table_df.to_markdown(index=False)
        clean_table = normalize_format(before_clean)
        info["column_list"] = table_df.columns.tolist()
        info["table_text"] = clean_table

        num_tokens = sum(count_tokens_advanced(cell, tokenizer) for _, row in table_df.iterrows() for cell in row)
        info['num_rows'] = len(table_df)
        info['num_columns'] = len(table_df.columns)
        info['num_tokens'] = num_tokens
        
    return unique_table_list

def load_tabfact_dataset(args):
    tabfact_statement_raw2clean_dict = {}
    with open(args.raw2clean_path, "r") as f:
        lines = f.readlines()
        for line in lines:
            info = json.loads(line)
            tabfact_statement_raw2clean_dict[info["statement"]] = info["cleaned_statement"]

    dataset = []
    # if first_n != -1:
    #     all_lines = []
    #     for line in open(args.input_file):
    #         all_lines.append(line)
    #         if len(all_lines) >= first_n: break
    # else:
    all_lines = open(args.input_file).readlines()

    for i, line in tqdm.tqdm(enumerate(all_lines), total=len(all_lines), desc=f"Loading tabfact dataset"):
        info = json.loads(line)
        info["id"] = f"{i}"
        
        # process statement
        if info["statement"] in tabfact_statement_raw2clean_dict:
            info["cleaned_statement"] = tabfact_statement_raw2clean_dict[
                info["statement"]
            ]
        else:
            info["cleaned_statement"] = info["statement"]
        info["cleaned_statement"] = normalize_format(info["cleaned_statement"])
        
        if info['label'] == 1:
            info['ground_truth'] = 'true'
        else:
            info['ground_truth'] = 'false'
        
        dataset.append(info)
    
    tokenizer = get_tokenizer(args.llm_in_use)

    table_info_list = process_tabfact_table(args, tokenizer=tokenizer)
    dataset_df = pd.DataFrame(dataset)
    table_info_df = pd.DataFrame(table_info_list)
    merged_df = dataset_df.merge(table_info_df, on="table_id", how="left")
    
    merged_df = merged_df.rename(
        columns={
            "table_text_x": "list_table",
            "table_text_y": "origin_table",
            "cleaned_statement": "query",
        }
    )
    
    return merged_df

def init_TabFact_messages(dataset: pd.DataFrame, starter: str) -> List[Dict]:
    dataset["checker_result"] = [[] for _ in range(len(dataset))]
    dataset["reasoner_result"] = [[] for _ in range(len(dataset))]
    dataset["baseline_result"] = [[] for _ in range(len(dataset))]
    dataset["reflector_result"] = [[] for _ in range(len(dataset))]
    dataset["first_round_in_loop"] = True
    dataset["total_round"] = 0
    start_agent = AGENT_NAME_MAP[starter]
    dataset["send_to"] = start_agent
    dataset = dataset.drop(["list_table"], axis=1)
    return dataset.to_dict(orient="records")


