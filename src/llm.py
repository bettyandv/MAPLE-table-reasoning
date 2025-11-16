from const import *
from openai import OpenAI, AsyncOpenAI, AzureOpenAI
from transformers import AutoModelForCausalLM, AutoTokenizer
from transformers.generation import GenerationConfig
import torch
import vllm
import asyncio
import os
import json
import pickle
import requests
import subprocess
import signal
import time
from asyncio import Semaphore
from tqdm.asyncio import tqdm_asyncio


def start_vllm(llm_in_use, max_tokens=16384):
    env = os.environ.copy()
    env["VLLM_USE_V1"] = "0"
    reasoning_model = (
        True if any([u in llm_in_use for u in ["deepseek", "QWQ"]]) else False
    )
    model_arg = f"--model {llm_in_use}"
    if reasoning_model:
        model_arg += " --reasoning-parser deepseek_r1 --enable-reasoning"

    vllm_cmd = f"""
    python -m vllm.entrypoints.openai.api_server \
    {model_arg} \
    --dtype bfloat16 \
    --api-key None \
    --tensor-parallel-size 2 \
    --host 0.0.0.0 \
    --port 9876 \
    --max-model-len {max_tokens} \
    --distributed-executor-backend ray \
    --enable-chunked-prefill \
    --gpu_memory_utilization 0.95 \
    --disable-uvicorn-access-log \
    --disable-log-stats \
    --disable-log-requests \
    --enable-prefix-caching
    """

    process = subprocess.Popen(
        vllm_cmd.strip().split(),
        # stdout=subprocess.PIPE,
        # stderr=subprocess.STDOUT,
        env=env,
        preexec_fn=os.setsid,  # In order to use pgid later to kill the entire process group
    )
    print(f"vLLM server started with PID {process.pid}.")
    return process


def wait_for_vllm_ready(port):
    print("waiting for vLLM server to be ready...")
    url = f"http://localhost:{port}/v1/models"
    for _ in range(60 * 15):  # 15 minutes timeout
        try:
            print(url)
            res = requests.get(url, timeout=1)
            print(res.status_code)
            if res.status_code == 200:
                print("vLLM server is ready.")
                return True
        except requests.exceptions.RequestException:
            print("vLLM server is initializing...")
            pass
        time.sleep(20)
    print("vLLM server is not ready after 15 minutes.")
    return False


def stop_vllm(process):
    print("Stopping vLLM server...")
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        process.wait()
        print("vLLM server stopped.")
    except Exception as e:
        print(f"Error stopping vLLM server: {e}")



class LLMWrapper:
    def __init__(self, args):
        self.llm_in_use = args.llm_in_use
        self.llm_url = args.llm_url
        self.llm_api_key = args.llm_api_key
        self.inference_mode = args.inference_mode # "offline_vllm", "api", "api_self_hosted", "oai_batch"
        self.llm = None
        self.tokenizer = None
        self.sampling_params = None
        self.oai_batch_mode = self.inference_mode == "oai_batch"
        # get the datetime as default suffix for the tmp dir
        self.oai_job_dir = getattr(args, "oai_job_dir", f"./tmp/")
        self.azure_endpoint = getattr(args, "azure_endpoint", None)
        
        self.init_llm()

    def close(self):
        if self.inference_mode == "api_self_hosted":
            stop_vllm(self.vllm_process)

    def init_llm(self):
        if self.inference_mode in ["api", "api_self_hosted"]:
            if self.inference_mode == "api_self_hosted":
                # Start vllm server
                self.vllm_process = start_vllm(self.llm_in_use)
                if wait_for_vllm_ready(9876):
                    print("vLLM server is ready.")
            self.client = AsyncOpenAI(
                base_url=self.llm_url,
                api_key=self.llm_api_key,
            )
        elif self.inference_mode == "oai_batch":
            if self.azure_endpoint is not None:
                api_version = self.azure_endpoint.split("api-version=")[-1]
                self.client = AzureOpenAI(
                    azure_endpoint=self.azure_endpoint,
                    api_key=self.llm_api_key,
                    api_version=api_version,
                )
            else:
                self.client = OpenAI(
                    base_url=self.llm_url,
                    api_key=self.llm_api_key,
                )
        else:
            self.tokenizer, self.llm, self.sampling_params = self.load_local_llm(
                model_name=self.llm_in_use
            )

    def load_local_llm(self, model_name):
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        generation_config = GenerationConfig.from_pretrained(model_name)
        sampling_params = vllm.SamplingParams(
            temperature=generation_config.temperature,
            top_p=generation_config.top_p,
            max_tokens=16384,
            repetition_penalty=generation_config.repetition_penalty,
            top_k=generation_config.top_k
        )
        # Use vllm to load model
        llm = vllm.LLM(
            model=model_name,
            tensor_parallel_size=torch.cuda.device_count(),
            dtype="bfloat16" if torch.cuda.is_bf16_supported() else "float16",
            distributed_executor_backend="ray",
            enable_prefix_caching=True,
            max_model_len=16384,
            gpu_memory_utilization=0.95,
            max_num_seqs=32,
        )
        return tokenizer, llm, sampling_params

    def format_prompt(self, system_prompt: str, user_prompt: str) -> str:
        message_list = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        if self.inference_mode == 'offline_vllm':
            return self.tokenizer.apply_chat_template(
                message_list,
                tokenize=False,
            )
        else:
            return message_list

    def generate_responses(self, prompts, post_process=lambda x: x.replace("<|start_header_id|>assistant<|end_header_id|>", "").strip()):
        if self.inference_mode == 'offline_vllm':
            model_outputs = self.llm.generate(
                prompts, sampling_params=self.sampling_params
            )
            responses = [post_process(output.outputs[0].text) for output in model_outputs]
        else:
            responses = asyncio.run(self.call_llm_api_async(prompts))
        return responses

    def call_llm_api(self, system_prompt: str, user_prompt: str):
        messages = self.format_prompt(system_prompt, user_prompt)
        completion = self.client.chat.completions.create(
            model=self.llm_in_use,
            messages=messages,
        )

        return completion.choices[0].message.content.strip()


    async def call_llm_api_async_single(self, prompt):

        try:
            completion = await self.client.chat.completions.create(
                model=self.llm_in_use,
                messages=prompt,
            )
            return completion.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error: {e}")
            return None
        
    
    async def call_llm_api_async(self, prompts):
        sem = Semaphore(16) # Limit the number of concurrent requests
        
        async def generate_one_sample_limited(prompt):
            async with sem:
                return await self.call_llm_api_async_single(prompt)

        return await tqdm_asyncio.gather(*[generate_one_sample_limited(prompt) for prompt in prompts])
    

    def submit_batch_job(self, prompts, job_name):
        job_dir = self.oai_job_dir
        # Check if the job is already submitted with f"{job_name}_reciept.pkl"
        if os.path.exists(
            os.path.join(job_dir, f"{job_name}_reciept.pkl")
        ):
            print(f"Job {job_name} already submitted, skipping...")
            return None
                
        def format_prompt(message, model_name: str, prompt_id: int):
            return {
                "custom_id": f"request-{prompt_id}",
                "method": "POST",
                "url": "/v1/chat/completions",
                "body": {
                    "model": model_name,
                    "messages": message,
                },
            }
        model_inputs = [
            format_prompt(prompt, self.llm_in_use, i) for i, prompt in enumerate(prompts)
        ]
        
        os.makedirs(job_dir, exist_ok=True)
        with open(f"{job_dir}/{job_name}.jsonl", "w") as f:
            for input_data in model_inputs:
                f.write(json.dumps(input_data) + "\n")

            
        batch_input_file = self.client.files.create(
            file=open(f"{job_dir}/{job_name}.jsonl", "rb"),
            purpose="batch",
        )

        
        print(batch_input_file)

            
        batch_input_file_id = batch_input_file.id
        reciept = self.client.batches.create(
            input_file_id=batch_input_file_id,
            endpoint="/v1/chat/completions",
            completion_window="24h",
            metadata={"description": "TableQA batch job"},
        )
            
        print(f"Reciept created: {reciept}")
        # Save the reciept to a pickle file in tmp directory
        output_path = os.path.join(job_dir, f"{job_name}_reciept.pkl")

        with open(output_path, "wb") as f:
            pickle.dump(reciept, f)

        return reciept.id

    def fetch_batch_job_results(self, job_name):
        job_dir = self.oai_job_dir
        job_result_file = os.path.join(job_dir, f"{job_name}_batch_output.jsonl")
        # Check if the job is already fetched with f"{job_name}_batch_output.jsonl"
        if os.path.exists(job_result_file):
            print(f"Job {job_name} already fetched, load results...")
            job_results = []
            with open(job_result_file, "r") as f:
                for line in f:
                    job_results.append(json.loads(line))
            llm_run_results = []
            for i, result in enumerate(job_results):
                response = result["response"]["body"]["choices"][0]["message"]["content"].strip()
                llm_run_results.append(response)
            print(f"Job results loaded, total {len(llm_run_results)} results")
            return llm_run_results

        with open(os.path.join(job_dir, f"{job_name}_reciept.pkl"), "rb") as f:
            reciept = pickle.load(f)
        
        retrieved_information = self.client.batches.retrieve(reciept.id)
        job_status = retrieved_information.status
        print(f"Reciept status: {job_status}")
        uncomplete_status = [ "failed", "in_progress", "validating", "finalizing" ]
        if uncomplete_status.count(job_status) > 0:
            print(f"Job: {job_status}")
            print(retrieved_information)
            return None
        
            
        assert job_status == "completed"
        print(retrieved_information.request_counts.__dict__)

        job_file_id = retrieved_information.output_file_id
        print(f"Job file id: {job_file_id}")

        # Download the results
        file_response = self.client.files.content(job_file_id)

        with open(job_result_file, "w") as f:
            f.write(file_response.text)
        print(f"Job results saved to {job_result_file}")

        # Load the results
        job_results = []
        with open(job_result_file, "r") as f:
            for line in f:
                job_results.append(json.loads(line))
        llm_run_results = []
        for i, result in enumerate(job_results):
            response = result["response"]["body"]["choices"][0]["message"]["content"].strip()
            llm_run_results.append(response)
        print(f"Job results loaded, total {len(llm_run_results)} results")
        return llm_run_results