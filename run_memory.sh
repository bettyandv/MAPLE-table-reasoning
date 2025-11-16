#!/bin/bash
# Set PYTHONPATH to include the code directory
export PYTHONPATH=$(pwd)/src:$PYTHONPATH

model="meta-llama/Llama-3.3-70B-Instruct"
# model="meta-llama/Llama-3.1-8B-Instruct"

############################# WIKITQ MEMORY SYSTEM ######################################
python ./run_memory.py \
        --output_file "./memory/wiki_result_3370b_ours_RA_wiki_4344_d5.json" \
        --inference_mode "offline_vllm" \
        --input_file "./results/wiki_result_3370b_ours_RA.json" \
        --llm_in_use $model \
        --head 4344 \
        --retrieve_number 3 \
        --retrieve_distance 0.5 | tee outputd3.log