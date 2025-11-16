#!/bin/bash

# Set PYTHONPATH to include the code directory
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
# export NCCL_IGNORE_DISABLED_P2P=1

# Generate Result on wikiTQ dataset for test set
# Run the Python script
# This will get ./results/wiki_result.json
# python ./run.py --output_file "./results/wiki_result.json" \
#                 --use_local_model=True \
# python ./run.py --output_file "./results/wiki_result.json" \
#                 --input_file "./data/WikiTableQuestions/data/pristine-unseen-tables.tsv" \
#                 --llm_in_use "meta-llama/Meta-Llama-3.1-70B-Instruct" \
#                 --LLM_URL "http://node14:9876/v1" \
#                 --LLM_API_KEY "betty"

# python ./run.py --output_file "./results/wiki_result.json" \
#                 --input_file "./data/WikiTableQuestions/data/pristine-unseen-tables.tsv" \
#                 --llm_in_use "meta-llama/Llama-3.2-1B-Instruct" --use_local_model

# echo "Done!"

# model="meta-llama/Llama-3.3-70B-Instruct"
model="Qwen/Qwen2.5-72B-Instruct"
# model="meta-llama/Llama-3.1-8B-Instruct"

model_short_name="qwen25"
# model_short_name="3370b"
# model_short_name="318b"
# model_short_name="gpt4om"

# prompt_type="zero_shot"
# prompt_type="few_shot"
# prompt_type="cot"
prompt_type="ours"

dataset="wiki"
# dataset="tabfact"

if [ "$dataset" = "wiki" ]; then
    input_file="./data/WikiTableQuestions/data/pristine-unseen-tables.tsv"
    dataset_name="WikiTQ"
elif [ "$dataset" = "tabfact" ]; then
    input_file="./data/TabFact/test.jsonl"
    dataset_name="TabFact"
else
    echo "Invalid dataset name. Please use 'wiki' or 'tabfact'."
    exit 1
fi

date="0516"

################################## For Standard Baseline ##########################################
# basline calue option: "zero_shot", "few_shot", "cot"
# dataset name option: "TabFact", "WikiTQ"
# python ./run_batch.py --output_file "./results/${dataset}_result_${model_short_name}_${prompt_type}_${date}.json" \
#                 --input_file ${input_file} \
#                 --llm_in_use $model --use_local_model \
#                 --available_agent "BASELINE_NAME" \
#                 --start_agent "BASELINE_NAME" \
#                 --dataset_name ${dataset_name} \
#                 --raw2clean_path "./data/TabFact/raw2clean.jsonl" \
#                 --standard_baseline_variant ${prompt_type} \
#                 # --head 30 \

################################## For Our Model ##########################################

# python ./run_batch.py --output_file "./results/${dataset}_result_${model_short_name}_${prompt_type}_${date}.json" \
#                 --input_file ${input_file} \
#                 --llm_in_use $model \
#                 --inference_mode "api_self_hosted" \
#                 --available_agent "REASONER_NAME,REFLECTOR_NAME,CHECKER_NAME" \
#                 --start_agent "REASONER_NAME" \
#                 --dataset_name ${dataset_name} \
#                 --raw2clean_path "./data/TabFact/raw2clean.jsonl" \
#                 # --head 30 \

VLLM_USE_V1=0 python ./run_batch.py --output_file "./memory_enhanced_result/${dataset}_result_${model_short_name}_${prompt_type}_${date}_c2w3.json" \
                --input_file ${input_file} \
                --llm_in_use $model \
                --inference_mode "api_self_hosted" \
                --available_agent "REASONER_NAME,REFLECTOR_NAME,CHECKER_NAME" \
                --start_agent "REASONER_NAME" \
                --dataset_name ${dataset_name} \
                --raw2clean_path "./data/TabFact/raw2clean.jsonl" \
#                 # --head 30 \

# For Memory Analyze
# python ./run_batch.py --output_file "./results/tabfact_result_qwen25_ours_RA.json" \
#                 --input_file ${input_file} \
#                 --llm_in_use $model \
#                 --inference_mode "offline_vllm" \
#                 --available_agent "RA_NAME" \
#                 --start_agent "RA_NAME" \
#                 --dataset_name ${dataset_name} \
#                 --raw2clean_path "./data/TabFact/raw2clean.jsonl" \
                # --head 30 \

          

