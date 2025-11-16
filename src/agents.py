from const import *
from llm import *
from utils import *
from const import *

import abc

class BaseAgent(metaclass=abc.ABCMeta):
    def __init__(self, available_agents: list):
        self.available_agents = available_agents
        self.llm = None
        pass

    @abc.abstractmethod
    def prepare_prompt(self):
        pass

    @abc.abstractmethod
    def process_response(self):
        pass   
    
class Solver(BaseAgent):
    """
    """
    name = REASONER_NAME
    
    def __init__(self, available_agents: list):
        super().__init__(available_agents)
        
    def prepare_prompt(self, message, args):
        # first_round_in_loop will affect the table that give to the LLM
        if message['first_round_in_loop'] == True:
            current_table = message.get('origin_table')
        else:
            if message.get('current_table',"") == "":
                current_table = message.get('origin_table')
            else:
                current_table = message.get('current_table')
        question = message.get('query')

        action_history = self.retrieve_action_history(message)
        
        optional_info = ""
        reflector_feedback = message.get('reflector_result', [])
        if reflector_feedback:
            optional_info += f"{reflector_feedback[-1]}"

        tried_times = message.get('inner_reasoner_round', 0)
        this_round = tried_times + 1
        rounds_left = MAX_INNER_REASONER_ROUND - this_round

        related_memory = message.get('retrieved_memory', "")

        
        # Create user prompt
        prompts = DATASET_PROMPTS[args.dataset_name][REASONER_NAME]
        user_prompt = prompts["user_prompt"].format(
            related_memory=related_memory,
            table=current_table,
            question=question,
            action_history=action_history,
            optional_info=optional_info,
            this_round=this_round,
            rounds_left=rounds_left
        )

        # Return complete system prompt and user prompt
        return {
            "system_prompt": prompts["system_prompt"],
            "user_prompt": user_prompt
        }
        
    def process_response(self, message, llm_response: str, args):
        
        # Counting section
        message["total_round"] += 1

        if message['first_round_in_loop'] == True:
            if 'outer_reasoner_round' not in message:
                message['outer_reasoner_round'] = 1
            else:
                message['outer_reasoner_round'] += 1
            message['first_round_in_loop'] = False
            template = { 'outer_round': message['outer_reasoner_round'],
                         'inner_result_list': []
                        }
            message['reasoner_result'].append(template)    
        
        if 'inner_reasoner_round' not in message:
            message['inner_reasoner_round'] = 1
        else:
            message['inner_reasoner_round'] += 1
        
        # Response processing section
        reasoner_result, is_format_correct = parse_json(llm_response)

        if is_format_correct:
            new_inner_dict ={
            'inner_round': message['inner_reasoner_round'],
            'thought': reasoner_result.get("thought",""),
            'action': reasoner_result.get("action",""),
            'intermediate_table': reasoner_result.get("intermediate_table",""),
            'answer': str(reasoner_result.get("answer","")).replace("<NOT_READY>",""),
            'llm_response':llm_response
                            }
            message['current_table'] = reasoner_result.get("intermediate_table","")
        else:
            answer = "INVALID_FORMAT"
            new_inner_dict ={
            'inner_round': message['inner_reasoner_round'],
            'thought': "",
            'action': "",
            'intermediate_table': "",
            'answer': answer,
            'llm_response':llm_response
                            } 
            
        outer_round_index = message['outer_reasoner_round'] - 1
        inner_result_list = message['reasoner_result'][outer_round_index]['inner_result_list']
        inner_result_list.append(new_inner_dict)
        
        message['answer'] = new_inner_dict['answer']
        
        # Route section
        # the format isn't correct
        if not is_format_correct:
            if message['inner_reasoner_round'] < MAX_INNER_REASONER_ROUND:
                message['send_to'] = REASONER_NAME  # Request regeneration
            else:
                # Handle max_round exceeded scenario
                if CHECKER_NAME in self.available_agents:
                    message['send_to'] = CHECKER_NAME
                else: # Assume there is only reasoner agent
                    if message['outer_reasoner_round'] < MAX_OUTER_REASONER_ROUND:
                        # start a new outer round
                        message['send_to'] = REASONER_NAME
                        message['first_round_in_loop'] = True
                        message['inner_reasoner_round'] = 0
                    else:
                        message['send_to'] = END_NAME # run out of outer round
        # the format is correct
        else:
            # check if the answer is valid
            if message['answer'] != "": # assume the answer is ready
                if CHECKER_NAME in self.available_agents:
                    message['send_to'] = CHECKER_NAME
                else:
                    message['send_to'] = END_NAME
            else:
                # answer not ready, need another round
                if message['inner_reasoner_round'] < MAX_INNER_REASONER_ROUND:
                    message['send_to'] = REASONER_NAME  # inner loop
                else: # didn't come up with an answer in last loop
                    if message['outer_reasoner_round'] < MAX_OUTER_REASONER_ROUND:
                        # start a new outer round
                        message['send_to'] = REASONER_NAME
                        message['first_round_in_loop'] = True
                        message['inner_reasoner_round'] = 0
                    else: # at the end, the answer is still ""
                        message['send_to'] = END_NAME
        
        return message
    
    def retrieve_action_history(self, message: list) -> str:
        if message['first_round_in_loop'] == True:
            history = None
        else:
            index = message['outer_reasoner_round'] - 1
            round_list = message['reasoner_result'][index]['inner_result_list']
            # actions = [f"{item['inner_round']}. {item['action']}" for item in round_list if item.get('action', '').strip()]
            actions = [
                        f"{item['inner_round']}. {self.stringify_action(item.get('action'))}"
                        for item in round_list
                        if self.stringify_action(item.get('action'))  
                        ]
            history = '\n'.join(actions) if actions else "None"
        return history
    
    def stringify_action(self, action) -> str:
        if isinstance(action, str):
            return action.strip()
        elif isinstance(action, dict):
            return ", ".join(f"{k}={v}" for k, v in action.items())
        else:
            return ""
        
class Checker(BaseAgent):
    """
    """
    name = CHECKER_NAME
    
    def __init__(self, available_agents: list):
        super().__init__(available_agents)
        
    def prepare_prompt(self, message, args):
        origin_table = message.get('origin_table')
        question = message.get('query')
        answer = message.get('answer', '')

        prompts = DATASET_PROMPTS[args.dataset_name][CHECKER_NAME]
        if args.dataset_name == WIKI_NAME:
            prompt = prompts["user_prompt"].format(table=origin_table, question=question, answer=answer)
        else:
            prompt = prompts["user_prompt"].format(answer=answer)
        
        return {
            "system_prompt": prompts["system_prompt"],
            "user_prompt": prompt
        }
    
    def calculate_checker_score(self, response: dict) -> int:
        """
        Calculate the total score based on the feedback scores.
        Invalid scores (non-integer types) are treated as 0.

        Parameters:
        response (dict): The checker response containing scores for each aspect.

        Returns:
        int: The total score.
        """
        feedback = response.get("feedback", {})
        total_score = 0

        for aspect, details in feedback.items():
            # Ensure details is a dictionary before accessing 'score'
            if isinstance(details, dict):
                score = details.get("score", 0)
                if not isinstance(score, int):
                    score = 0
            else:
                score = 0  # If details is not a dict, treat score as 0
            total_score += score

        return total_score

    def process_response(self, message, llm_response: str, args):     
        
        # Counting section
        message["total_round"] += 1

        if 'checker_round' not in message:
            message['checker_round'] = 1
        else:
            message['checker_round'] += 1
        
        # Response processing section
        checker_result, is_format_correct = parse_json(llm_response)

        if not is_format_correct:
            checker_score = -100
            message['checker_result'].append({
                'round': message['checker_round'],
                'feedback': llm_response,
                'checker_score': checker_score,
            })
        else:
            checker_score = self.calculate_checker_score(checker_result)
            message['checker_result'].append({
                'round': message['checker_round'],
                'feedback': checker_result.get("feedback",{}),
                'checker_score': checker_score,
            }) 
        
        # Route section
        checker_point = 0
        if args.dataset_name == WIKI_NAME:
            checker_point = WIKI_CHECKER_POINTS
        else:
            checker_point = TAB_CHECKER_POINTS
        
        if is_format_correct:
            if checker_score == checker_point:
                message['send_to'] = END_NAME  # End the process
            else:
                if REFLECTOR_NAME in self.available_agents:
                    message['send_to'] = REFLECTOR_NAME
                else:
                    if message['outer_reasoner_round'] < MAX_OUTER_REASONER_ROUND:
                        # start a new outer round
                        message['send_to'] = REASONER_NAME
                        message['first_round_in_loop'] = True
                        message['inner_reasoner_round'] = 0
                    else: 
                        message['send_to'] = END_NAME
        else:
            if message['checker_round'] < MAX_CHECKER_ROUND:
                message['send_to'] = CHECKER_NAME  # Retry the checker
            else:
                # Handle max_round exceeded scenario
                message['send_to'] = END_NAME
        return message
    
          
class Reflector(BaseAgent):
    """
    """
    name = REFLECTOR_NAME
    
    def __init__(self, available_agents: list):
        super().__init__(available_agents)
        
    def prepare_prompt(self, message, args):
        origin_table = message.get('origin_table')
        question = message.get('query')
        answer = message.get('answer', '')
        checker_info = ''
        checker_results = message.get('checker_result', [])
        if isinstance(checker_results, list) and checker_results:
            checker_info = checker_results[-1].get('feedback', '')
        reasoner_info = ''
        reasoner_results = message.get('reasoner_result', [])
        if isinstance(reasoner_results, list) and reasoner_results:
            reasoner_info = reasoner_results[-1].get('inner_result_list', [])

        # Create user prompt
        prompts = DATASET_PROMPTS[args.dataset_name][REFLECTOR_NAME]
        user_prompt = prompts["user_prompt"].format(
            table=origin_table,
            question=question,
            reasoner_history=reasoner_info,
            answer=answer,
            checker_feedback=checker_info
        )

        # Return complete system prompt and user prompt
        return {
            "system_prompt": prompts["system_prompt"],
            "user_prompt": user_prompt
        }
        
    def process_response(self, message, llm_response: str, args):

        # Counting section
        message["total_round"] += 1
        
        if 'reflector_round' not in message:
            message['reflector_round'] = 1
        else:
            message['reflector_round'] += 1
        
        # Response processing section
        reasoner_result, is_format_correct = parse_json(llm_response)
        if is_format_correct:
            message['reflector_result'].append({
                'round': message['reflector_round'],
                'diagnosis': reasoner_result.get("diagnosis", ""),
                'improvement_plan': reasoner_result.get("improvement_plan", ""),
            })
        else:
            message['reflector_result'].append({
                'round': message['reflector_round'],
                'diagnosis': llm_response,
                'improvement_plan': "",
            })
        
        # Route section
        if is_format_correct:
            if message['outer_reasoner_round'] < MAX_OUTER_REASONER_ROUND:
                # start a new outer round
                message['send_to'] = REASONER_NAME
                message['first_round_in_loop'] = True
                message['inner_reasoner_round'] = 0
            else: 
                message['send_to'] = END_NAME
        else:
            if message['reflector_round'] < MAX_REFLECTOR_ROUND:
                message['send_to'] = REFLECTOR_NAME
            else:
                message['send_to'] = END_NAME
        
        return message
    
    def retrieve_action_history(self, message: list) -> str:
        if message['first_round_in_loop'] == True:
            history = None
        else:
            index = message['outer_reasoner_round'] - 1
            round_list = message['reasoner_result'][index]['inner_result_list']
            actions = [f"{item['inner_round']}. {item['action']}" for item in round_list if item.get('action', '').strip()]
            history = '\n'.join(actions) if actions else "None"
        return history

        
class Baseline(BaseAgent):
    """
    
    """
    name = BASELINE_NAME
    
    def __init__(self, available_agents: list):
        super().__init__(available_agents)
    
    def prepare_prompt(self, message, args):
        origin_table = message.get('origin_table')
        question = message.get('query')
        
        prompts = STANDARD_BASELINE_PROMPTS[args.dataset_name][args.standard_baseline_variant]
        if prompts is None:
            raise ValueError(f"Prompt not found for dataset={args.dataset_name}, variant={args.standard_baseline_variant}")
        prompt = prompts["user_prompt"].format(table=origin_table, question=question)
        return {
            "system_prompt": prompts["system_prompt"],
            "user_prompt": prompt
        }
       
    def process_response(self, message, llm_response: str, args):
        
        if 'baseline_round' not in message:
            message['baseline_round'] = 1
        else:
            message['baseline_round'] += 1
        
        answer = parse_baseline_response(llm_response)
        message['baseline_result'].append({
                'round': message['baseline_round'],
                'answer': answer
            })

        message['answer'] = answer
        message['send_to'] = END_NAME
        
        return message


class Result_Analyze(BaseAgent):
    """
    
    """
    name = RA_NAME
    
    def __init__(self, available_agents: list):
        super().__init__(available_agents)
    
    def prepare_prompt(self, message, args):
        table = message.get('origin_table')
        question = message.get('query')
        ground_truth = message.get('ground_truth')
        answer = message.get('answer')
        reasoner_history=message['reasoner_result'][-1]['inner_result_list']
        if message['reflector_result'] ==[]:
            reflector_feedback=None
        else:
            reflector_feedback=message['reflector_result'][-1]
        
        prompt = result_analyze_user.format(question=question,table=table,answer=answer,ground_truth=ground_truth,reasoner_history=reasoner_history,reflector_feedback=reflector_feedback)
        return {
            "system_prompt": result_analyze_system,
            "user_prompt": prompt
        }
       
    def process_response(self, message, llm_response: str, args):
        ra_result, is_format_correct = parse_json(llm_response)
        if is_format_correct:
            message['question_type'] = ra_result.get('question_type',"")
            message['required_operations'] = ra_result.get('required_operations',[])
            message['context'] = ra_result.get('context',"")
            message['keywords'] = ra_result.get('keywords',[])
            message['tags'] = ra_result.get('tags',[])
            message['correct_steps'] = ra_result.get('correct_steps',[])
            message['wrong_steps'] = ra_result.get('wrong_steps',[])
            message['error_type'] = ra_result.get('error_type',"")
            message['error_reason'] = ra_result.get('error_reason',"")
        else:
            message['question_type'] = llm_response
        
        message['send_to'] = END_NAME
        
        return message