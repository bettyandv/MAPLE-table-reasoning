# -*- coding: utf-8 -*-
import os
import json
import argparse

from utils import *
from agents import *
from coordinator import *
from const import *


def main(args):

    # Create the result folder if it doesn't exist
    result_folder = os.path.dirname(args.output_file)
    if not os.path.exists(result_folder):
        os.makedirs(result_folder)

    if os.path.exists(args.output_file):
        print(f"Loading previous user_messages from {args.output_file}")
        with open(args.output_file, "r", encoding="utf-8") as f:
            user_messages = [json.loads(line) for line in f]
    else:
        if args.dataset_name == TAB_NAME:
            tabfact_df = load_tabfact_dataset(args)
            user_messages = init_TabFact_messages(tabfact_df, args.start_agent)[: args.head]
        else:
            wiki_data = load_wikiTQ_data(args.input_file)
            wiki_data = preload_wiki_data(args, wiki_data)
            user_messages = init_wikiTQ_messages(wiki_data, args.start_agent)[: args.head]
    
    all_finished = False
    running_round = 0
    coordinator = Coordinator(args)
    while not all_finished:
        all_finished, user_messages = coordinator.process(user_messages, args)
        running_round += 1
        print(f"Running round {running_round} done!", flush=True)
        with open(args.output_file, "w", encoding="utf-8") as fp:
            for user_message in user_messages:
                fp.write(json.dumps(user_message, ensure_ascii=False) + "\n")
        print(f"Intermediate result saved after round {running_round}")

    # Dump user messages as a jsonl file, into the output_file
    with open(
        args.output_file, "w", encoding="utf-8"
    ) as fp:  
        for user_message in user_messages:
            fp.write(json.dumps(user_message, ensure_ascii=False) + "\n")
    
    coordinator.llm.close()
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_file", type=str, required=True, help="path to predicted output"
    )
    parser.add_argument(
        "--inference_mode", type=str, default="api_self_hosted", help="inference mode, offline_vllm or api or api_self_hosted or oai_batch"
    )
    parser.add_argument(
        "--input_file", type=str, required=True, help="path to dataset input"
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
        "--dataset_name", type=str, required=True, help="which dataset to run", default=WIKI_NAME
    )
    parser.add_argument(
        "--head", type=int, default=1000000, help="head of the dataset to run"
    )
    parser.add_argument(
        "--start_agent", type=str, default="REASONER_NAME", help="The start agent's name"
    )
    parser.add_argument(
        "--available_agent", type=str, default="REASONER_NAME,REFLECTOR_NAME,CHECKER_NAME", help="Comma-separated list of agent names"
    )
    parser.add_argument(
        "--raw2clean_path", type=str, default="./data/TabFact/raw2clean.jsonl", help="special file for tabfact dataset"
    )
    parser.add_argument(
        "--standard_baseline_variant", type=str, default="zero_shot", help="the type of standard baseline"
    )
    args = parser.parse_args()
    # print args
    for key, value in vars(args).items():
        print(f"{key}: {value}")

    # pretty print args json
    args_json_str = json.dumps(vars(args), indent=2, ensure_ascii=False)
    print(f"args:\n{args_json_str}")

    main(args=args)
