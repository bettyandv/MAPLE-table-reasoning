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
        # Check if the dataset is already cached
        if os.path.exists(args.cache_dir + f"/{args.dataset_name}.pkl"):
            print(f"Loading cached dataset from {args.cache_dir}/{args.dataset_name}.pkl")
            dataset = pd.read_pickle(args.cache_dir + f"/{args.dataset_name}.pkl")
        else:
            if args.dataset_name == TAB_NAME:
                dataset = load_tabfact_dataset(args)
            else:
                dataset = load_wikiTQ_data(args.input_file)
                dataset = preload_wiki_data(args, dataset)
            # save processed datastet into cache
            os.makedirs(args.cache_dir, exist_ok=True)
            dataset.to_pickle(args.cache_dir + f"/{args.dataset_name}.pkl")
        user_messages = {
            WIKI_NAME: init_wikiTQ_messages,
            TAB_NAME: init_TabFact_messages,
        }.get(args.dataset_name, lambda x, y: None)(dataset, args.start_agent)[: args.head]

    running_round = 0
    if os.path.exists(args.processed_jobs_file_path):
        with open(args.processed_jobs_file_path, "r") as f:
            running_round = json.load(f)['running_round']
    else:
        running_round = 0
    
    all_finished = False
    
    coordinator = Coordinator(args)

    while not all_finished:
        all_finished, user_messages, job_done = coordinator.job_process(user_messages, args, str(running_round))
        if not job_done:
            print("Job not done, waiting longer to fetch results")
            return
        with open(args.output_file, "w", encoding="utf-8") as fp:
            for user_message in user_messages:
                fp.write(json.dumps(user_message, ensure_ascii=False) + "\n")
        print(f"Running round {running_round} done!", flush=True)
        print(f"Intermediate result saved after round {running_round}")
        running_round += 1
        with open(args.processed_jobs_file_path, "w") as f:
            json.dump({'running_round': running_round}, f)

        

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output_file", type=str, required=True, help="path to predicted output"
    )
    parser.add_argument(
        "--inference_mode", type=str, default="batch", help="inference mode, batch or api or oai_batch"
    )
    parser.add_argument(
        "--input_file", type=str, required=True, help="path to dataset input"
    )
    parser.add_argument(
        "--llm_in_use", type=str, required=True, help="model used to inference"
    )
    parser.add_argument(
        "--llm_url", type=str, required=False, help=" ", default=None
    )
    parser.add_argument(
        "--llm_api_key", type=str, required=False, help=" ", default=None
    )
    parser.add_argument(
        "--azure_endpoint", type=str, required=False, help=" ", default=None
    )
    parser.add_argument(
        "--oai_job_dir", type=str, default="./oai_jobs", help="directory to save openai jobs"
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
    parser.add_argument(
        "--cache_dir", type=str, default="./cache", help="cache directory for dataset"
    )
    parser.add_argument(
        "--processed_jobs_file_path", type=str, default="./processed_jobs.jsonl", help="path to save processed jobs"
    )
    args = parser.parse_args()
    # print args
    for key, value in vars(args).items():
        print(f"{key}: {value}")

    # pretty print args json
    args_json_str = json.dumps(vars(args), indent=2, ensure_ascii=False)
    print(f"args:\n{args_json_str}")

    main(args=args)
