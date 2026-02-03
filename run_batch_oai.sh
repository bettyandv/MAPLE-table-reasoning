#!/bin/bash

# Set PYTHONPATH to include the code directory
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
# export NCCL_IGNORE_DISABLED_P2P=1

model="gpt-4o-mini"
# model="Qwen/Qwen2.5-72B-Instruct "
# model="meta-llama/Llama-2-13b-chat-hf"
# model="meta-llama/Meta-Llama-3.1-70B-Instruct"
# model="meta-llama/Llama-3.1-8B-Instruct"

# model_short_name="qwen25"
model_short_name="gpt4om"
# model_short_name="318b"

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

jobname="gpt4om_${date}_${prompt_type}_${dataset}"

# wiki_inputfile="./data/WikiTableQuestions/data/pristine-unseen-tables.tsv"
# tabfact_inputfile="./data/TabFact/test.jsonl"
API_KEY="please_replace_your_api_key_here"
# azure_endpoint="https://oai.azure.com/"
##################################WIKITQ DATASET##########################################

# For WikiTQ standard baselines
# basline calue option: "zero_shot", "few_shot", "cot"
# dataset name option: "TabFact", "WikiTQ"
python ./run_openai_batch.py --output_file "./memory_enhanced_result/${dataset}_result_${model_short_name}_${prompt_type}_${date}.json" \
                --input_file ${input_file} \
                --llm_in_use $model \
                --available_agent "REASONER_NAME,REFLECTOR_NAME,CHECKER_NAME" \
                --start_agent "REASONER_NAME" \
                --dataset_name ${dataset_name} \
                --raw2clean_path "./data/TabFact/raw2clean.jsonl" \
                --standard_baseline_variant ${prompt_type} \
                --cache_dir "./cache/${jobname}" \
                --inference_mode  'oai_batch' \
                --oai_job_dir ${jobname} \
                --llm_api_key $API_KEY \
                # --head 10 \
                # --azure_endpoint "https://oai.azure.com/" \
