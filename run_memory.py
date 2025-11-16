# -*- coding: utf-8 -*-
import os
import json
import argparse
import tqdm
from memory_system import *

def load_checkpoint(output_file):
    if not os.path.exists(output_file):
        return {}, 0, 0, 0

    with open(output_file, 'r', encoding='utf-8') as f:
        checkpoint = json.load(f)

    memory_data = checkpoint.get("memories", {})
    resume_index = checkpoint.get("resume_index", 0)
    evol_count = checkpoint.get("evol_count", 0)
    evol_mem_count = checkpoint.get("evol_mem_count", 0)
    
    # Reconcondastruct the memory system
    memory_dict = {}
    for mem_id, mem_fields in memory_data.items():
        note = QAMemoryNote(**mem_fields)
        memory_dict[mem_id] = note

    return memory_dict, resume_index, evol_count, evol_mem_count

def main(args):
    result_folder = os.path.dirname(args.output_file)
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)

    ms = AgenticMemorySystem(args)
    print("Creating Memory System")

    # Step 1: resume from output file if exists
    memory_dict, resume_index, evol_count, evol_mem_count = load_checkpoint(args.output_file)
    ms.memories = memory_dict
    ms.evol_count = evol_count
    ms.evol_mem_count = evol_mem_count
    if memory_dict:
        print(f"[Resume] Loaded {len(memory_dict)} memories from {args.output_file}")
        ms.consolidate_memories()

    # Step 2: load input data
    with open(args.input_file, "r", encoding="utf-8") as file:
        raw_data = [json.loads(line) for line in file][:args.head]

    # Step 3: process remaining data
    for idx in tqdm.tqdm(range(resume_index, len(raw_data)), desc="Processing memories", unit="entry"):    
        current_entry = raw_data[idx]
        question_id=current_entry.get('qs_id',"")
        question_text=current_entry.get('query',"")
        question_type=current_entry.get('question_type',"")
        required_operations=current_entry.get('required_operations',[])
        correct_steps=current_entry.get('correct_steps',[])
        wrong_steps=current_entry.get('wrong_steps',[])
        correct_answer=current_entry.get('ground_truth',"")
        model_answer=current_entry.get('answer',"")
        error_type=current_entry.get('error_type',"")
        error_reason=current_entry.get('error_reason',"")
        tags=current_entry.get('tags',[])
        context=current_entry.get('context',"")
        keywords=current_entry.get('keywords',[])

        content = ms.build_content_from_fields(
            question_id=question_id,
            question_text=question_text,
            question_type=question_type,
            required_operations=required_operations,
            correct_steps=correct_steps,
            wrong_steps=wrong_steps,
            correct_answer=correct_answer,
            model_answer=model_answer,
            error_type=error_type,
            error_reason=error_reason,
            tags=tags,
            context=context,
            keywords=keywords
        )
        neighbours = ms.find_related_memories(content,args.retrieve_number,args.retrieve_distance)
        if len(neighbours) <= 3: # if the number of neighbours is less than 3, add the memory note to the memory system
            print("neighbours less than 3, starting add memory note")
            _ = ms.add_note(question_id=question_id,
                question_text=question_text,
                question_type=question_type,
                retrive_result=neighbours,
                required_operations=required_operations,
                correct_steps=correct_steps,
                wrong_steps=wrong_steps,
                correct_answer=correct_answer,
                model_answer=model_answer,
                error_type=error_type,
                error_reason=error_reason,
                content=content,
                tags=tags,
                category="Original note",
                context=context,
                keywords=keywords,
                args=args)
            print("finish add memory note")

        # Step 4: save every 10 entries to reduce I/O overhead
        if (idx + 1) % 10 == 0 or (idx + 1) == len(raw_data):
            with open(args.output_file, 'w', encoding='utf-8') as f:
                serializable_memories = {k: v.__dict__ for k, v in ms.memories.items()}
                serializable_retrieval_count = {str(k): v for k, v in ms.retrieval_count.items()}
                checkpoint = {
                    "memories": serializable_memories,
                    "resume_index": idx + 1,
                    "evol_count": ms.evol_count,
                    "evol_mem_count": ms.evol_mem_count,
                    "retrieval_count": serializable_retrieval_count
                }
                json.dump(checkpoint, f, ensure_ascii=False, indent=2)
            print(f"[Checkpoint] Saved {len(ms.memories)} memories at step {idx+1}")
            
    
    # save memory into a place for retrive and visulize
    print(f"[Done] Finish add all memories, add {len(ms.memories)} memories, evolve {ms.evol_count} times invoving {ms.evol_mem_count} memories")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_file", type=str, required=True, help="path to predicted output"
    )
    parser.add_argument(
        "--inference_mode", type=str, default="api_self_hosted", help="inference mode, offline_vllm or api or api_self_hosted or oai_batch"
    )
    parser.add_argument(
        "--input_file", type=str, required=True, help="path to memory input"
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
        "--head", type=int, default=1000000, help="head of the dataset to run"
    )
    parser.add_argument(
        "--retrieve_number", type=int, default=3, help="how many similar memory you want to retrieve"
    )
    parser.add_argument(
        "--retrieve_distance", type=float, default=0.3, help="the distance that can be classfied into one group"
    )
    parser.add_argument(
        "--evolve_type", type=str, default="LLM_based", help="the type of evolve, always, every_n_entries, LLM_based, never"
    )
    parser.add_argument(
        "--evolve_interval", type=int, default=5, help="the interval of evolve"
    )
    args = parser.parse_args()
    # print args
    for key, value in vars(args).items():
        print(f"{key}: {value}")

    # pretty print args json
    args_json_str = json.dumps(vars(args), indent=2, ensure_ascii=False)
    print(f"args:\n{args_json_str}")

    main(args=args)
