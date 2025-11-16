from agents import *
from const import *
from llm import LLMWrapper
import tqdm

AGENT_CLASS_MAP = {
    'Solver': Solver,
    'Baseline': Baseline,
    'Checker': Checker,
    'Reflector': Reflector,
    'Result_Analyze':Result_Analyze
}


class Coordinator(object):
    def __init__(self, args):
        self.llm = LLMWrapper(args)
        
        selected_agent_vars = [x.strip().upper() for x in args.available_agent.split(',')]
        for name in selected_agent_vars:
            if name not in AGENT_NAME_MAP:
                raise ValueError(f"Unknown agent name: {name}. Available keys: {AGENT_NAME_MAP.keys()}")

        selected_agent_names = [AGENT_NAME_MAP[name.strip()] for name in selected_agent_vars]
        self.agents = {name: AGENT_CLASS_MAP[name](available_agents=selected_agent_names) for name in selected_agent_names}

    def prepare_batch_prompt(self, user_messages, args):
        print("Preparing batch prompt")
        prompts = []
        active_user_messages = []
        for i,user_message in tqdm.tqdm(enumerate(user_messages),total=len(user_messages)):
            if user_message['send_to'] == END_NAME:
                continue
            
            prompts.append(self.llm.format_prompt(**self.agents[user_message['send_to']].prepare_prompt(user_message, args)))
            active_user_messages.append(i)
        print("Remaining active user messages: ", len(active_user_messages))
        return active_user_messages, prompts

    def generate_responses(self, prompts):
        print("Generating responses")
        return self.llm.generate_responses(prompts)

    def process_responses(self, user_messages, active_user_messages, responses, args):
        print("Processing responses")
        for i, response in tqdm.tqdm(zip(active_user_messages, responses), total=len(active_user_messages)):
            user_messages[i] = self.agents[user_messages[i]['send_to']].process_response(user_messages[i], response, args)
        return user_messages

    def process(self, user_messages: list, args):
        active_user_messages, prompts = self.prepare_batch_prompt(user_messages, args)
        if len(prompts) == 0 and len(active_user_messages) == 0:
            return True, user_messages

        responses = self.generate_responses(prompts)

        user_messages = self.process_responses(user_messages, active_user_messages, responses, args)
        return False, user_messages

    def job_process(self, user_messages: list, args, job_name):
        active_user_messages, prompts = self.prepare_batch_prompt(user_messages, args)
        if len(prompts) == 0 and len(active_user_messages) == 0:
            return True, user_messages, True
        
        job_id = self.llm.submit_batch_job(prompts, job_name)
        if job_id is None:
            print("Job has been submitted, fetch results now")
        responses = self.llm.fetch_batch_job_results(job_name)
        if responses is None:
            print("Job has not been finished yet, please wait")
            return False, None, False
        user_messages = self.process_responses(user_messages, active_user_messages, responses, args)

        return False, user_messages, True
        

        