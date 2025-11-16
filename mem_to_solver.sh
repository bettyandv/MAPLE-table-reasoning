#!/bin/bash
# Set PYTHONPATH to include the code directory
export PYTHONPATH=$(pwd)/src:$PYTHONPATH
export OMP_NUM_THREADS=1
export OMP_PROC_BIND=false

model="meta-llama/Llama-3.1-8B-Instruct"

# dataset="wiki"
dataset="tabfact"

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

############################# WIKITQ MEMORY SYSTEM ######################################
# python ./mem_to_solver.py \
#         --output_file "./memory_enhanced_result/wiki_result_3370b_ours_0516_c2w1.json" \
#         --memory_json_path "./memory/combined_memory_d1.json" \
#         --input_file ${input_file} \
#         --start_agent "REASONER_NAME" \
#         --dataset_name ${dataset_name} \
#         --head 4345 \
#         --retrieve_number 2 \
#         --inference_mode "api" \
#         --llm_in_use $model \
#         --retrieve_distance 1.0 \
#         --raw2clean_path "./data/TabFact/raw2clean.jsonl" \
        
        # | tee d10output_debug.log
        
############################# TABFACT MEMORY SYSTEM ######################################
python ./mem_to_solver.py \
        --output_file "./memory_enhanced_result/tabfact_result_3370b_ours_0516_c2t1.json" \
        --memory_json_path "./memory/combined_memory_d1.json" \
        --input_file ${input_file} \
        --start_agent "REASONER_NAME" \
        --dataset_name ${dataset_name} \
        --head 2025 \
        --retrieve_number 2 \
        --inference_mode "api" \
        --llm_in_use $model \
        --retrieve_distance 1.0 \
        --raw2clean_path "./data/TabFact/raw2clean.jsonl" \