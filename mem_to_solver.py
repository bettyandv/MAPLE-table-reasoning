# -*- coding: utf-8 -*-
import os
import argparse
import tqdm
from utils import *
from typing import Tuple
import json
from memory_system import AgenticMemorySystem, QAMemoryNote
from typing import List, Dict

def load_and_consolidate_memory(args) -> Tuple[AgenticMemorySystem, int, int, int]:
    """
    Load memory from a JSON file, rebuild the memory system, and consolidate vector store.
    """
    # Load saved memory JSON file
    with open(args.memory_json_path, "r", encoding="utf-8") as f:
        memory_data = json.load(f)

    # Initialize memory system
    ms = AgenticMemorySystem(args)

    # Restore each memory note into the system
    for mem_id, mem_dict in memory_data.get("memories", {}).items():
        note = QAMemoryNote(**mem_dict)  # Unpack all fields directly
        ms.memories[mem_id] = note

    # Consolidate into the retriever (rebuild vector index)
    ms.consolidate_memories()

    # Restore resume progress and evolution stats
    resume_index = memory_data.get("resume_index", 0)
    ms.evol_count = memory_data.get("evol_count", 0)
    ms.evol_mem_count = memory_data.get("evol_mem_count", 0)

    return ms, resume_index, ms.evol_count, ms.evol_mem_count

def load_data(args):
    if args.dataset_name == TAB_NAME:
            tabfact_df = load_tabfact_dataset(args)
            user_messages = init_TabFact_messages(tabfact_df, args.start_agent)[: args.head]
    else:
        wiki_data = load_wikiTQ_data(args.input_file)
        wiki_data = preload_wiki_data(args, wiki_data)
        user_messages = init_wikiTQ_messages(wiki_data, args.start_agent)[: args.head]
    return user_messages

def attach_top1_memory_to_user_messages(user_messages: List[Dict], ms, args) -> List[Dict]:
    """
    For each user message, retrieve the top-1 most relevant memory and attach it to the message.
    """
    for msg in user_messages:
        # Step 1: Compose the search query from question and column headers
        retrieval_query = f"question: {msg['query']} | columns: {', '.join(msg['column_list'])}"

        # Step 2: Retrieve top-k similar memories (default k=1)
        top_memories = ms.find_related_memories(retrieval_query, k=args.retrieve_number, threshold=args.retrieve_distance)
        # print(top_memories)
        if top_memories:
            top = top_memories[1] if len(top_memories) > 1 else top_memories[0]
            print(f"{msg['query']} => Retrieved {len(top_memories)} memories")
            retrieved_text = (
                f"Past Question: {top['question_text']}\n"
                f"Question Type: {top['question_type']}\n"
                f"Required Operations: {', '.join(top['required_operations'])}\n\n"
                f"Correct Reasoning Steps:\n" +
                '\n'.join([f"- {step}" for step in top['correct_steps']]) + "\n\n"
                f"Mistake in previous attempt:\n" +
                '\n'.join([f"- {step}" for step in top['wrong_steps']]) + "\n\n"
                f"Error Type: {top['error_type']}\n"
                f"Error Reason: {top['error_reason']}"
            )
            msg["retrieved_memory"] = retrieved_text
            msg["memory_distance"] = top.get("distance", 1.0)
        else:
            msg["retrieved_memory"] = "No related memory"
            msg["memory_distance"] = 1.0  # farthest possible

    return user_messages


def main(args):
    result_folder = os.path.dirname(args.output_file)
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)

    # Step 1: Load memory from file and consolidate vector index
    ms, resume_index, evol_count, evol_mem_count = load_and_consolidate_memory(args)
    print(f"Loaded memory with {len(ms.memories)} notes. Evolutions: {evol_count}, affected memories: {evol_mem_count}")

    # Step 2: Load dataset and user messages
    user_messages = load_data(args)
    print(f"Loaded {len(user_messages)} user messages from dataset: {args.dataset_name}")

    # Step 3: Inject top-1 memory into each user message
    user_messages = attach_top1_memory_to_user_messages(user_messages, ms, args)

    # Step 4: Save the final messages with memory info
    with open(args.output_file, "w", encoding="utf-8") as fp:
        for msg in tqdm.tqdm(user_messages, desc="Saving messages with memory", unit="msg"):
            fp.write(json.dumps(msg, ensure_ascii=False) + "\n")

    print(f"Memory-enriched user messages saved to: {args.output_file}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_file", type=str, required=True, help="path to predicted output"
    )
    parser.add_argument(
        "--memory_json_path", type=str, required=True, help="path to memory input"
    )
    parser.add_argument(
        "--input_file", type=str, required=True, help="path to memory input"
    )
    parser.add_argument(
        "--head", type=int, default=1000000, help="head of the dataset to run"
    )
    parser.add_argument(
        "--start_agent", type=str, default="REASONER_NAME", help="The start agent's name"
    )
    parser.add_argument(
        "--dataset_name", type=str, required=True, help="which dataset to run", default=WIKI_NAME
    )
    parser.add_argument(
        "--retrieve_number", type=int, default=3, help="how many similar memory you want to retrieve"
    )
    parser.add_argument(
        "--llm_in_use", type=str, required=True, help="model used to inference"
    )
    parser.add_argument(
        "--llm_url", type=str, required=False, help=" ", default="http://localhost:9876/v1/"
    )
    parser.add_argument(
        "--llm_api_key", type=str, required=False, help=" ", default="None"
    )
    parser.add_argument(
        "--inference_mode", type=str, default="api_self_hosted", help="inference mode, offline_vllm or api or api_self_hosted or oai_batch"
    )
    parser.add_argument(
        "--retrieve_distance", type=float, default=0.3, help="the distance that can be classfied into one group"
    )
    parser.add_argument(
        "--raw2clean_path", type=str, default="./data/TabFact/raw2clean.jsonl", help="special file for tabfact dataset"
    )
    args = parser.parse_args()
    # print args
    for key, value in vars(args).items():
        print(f"{key}: {value}")

    # pretty print args json
    args_json_str = json.dumps(vars(args), indent=2, ensure_ascii=False)
    print(f"args:\n{args_json_str}")

    main(args=args)