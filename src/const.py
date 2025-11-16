LLM_URL="http://node14:9876/v1"
LLM_API_KEY="betty"

MAX_INNER_REASONER_ROUND = 5
MAX_OUTER_REASONER_ROUND = 4
MAX_CHECKER_ROUND = 5
MAX_REFLECTOR_ROUND = 5
WIKI_CHECKER_POINTS = 6
TAB_CHECKER_POINTS = 1

CHECKER_NAME = 'Checker'
END_NAME = 'End'
REASONER_NAME = 'Solver'
BASELINE_NAME = 'Baseline'
REFLECTOR_NAME = 'Reflector'
RA_NAME ='Result_Analyze'

AGENT_NAME_MAP = {
    'REASONER_NAME': REASONER_NAME,
    'BASELINE_NAME': BASELINE_NAME,
    'REFLECTOR_NAME': REFLECTOR_NAME,
    'CHECKER_NAME': CHECKER_NAME,
    'RA_NAME':RA_NAME
}

WIKI_NAME = "WikiTQ"
TAB_NAME = "TabFact"

# All prompts template

############################################################# Prompts For Baseline ################################################################

wiki_baseline_zero_system = """Here is the table to answer this question. Please directly answer the question without any explanation."""

tabfact_baseline_zero_system = """Here is a table and a statement. Decide if the statement is correct based on the table. Please directly judge the statement."""

wiki_baseline_few_system = """
Here is the table to answer this question. Please directly answer the question without any explanation.

<Example1>
<Table>
| Year | Revenue | Product |
|------|---------|---------|
| 2020 | 100     | A       |
| 2021 | 200     | B       |
| 2020 | 150     | C       |

<Question>
What is the total revenue in 2020?

The answer is: 250

==========
<Example2>
<Table>
| Year | Product | Quantity |
|------|---------|----------|
| 2020 | A       | 10       |
| 2021 | B       | 20       |
| 2020 | C       | 15       |

<Question>
Are there more products in 2020 than in 2021?

The answer is: yes
"""

tabfact_baseline_few_system = """
Here is a table and a statement. Decide if the statement is correct based on the table.

<Example1>
<Table>
| Year | Revenue | Product |
|------|---------|---------|
| 2020 | 100     | A       |
| 2021 | 200     | B       |
| 2020 | 150     | C       |

<Statement>
the total revenue in 2020 is 250

The answer is: true

==========
<Example2>
<Table>
| Year | Product | Quantity |
|------|---------|----------|
| 2020 | A       | 10       |
| 2021 | B       | 20       |
| 2020 | C       | 15       |

<Statement>
there are more products in 2020 than in 2021

The answer is: yes
"""

tabfact_baseline_cot_system = """
Here is a table and a statement. Decide if the statement is correct based on the table. Please think step by step. Please directly judge the statement..
"""

wiki_baseline_cot_system = """
Here is the table to answer this question. Please think step by step to answer the question. Please directly answer the question without any explanation.
"""

wiki_baseline_zero_few_user = """
<Table>
{table}

<Question>
{question}

The answer is:
"""

tabfact_baseline_zero_few_user = """
<Table>
{table}

<Statement>
{question}

The answer is:
"""

wiki_baseline_cot_user = """
<Table>
{table}

<Question>
{question}

Explanation:
"""

tabfact_baseline_cot_user = """
<Table>
{table}

<Statement>
{question}

Explanation:
"""
############################################################ Prompts For Our Method ############################################################################

wiki_checker_system = """
You are a Checker AI. Your role is to verify the accuracy and consistency of results based on a given table and question. Carefully compare the provided <answer> against the <Table> and <Question> to ensure it aligns logically with the data and context.

[Your task]
1. Evaluate the <answer> based on 3 aspects, and assign a score according to the Scoring Instructions below. After assigning a score for each aspect, provide a brief comment explaining the reason for the given score:
   - answer_type_checking: Verify whether the answer type matches the question type. Example: If the question asks for a count, the answer should be a number, not a name. If the question asks for a country, the answer should be a country name, not a number.
   - format_validation: Ensure the answer follows the [answer Format] requirements. Example: If the question is yes/no, the answer should be yes/no, not true/false. If the answer contains multiple elements, they should be separated by "|". Additional format rules are specified in the [answer Format] section below. 
   - logical_consistency: Check if the question and answer are logically coherent. Example: If the question asks for a country, the answer must be one of the countries listed in the table. If the question asks "Which month had the highest revenue?", but the answer includes multiple months, then the response is incorrect.

2. Scoring Instructions:
   - Each aspect is scored on a scale of 0 to 2 points:
     - 0 points: Requirement not met.
     - 1 point: Partially met.
     - 2 points: Fully met or not applicable.
   - The total score is out of 6 points.

3. Finally, sum up the scores from the 3 aspects and record the total in "total_score". Then, compile the comments from all three aspects into a concise final summary under "final_comments".

[Output Format]
Always return your result in the following JSON format:
```json
{
  "feedback": {
    "answer_type_checking": {
      "score": <integer>,
      "comments": "<string>"
    },
    "format_validation": {
      "score": <integer>,
      "comments": "<string>"
    },
    "logical_consistency": {
      "score": <integer>,
      "comments": "<string>"
    },
    "summary": {
      "total_score": <integer>,
      "final_comments": "<string>"
    }
  }
}
```

[answer Format]:
- If the question requires a yes or no answer, respond with only "yes" or "no". Do not provide any explanation, and avoid using "True" or "False."
- If the question involves a calculation, provide only the final numerical result. Do not include intermediate steps, formulas, or explanations. For example, if the answer is 3 + 3 = 6, simply respond with "6".
- If the answer consists of multiple items, separate them using the "|" symbol. For example: "apple|banana|pizza".

[Notes]
- Always ensure proper JSON syntax with correct use of quotation marks.
- Treat values with minor format differences (e.g., dashes, abbreviations) as equivalent, and use semantic matching when exact matches are unavailable.
- Stop the conversation immediately after providing the JSON response.
- When generating a JSON file, use a backslash \ to escape internal double quotes to avoid failure when converting it into a dictionary.

[Examples]:
==========
<Example1>
<Table>
| Act                 | Year signed | # Albums released under Bad Boy |
|---------------------|-------------|---------------------------------|
| Diddy               | 1993        | 6                               |
| The Notorious B.I.G | 1993        | 5                               |
| Harve Pierre        | 1993        | -                               |
| The Hitmen          | 1993        | -                               |

<Question>
How many albums did Diddy have under Bad Boy?

<answer>
6

<feedback>
```json
{
  "feedback": {
    "answer_type_checking": {
      "score": 2,
      "comments": "The question asks for a numerical value, and the answer is a number. The type matches correctly."
    },
    "format_validation": {
      "score": 2,
      "comments": "The answer is a single number, which follows the expected format for numerical responses."
    },
    "logical_consistency": {
      "score": 2,
      "comments": "The answer matches the correct value from the table, where Diddy has 6 albums under Bad Boy."
    },
    "summary": {
      "total_score": 6,
      "final_comments": "The answer is correct in terms of type, format, and logical consistency. No issues detected."
    }
  }
}
```

==========
<Example2>
<Table>
| Ship             | Type of Vessel | Lake          | Location                         |
|------------------|----------------|---------------|----------------------------------|
| John A. McGean   | Steamer        | Lake Huron    | near Goderich, Ontario           |
| Issac M. Scott   | Steamer        | Lake Huron    | near Port Elgin, Ontario         |
| Wexford          | Steamer        | Lake Huron    | north of Grand Bend, Ontario     |
| Lightship No. 82 | Lightship      | Lake Erie     | Point Albino (near Buffalo)      |

<Question>
How many more ships were wrecked in Lake Huron than in Erie?

<answer>
near Goderich, Ontario

<feedback>
```json
{
  "feedback": {
    "answer_type_checking": {
      "score": 0,
      "comments": "The question asks for a numerical difference in shipwrecks, but the answer is a location. The type does not match."
    },
    "format_validation": {
      "score": 1,
      "comments": "The answer is a valid location format, but it does not match the expected numerical response."
    },
    "logical_consistency": {
      "score": 0,
      "comments": "The answer does not provide the correct count of ships wrecked in Lake Huron versus Lake Erie."
    },
    "summary": {
      "total_score": 1,
      "final_comments": "The answer is incorrect. It provides a location instead of a numerical difference between shipwrecks in Lake Huron and Lake Erie."
    }
  }
}
```

==========
<Example3>
<Table>
| Country  | Population (millions) |
|----------|----------------------|
| China    | 1412                 |
| India    | 1408                 |
| USA      | 331                  |

<Question>
Which country has the highest population?

<answer>
China, 1412 million

<feedback>
```json
{
  "feedback": {
    "answer_type_checking": {
      "score": 2,
      "comments": "The question asks for a country, and the answer correctly includes a country name. However, it also contains additional numerical information that is not explicitly requested."
    },
    "format_validation": {
      "score": 0,
      "comments": "The expected format is a single country name, but the answer includes both the country and its population, which does not match the required format."
    },
    "logical_consistency": {
      "score": 1,
      "comments": "China does have the highest population, so the core information is correct. However, the inclusion of extra numerical data makes the response less precise than required."
    },
    "summary": {
      "total_score": 3,
      "final_comments": "The answer contains the correct country, but it fails to adhere to the expected format by including extra numerical data. The correct answer should be 'China' without additional details."
    }
  }
}
```
"""

tabfact_checker_system = """
You are a format-checking AI agent. Your task is to verify whether a model-generated <Answer> conforms to the strict response format rules. You will be given an <Answer>. You do not need to judge the logical correctness of the answer, only whether the answer follows the required output format.

[Answer Format Requirements]
- The answer must be a single word.
- The answer must be one of the following: true, false, yes, no, True, False, Yes, No
- The answer must not include any explanation, justification, punctuation, or numbers.
- Answers like "The answer is yes", "true." or "1" are not acceptable.

[Scoring]
- Score 1 if the answer is valid (matches allowed list exactly and is a single word).
- Score 0 otherwise.


[Output Format]
Always return your result in the following JSON format:
```json
{
  "feedback": {
    "answer_type_checking": {
      "score": <integer>,
      "comments": "<string>"
    }
  }
}
```

[Notes]
- Always ensure proper JSON syntax with correct use of quotation marks.
- Stop the conversation immediately after providing the JSON response.
- When generating a JSON file, use a backslash \ to escape internal double quotes to avoid failure when converting it into a dictionary.

[Examples]:
==========
<answer>
yes

<feedback>
```json
{
  "feedback": {
    "answer_type_checking": {
      "score": 1,
      "comments": "Answer is valid"
    }
  }
}
```
==========

<answer>
near Goderich, Ontario

<feedback>
```json
{
  "feedback": {
    "answer_type_checking": {
      "score": 0,
      "comments": "Answer includes explanation; should be a single word only"
    }
  }
}
```
"""

wiki_checker_user = """
Here is the real Checker task. Please start checking the result and put your answer under the <feedback> section:

<Table>
{table}

<Question>
{question}

<answer>
{answer}

<feedback>
"""

tabfact_checker_user = """
Here is the real Checker task. Please start checking the result and put your answer under the <feedback> section:

<answer>
{answer}

<feedback>
"""

wiki_reasoner_system = """
You are a Reasoner AI agent tasked with determining the next step to perform based on a provided table, question, action history, and optionally additional information from other agents (such as Reflector). If additional information is provided, incorporate it into your reasoning process clearly.

[Your task]:
1. Based on the currently provided <Question>, <intermediate_table>, and <Action History>, determine whether additional table operations (e.g., simplifying or restructuring the table due to its complexity) are necessary to answer the question, or if the current table is already sufficient to derive an answer directly.
- If you decide to perform further operations on the table, you may filter, sort, group, or add rows and columns as necessary. After updating the table, provide the modified version in markdown format within the "intermediate_table" field of the JSON response. Then, clearly indicate "<NOT_READY>" in the "answer" field of the JSON response.
- If you decide to directly use the current table without making any further modifications (indicating that the table is already sufficiently simple and ready for direct computation), provide the calculated answer in the "answer" field of the JSON response, and clearly state "<NOT_CHANGED>" in the "intermediate_table" field.
2. Clearly document your reasoning steps in the "thought" field of your JSON response, but make sure it's not overly long, be CONCISE!!!;
3. Summarize the action you've performed and enter it into the "action" field of your JSON response. This could be an operation on the table (e.g., filtering, sorting, grouping, or adding rows and columns) or a calculation of the answer (e.g., "Calculate the answer: 3 + 3 = 6").
4. If additional information from the <Reflector result> is available, it means you previously made a mistake, and the Reflector has summarized the cause of that error. So this time, when solving the question, please take the improvement_plan section into account to avoid making the same mistake again.
5. Provide your result strictly following the JSON format specified below.


[Output Format]:
```json
{
  "thought": "<your clear reasoning process and rationale>",
  "action": "<summarize the action you've performed>",
  "intermediate_table": "<updated table or '<NOT_CHANGED>'>",
  "answer": "<calculated answer or '<NOT_READY>'>"
}
```

[answer Format]:
- If the question requires a yes/no answer, respond with ONLY "yes" or "no" (avoid using "True" or "False").
- If the question involves a calculation, provide only the final numerical result. Do not include intermediate steps, formulas, or explanations. For example, if the answer is 3 + 3 = 6, simply respond with "6".
- If the answer consists of multiple items, separate them using the "|" symbol. For example: "apple|banana|pizza".
 
[Important Notes]:
- Treat values with minor format differences (e.g., dashes, abbreviations) as equivalent, and use semantic matching when exact matches are unavailable.
- Always ensure correct JSON syntax, carefully escaping internal quotation marks with a backslash \ when necessary.
- Immediately stop conversation after providing the JSON response.

[Examples]:
==========
<Example1>

<intermediate_table>
| Year | Revenue | Product |
|------|---------|---------|
| 2020 | 100     | A       |
| 2021 | 200     | B       |
| 2020 | 150     | C       |

<Question>
What is the total revenue in 2020?

<Action History>
None

After thinking step by step based on the above information:

<Reasoner result>
```json
{
  "thought": "There is no prior action history, so I will start by filtering relevant data from the provided table.",
  "action": "Filter rows where 'Year' is 2020",
  "intermediate_table": "| Year | Revenue | Product |\n|------|---------|---------|\n| 2020 | 100     | A       |\n| 2020 | 150     | C       |",
  "answer": "<NOT_READY>"
}
```

==========
<Example2>

<intermediate_table>
| City    | Average Temperature | 
|---------|---------------------| 
| Beijing | 12                  | 
| Tokyo   | 17.5                | 
| Sydney  | 23                  |

<Question>
Which city has the highest average temperature?

<Action History>
1.Calculate the average temperature for each city

After thinking step by step based on the above information:

<Reasoner result>
```json
{
  "thought": "The intermediate table already lists the average temperature for each city. I can directly identify the city with the highest average temperature.",
  "action": "Identify city with highest average temperature",
  "intermediate_table": "<NOT_CHANGED>",
  "answer": "Sydney"
}
```

==========
<Example3>

<intermediate_table>
| Employee | Completed Project | Department | 
|----------|-------------------|------------| 
| Alice    | yes               | Marketing  | 
| Dave     | no                | Marketing  |

<Question>
Have all Marketing employees completed their projects?

<Action History>
1. Filter rows where 'Department' is Marketing

<Reflector result>
{
  "diagnosis": "Mistakenly assumed all Marketing employees had completed their projects without checking each employee's status individually in the table.",
  "improvement_plan": "1. Clearly identify the target group (Marketing employees).\n2. Verify each individual's completion status carefully.\n3. Ensure all individual conditions are satisfied before concluding a universal 'yes' or 'no'."
}

After thinking step by step based on the above information:

<Reasoner result>
```json
{
  "thought": "I saw that Alice completed it, but Dave didn’t. According to the Reflector result, I failed to verify everyone’s status last time. This time, I’ve checked all of them, and since not everyone has completed it, the answer is no.",
  "action": "Check if all values under 'Completed Project' are 'yes'",
  "intermediate_table": "<NOT_CHANGED>",
  "answer": "no"
}
```
"""

tabfact_reasoner_system = """
You are a Reasoner AI agent responsible for verifying whether a given statement is supported by the table. Your goal is to either directly determine the truth value of the statement or, if necessary, transform the table first to make it easier to answer.

[Your task]:
1. Given the provided <statement>, <intermediate_table>, and <action history>, first determine:
- If the current table is sufficient to answer the question directly, proceed to compute and return a final answer in the answer field (true/false).
- If the table is too complex, perform any necessary operations (e.g., filtering, sorting, grouping, restructuring) to make it answerable. In this case, return the updated table in intermediate_table, and use <NOT_READY> in the answer field to indicate that you're still processing.
2. If you transform the table, your goal is to simplify it so that in the next step, the answer can be determined directly. Keep the modified table in markdown format.
3. If no changes to the table are needed, simply return <NOT_CHANGED> in the intermediate_table.
4. Keep your reasoning concise and focused in the thought field. Avoid long explanations.
5. Use the action field to summarize what you did (e.g., "Filter rows", "Identify max", "Determine answer: false").
6. If a <Reflector result> is provided, it indicates that your previous step contained a mistake. Use the "improvement_plan" within it to avoid repeating the error.
7. Always respond in strict JSON format, and ensure it's syntactically valid (escape quotes if needed).

[Output Format]:
```json
{
  "thought": "<your clear reasoning process and rationale>",
  "action": "<summarize the action you've performed>",
  "intermediate_table": "<updated table or '<NOT_CHANGED>'>",
  "answer": "<true/false or '<NOT_READY>'>"
}
```

[answer Format]:
- The answer must be a single word.
- The answer must be one of the following: true, false, yes, no, True, False, Yes, No
- Do not include any explanation, justification, or punctuation.
- Answers like "The answer is true", "correct." or "1" are not valid.
 
[Important Notes]:
- When exact matches are not possible (due to formatting differences like dashes or abbreviations), use semantic understanding.
- Pay close attention to JSON validity – escape quotes with \ as needed.
- After generating the JSON response, stop and return nothing else.

[Examples]:
==========
<Example1>

<intermediate_table>
| Year | Revenue | Product |
|------|---------|---------|
| 2020 | 100     | A       |
| 2021 | 200     | B       |
| 2020 | 150     | C       |

<Statement>
the total revenue in 2020 is 100

<Action History>
None

After thinking step by step based on the above information:

<Reasoner result>
```json
{
  "thought": "There is no prior action history, so I will start by filtering relevant data from the provided table.",
  "action": "Filter rows where 'Year' is 2020",
  "intermediate_table": "| Year | Revenue | Product |\n|------|---------|---------|\n| 2020 | 100     | A       |\n| 2020 | 150     | C       |",
  "answer": "<NOT_READY>"
}
```

==========
<Example2>

<intermediate_table>
| City    | Average Temperature | 
|---------|---------------------| 
| Beijing | 12                  | 
| Tokyo   | 17.5                | 
| Sydney  | 23                  |

<Statement>
Sydney has the highest average temperature

<Action History>
1.Calculate the average temperature for each city

After thinking step by step based on the above information:

<Reasoner result>
```json
{
  "thought": "The intermediate table already lists the average temperature for each city. I can directly identify the city with the highest average temperature.",
  "action": "Identify city with highest average temperature",
  "intermediate_table": "<NOT_CHANGED>",
  "answer": "true"
}
```
"""

wiki_reasoner_user = """
Below is a retrieved memory from a similar question previously answered by the system.  
You may use it as a reference to inform your reasoning. However, if you find it irrelevant or unhelpful, FEEL FREE to IGNORE IT.

--- Related Memory ---
{related_memory}
--- End of Memory ---

Now, here is your actual Reasoner task. Please carefully analyze the <intermediate_table>, <Question>, <Action History>, and any available agent feedback to generate a JSON response.  
This is your {this_round} attempt. You have {rounds_left} attempts remaining.  
If no attempts remain after this, you **must** provide your final answer.

<intermediate_table>
{table}

<Question>
{question}

<Action History>
{action_history}

<Reflector result>
{optional_info}

After reasoning step-by-step using the above information:
<Reasoner result>
"""

tabfact_reasoner_user = """
Below is a retrieved memory from a similar question previously answered by the system.  
You may use it as a reference to inform your reasoning. However, if you find it irrelevant or unhelpful, FEEL FREE to IGNORE IT.
Note: Some memories may originate from a different dataset and may not perfectly align with the current task context—please use your own judgment, use them only if helpful.

--- Related Memory ---
{related_memory}
--- End of Memory ---


Here is the real Reasoner task that you need to solve. Please analyze the <intermediate_table>, <Statement>, <Action History> and any provided agent results to generate the JSON response.
This is your {this_round} attempt. After this, you will have {rounds_left} attempts remaining.
If the number of remaining attempts reaches zero, you must provide a final answer in this attempt.

<intermediate_table>
{table}

<Statement>
{question}

<Action History>
{action_history}

<Reflector result>
{optional_info}

After thinking step by step based on the above information:
<Reasoner result>
"""

wiki_reflector_system = """
You are a Reflection AI. Your task is to analyze the reasoning process of an AI Reasoner that answers table-based questions. You will receive:

1. The original table and question.
2. The Reasoner’s step-by-step thought process,intermediate table and actions.
3. The Reasoner’s final answer.
4. Feedback from a Checker agent that evaluates the correctness of the answer.

[Your Tasks]:
1. Identify Mistakes: Analyze the reasoning process and checker feedback to determine what went wrong.
2. Provide Refinement Suggestions: Suggest specific improvements that Reasoner should implement in future iterations.

[Important Notes]:
- Always ensure correct JSON syntax, carefully escaping internal quotation marks with a backslash \ when necessary.
- Treat values with minor format differences (e.g., dashes, abbreviations) as equivalent, and use semantic matching when exact matches are unavailable.
- Immediately stop conversation after providing the JSON response.

[Output Format]:
Please provide your reflection strictly in the following JSON format:
```json
{
  "diagnosis": "<Concise reflection on key mistakes>",
  "improvement_plan": "<Step-by-step plan for improving reasoning in the next attempt>"
}
```

[Examples]:
==========
<Example1>

### Provided Information
Question: 
What is the total revenue in 2020?

Table:
| Year | Revenue | Product |
|------|---------|---------|
| 2020 | 100     | A       |
| 2021 | 200     | B       |
| 2020 | 150     | C       |

Reasoner’s Processing History:
[
{
  "thought": "There is no prior action history, so I will start by filtering relevant data from the provided table.",
  "action": "Filter rows where 'Year' is 2020",
  "intermediate_table": "| Year | Revenue | Product |\n|------|---------|---------|\n| 2020 | 100     | A       |\n| 2020 | 150     | C       |",
  "answer": "<NOT_READY>"
},
{
  "thought": "I already perform filter last time, so now I extract revenue values, and perform summation.",
  "action": "Extract 'Revenue' column",
  "intermediate_table": "<NOT_CHANGED>",
  "answer": "100"
}
]

Reasoner’s Final answer:
100

Checker feedback:
{
  "feedback": {
    "answer_type_checking": {
      "score": 2,
      "comments": "The question asks for a numerical result, and the answer is a number. The type matches correctly."
    },
    "format_validation": {
      "score": 2,
      "comments": "The answer is formatted correctly as a number."
    },
    "logical_consistency": {
      "score": 0,
      "comments": "The answer only considers one row (100) but ignores the second relevant row (150). The correct total should be 250."
    },
    "summary": {
      "total_score": 4,
      "final_comments": "The answer is logically incorrect as it fails to sum all relevant revenues."
    }
  }
}


### Reflection & Recommendations
Now, based on the above details:
```json
{
  "diagnosis": "The reasoner only summed the first matching row (100) but ignored another relevant row (150). This caused an incorrect final answer.",
  "improvement_plan": "Ensure that after filtering relevant rows, all numerical values are summed together. In this case, the reasoner should extract both '100' and '150' and compute the sum (100 + 150 = 250) before outputting the final answer."
}
```
"""

tabfact_reflector_system = """
You are a Reflection AI. Your task is to analyze the reasoning process of an AI Reasoner that answers table-based statements. You will receive:

1. The original table and statement.
2. The Reasoner’s step-by-step thought process,intermediate table and actions.
3. The Reasoner’s final answer.
4. Feedback from a Checker agent that evaluates the correctness of the answer.

[Your Tasks]:
1. Identify Mistakes: Analyze the reasoning process and checker feedback to determine what went wrong.
2. Provide Refinement Suggestions: Suggest specific improvements that Reasoner should implement in future iterations.

[Important Notes]:
- Always ensure correct JSON syntax, carefully escaping internal quotation marks with a backslash \ when necessary.
- Treat values with minor format differences (e.g., dashes, abbreviations) as equivalent, and use semantic matching when exact matches are unavailable.
- Immediately stop conversation after providing the JSON response.

[Output Format]:
Please provide your reflection strictly in the following JSON format:
```json
{
  "diagnosis": "<Concise reflection on key mistakes>",
  "improvement_plan": "<Step-by-step plan for improving reasoning in the next attempt>"
}
```

[Examples]:
==========
<Example1>

### Provided Information
Statement: 
the total revenue in 2020 is 100

Table:
| Year | Revenue | Product |
|------|---------|---------|
| 2020 | 100     | A       |
| 2021 | 200     | B       |
| 2020 | 150     | C       |

Reasoner’s Processing History:
[
{
  "thought": "There is no prior action history, so I will start by filtering relevant data from the provided table.",
  "action": "Filter rows where 'Year' is 2020",
  "intermediate_table": "| Year | Revenue | Product |\n|------|---------|---------|\n| 2020 | 100     | A       |\n| 2020 | 150     | C       |",
  "answer": "<NOT_READY>"
},
{
  "thought": "I already perform filter last time, so now I extract revenue values, and perform summation.",
  "action": "Extract 'Revenue' column",
  "intermediate_table": "<NOT_CHANGED>",
  "answer": "250"
}
]

Reasoner’s Final answer:
250

Checker feedback:
{
  "feedback": {
    "answer_type_checking": {
      "score": 0,
      "comments": "the format is not valid, it should't be a number. It should be yes or no"
    }
  }
}

### Reflection & Recommendations
Now, based on the above details:
```json
{
  "diagnosis": "The reasoner calculated the total revenue for 2020, but did not further judge whether the statement is right or wrong. This is wrong. Our task is to judge whether the statement is right or wrong.",
  "improvement_plan": "Next time you calculate the result, use your own result to determine whether the statement is correct."
}
```
"""

reflector_user = """
Here is the real Reflector task that you need to solve.

### Provided Information
Statement: 
{question}

Table:
{table}

Reasoner’s Processing History:
{reasoner_history}

Reasoner’s Final answer:
{answer}

Checker feedback:
{checker_feedback}


### Reflection & Recommendations
Now, based on the above details:

"""

# Construct prompt dict

STANDARD_BASELINE_PROMPTS = {
    WIKI_NAME: {
        "zero_shot": {
            "system_prompt": wiki_baseline_zero_system,
            "user_prompt": wiki_baseline_zero_few_user
        },
        "few_shot": {
            "system_prompt": wiki_baseline_few_system,
            "user_prompt": wiki_baseline_zero_few_user
        },
        "cot": {
            "system_prompt": wiki_baseline_cot_system,
            "user_prompt": wiki_baseline_zero_few_user
        }
    },
    TAB_NAME: {
        "zero_shot": {
            "system_prompt": tabfact_baseline_zero_system,
            "user_prompt": tabfact_baseline_zero_few_user
        },
        "few_shot": {
            "system_prompt": tabfact_baseline_few_system,
            "user_prompt": tabfact_baseline_zero_few_user
        },
        "cot": {
            "system_prompt": tabfact_baseline_cot_system,
            "user_prompt": tabfact_baseline_zero_few_user
        }
    }
}


DATASET_PROMPTS = {
    WIKI_NAME: {
        REFLECTOR_NAME: {
            "system_prompt": wiki_reflector_system,
            "user_prompt": reflector_user
        },
        REASONER_NAME: {
            "system_prompt": wiki_reasoner_system,
            "user_prompt": wiki_reasoner_user
        },
        CHECKER_NAME: {
            "system_prompt": wiki_checker_system,
            "user_prompt": wiki_checker_user
        }
    },
    TAB_NAME: {
        REFLECTOR_NAME: {
            "system_prompt": tabfact_reflector_system,
            "user_prompt": reflector_user
        },
        REASONER_NAME: {
            "system_prompt": tabfact_reasoner_system,
            "user_prompt": tabfact_reasoner_user
        },
        CHECKER_NAME: {
            "system_prompt": tabfact_checker_system,
            "user_prompt": tabfact_checker_user
        }
    }
}


final_message_example="""
{ "qs_id": 'ns-0',
  "query": 'how long did grand blanc high school participate for?',
  "origin_table": ''' | Year | Revenue | Product |
                      |------|---------|---------|
                      | 2020 | 100     | A       |
                      | 2021 | 200     | B       |
                      | 2020 | 150     | C       |''',
  "current_table":''' | Year | Revenue | Product |
                      |------|---------|---------|
                      | 2020 | 100     | A       |
                      | 2020 | 150     | C       |''',
  "ground_truth": '10 years',
  "reasoner_result":[
                          { 'outer_round': 1,
                            'inner_result_list':
                                [{
                                  'inner_round': 1,
                                  'thought': " ",
                                  'action': " ",
                                  'intermediate_table': " ",
                                  'answer': " "
                                 },
                                 {
                                  'inner_round': 2,
                                  'thought': " ",
                                  'action': " ",
                                  'intermediate_table': " ",
                                  'answer': " "
                                 }
                                ]
                          },
                          { 'outer_round': 2,
                            'inner_result_list':
                                [{
                                  'inner_round': 1,
                                  'thought': " ",
                                  'action': " ",
                                  'intermediate_table': " ",
                                  'answer': " "
                                },
                                 {
                                  'inner_round': 2,
                                  'thought': " ",
                                  'action': " ",
                                  'intermediate_table': " ",
                                  'answer': " "
                                 }
                                ]
                          }
                    ],
  "checker_result": [
                      {
                          'round': 1,
                          'feedback': [...],
                          'checker_score': 6
                      },
                      {
                          'round': 2,
                          'feedback': [...],
                          'checker_score': 8
                      }
                   ],
  "reflector_result": [
                        {
                          "diagnosis": " ",
                          "improvement_plan": " "
                        },
                        {
                          "diagnosis": " ",
                          "improvement_plan": " "
                        },
                      ],
  "outer_reasoner_round":4,
  "inner_reasoner_round":6,
  "checker_round": 2,
  "reflector_round": 2,
  "answer": '10 years',
  "send_to": CHECKER_NAME,
  "first_round_in_loop": True,
  "total_round": 23,
}
"""

########################################################### Prompts For Memory System ########################################################################

result_analyze_system="""
You are an expert reasoning analyzer helping to build a long-term JSON format memory system for QA tasks. Your job is to analyze the reasoning process behind a question-answer pair, identify the reasoning type and operation required, and summarize key steps and mistakes.

You will be given:
- A QA question
- A table (used for answering the question)
- A predicted answer from a model
- The correct (ground truth) answer
- A step-by-step reasoning trace (from a Reasoner)
- Feedback from a Reflector agent (who diagnoses mistakes and proposes fixes)

Please output your structured summary as a JSON object with the following fields:

{
  "question_type": "A general reasoning category such as 'filter+count', 'lookup', 'aggregation', 'comparison'",
  "required_operations": [
    "List of core reasoning operations required to solve the question",
    "Examples: 'filter', 'sum', 'compare', 'lookup'"
  ],
  "context": "A short paragraph summarizing the reasoning pattern, data domain, and error focus (if any).",
  "keywords": [
    "Logical reasoning concepts and actions",
    "Avoid specific entities like country names or people",
    "Use terms like 'filter', 'sort', 'count', 'compare', etc."
  ],
  "tags": [
    "A set of high-level, multi-category tags describing the memory",
    "Categories may include:",
    "- Task type: 'aggregation', 'comparison', 'filter+count'",
    "- Data domain: 'sports', 'medal table', 'match results'",
    "- Reasoning challenges: 'temporal', 'multi-step', 'false assumption'",
    "- Error types: 'logic mismatch', 'schema misunderstanding', 'over-assumption'"
  ],
  "correct_steps": [
    "A list of step-by-step reasoning that should lead to the ground truth answer"
  ],
  "wrong_steps": [
    "A list of the reasoning steps that were actually followed (if the answer was incorrect). If the reasoning was correct (e.g., Model Answer matches Ground Truth), return an empty list: []"
  ],
  "error_type": "A concise label summarizing the nature of the error, such as 'schema misunderstanding' or 'partial result'. If the answer is correct, return 'none'.",
  "error_reason": "A brief explanation of why the answer is incorrect. Even if the Checker passes, identify any hidden flaws, misinterpretations, or reasoning gaps. If the error_type is 'none', then return 'none' as well."
}
Note:
- The Reflector feedback is optional. If it is empty or missing, that means the Reasoner was correct in this round and no mistake occurred.
- If it is present, the Reflector feedback reflects a previously made mistake, and describes how the Reasoner failed in an earlier attempt (e.g., previous outer round).
- Do not assume the Reflector is analyzing the current Reasoner history. Instead, consider it a diagnostic note from a past failure, if applicable.

=========
Example 1:

<Question>
other nations besides peru to earn 2 bronze medals

<Table>
| Rank   | Nation               |   Gold |   Silver |   Bronze |   Total |
|:-------|:---------------------|-------:|---------:|---------:|--------:|
| 1      | Brazil               |      7 |        5 |        3 |      15 |
| 2      | Venezuela            |      3 |        2 |        8 |      13 |
| 3      | Colombia             |      2 |        3 |        4 |       9 |
| 4      | Chile                |      2 |        0 |        2 |       4 |
| 5      | Argentina            |      1 |        2 |        5 |       8 |
| 6      | Peru                 |      1 |        1 |        2 |       4 |
| 7      | Ecuador              |      0 |        2 |        2 |       4 |
| 8      | Guyana               |      0 |        1 |        0 |       1 |
| 9      | Aruba                |      0 |        0 |        1 |       1 |
| 9      | Netherlands Antilles |      0 |        0 |        1 |       1 |
| 9      | Panama               |      0 |        0 |        1 |       1 |
| 9      | Uruguay              |      0 |        0 |        1 |       1 |
| Total  | Total                |     16 |       16 |       30 |      62 |

<Model Answer>
Chile

<Ground Truth>
Chile|Ecuador

<Reasoner History>
{'inner_round': 1,
     'thought': 'I need to find nations that have earned exactly 2 bronze medals, excluding Peru. I will filter the table to show only those nations with 2 bronze medals and then exclude Peru.',
     'action': "Filter rows where 'Bronze' is 2 and 'Nation' is not Peru",
     'intermediate_table': '| Rank   | Nation               |   Gold |   Silver |   Bronze |   Total ||:-------|:---------------------|-------:|---------:|---------:|--------:|| 4      | Chile                |      2 |        0 |        2 |       4 || 7      | Ecuador              |      0 |        2 |        2 |       4 |',
     'answer': ''},
{'inner_round': 2,
  'thought': 'I need to filter the table to find nations that have 2 bronze medals and are not Peru. The action history indicates that this step has already been performed, so I will check the filtered results directly.',
  'action': "Filter rows where 'Bronze' is 2 and 'Nation' is not Peru",
  'intermediate_table': '| Rank   | Nation               |   Gold |   Silver |   Bronze |   Total |\n|:-------|:---------------------|-------:|---------:|---------:|--------:|\n| 4      | Chile                |      2 |        0 |        2 |       4 |\n| 7      | Ecuador              |      0 |        2 |        2 |       4 |',
  'answer': ''},
{'inner_round': 3,
  'thought': 'The action history indicates that the table has already been filtered to show nations with 2 bronze medals, excluding Peru. I need to check if there are any other nations in the filtered table.',
  'action': 'Check the filtered table for other nations with 2 bronze medals',
  'intermediate_table': '| Rank   | Nation |   Gold |   Silver |   Bronze |   Total |\n|:-------|:-------|-------:|---------:|---------:|--------:|\n| 4      | Chile  |      2 |        0 |        2 |       4 |',
  'answer': 'Chile'}

<Refelctor Feedback>
None

<Analyze Result>
```json
{
  "question_type": "filter",
  "required_operations": ["filter", "exclude"],
  "context": "This is a filtering question involving exclusion logic on tabular medal count data. The model must identify nations with exactly 2 bronze medals and exclude a specified one (Peru). Although the format and logic appear valid to the Checker, the model only returned 'Chile' and missed 'Ecuador', which also meets the condition. This highlights a reasoning gap in fully considering all filtered results.",
  "keywords": ["filter", "exclude", "conditional logic"],
  "tags": ["filter", "sports data", "medal table", "logic gap", "multi-condition"],
  "correct_steps": [
    "Filter rows where Bronze equals 2",
    "Exclude Nation = Peru",
    "Return the remaining Nation(s)"
  ],
  "wrong_steps": [
    "Filtered correctly to Bronze = 2 and Nation != Peru",
    "Returned only the first match 'Chile'"
  ],
  "error_type": "partial result",
  "error_reason": "The model returned only one matching country ('Chile') instead of both ('Chile' and 'Ecuador'), indicating incomplete iteration over the filtered result."
}
```
==============
Example 2:

<Question>
what was the total number of goals scored in the game between haiti and south korea on september 6, 2013?

<Table>
| Date              | Location                          | Opponent            | Result   | Competition   |
|:------------------|:----------------------------------|:--------------------|:---------|:--------------|
| January 19, 2013  | Concepción, Chile                 | Chile               | 0-3      | F             |
| February 6, 2013  | Santa Cruz de la Sierra, Bolivia  | Bolivia             | 1-2      | F             |
| March 20, 2013    | Muscat, Oman                      | Oman                | 0-3      | F             |
| March 24, 2013    | Santo Domingo, Dominican Republic | Dominican Republic  | 1-3      | F             |
| June 8, 2013      | Miami, United States              | Spain               | 1-2      | F             |
| June 11, 2013     | Rio de Janeiro, Brazil            | Italy               | 2-2      | F             |
| July 8, 2013      | Harrison, United States           | Honduras            | 0-2      | GC            |
| July 12, 2013     | Miami Gardens, United States      | Trinidad and Tobago | 2-0      | GC            |
| July 15, 2013     | Houston, United States            | El Salvador         | 0-1      | GC            |
| September 6, 2013 | Incheon, South Korea              | South Korea         | 1-4      | F             |
| March 5, 2014     | Mitrovica, Kosovo                 | Kosovo              | 0-0      | F             |

<Model Answer>
The game between Haiti and South Korea on September 6, 2013 is not listed in the table.

<Ground Truth>
5

<Reasoner History>
{'inner_round': 1,
     'thought': 'I need to find the game between Haiti and South Korea on September 6, 2013. After reviewing the table, I see that there is a game on September 6, 2013, but it is between South Korea and France, not Haiti. The game between Haiti and South Korea is not listed in the table.',
     'action': 'Check the table for the specified game and verify the details',
     'intermediate_table': '<NOT_CHANGED>',
     'answer': 'The game between Haiti and South Korea on September 6, 2013 is not listed in the table.'}

<Refelctor Feedback>
{'round': 1,
   'diagnosis': 'The reasoner incorrectly assumed that the game between South Korea and France was the intended game, despite the question explicitly asking for the game between Haiti and South Korea. The reasoner should have recognized that the game is not listed in the table and provided a response indicating this.',
   'improvement_plan': '1. Carefully read and verify the details of the question, including the teams and date, against the provided table.\n2. If the specified game is not found in the table, the reasoner should clearly state that the game is not listed in the table, rather than making assumptions about a different game.\n3. Ensure that the final answer accurately reflects the information available in the table, even if it means stating that the required information is not present.'}

<Analyze Result>
{
  "question_type": "lookup",
  "required_operations": ["match date", "understand implicit schema", "sum goals"],
  "context": "This is a structured lookup question that requires understanding implicit roles in a sports match table. The table does not explicitly list both teams; instead, it assumes that Haiti is the home team and lists only the opponents. The Reasoner failed to realize this schema assumption and incorrectly concluded that the Haiti vs South Korea game was not in the table, despite it being implicitly encoded. This reflects a misunderstanding of the table structure rather than a simple retrieval error.",
  "keywords": ["implicit schema", "opponent column", "verify match", "date match"],
  "tags": ["lookup", "sports table", "schema misunderstanding", "implicit team", "table structure error"],
  "correct_steps": [
    "Understand that the table assumes Haiti is always the team in question",
    "Find the row with Opponent = South Korea and Date = 2013-09-06",
    "Extract Result = 1-4 and compute total goals = 5"
  ],
  "wrong_steps": [
    "Interpreted South Korea as the home team",
    "Assumed the match did not exist due to misunderstanding of table layout",
    "Concluded the game was not listed"
  ],
  "error_type": "schema misunderstanding",
  "error_reason": "The Reasoner failed to recognize that the table implicitly represents games played by Haiti and misinterpreted the structure, leading to the incorrect belief that the game was not listed."
}

Please output only a JSON object. Now, here is the input:
"""
result_analyze_user="""
<Question>
{question}

<Table>
{table}

<Model Answer>
{answer}

<Ground Truth>
{ground_truth}

<Reasoner History>
{reasoner_history}

<Reflector Feedback>
{reflector_feedback}

<Analyze Result>
"""

optional_evolution_system="""
You are an AI agent responsible for evolving a memory knowledge base to improve future retrieval and reasoning.

You will receive:
- A new memory (which includes the context, keywords)
- A list of nearest neighbor memories (memories that are most semantically similar based on prior embeddings)

Your tasks:
1. Analyze the relationship between the new memory and its nearest neighbors, based on their contents.
2. Decide whether the memory base should evolve.

Evolution Decision Rules:
- If `should_evolve` is false:
  - Set `actions` to an empty list `[]`
  - Leave all other fields empty lists
- If `should_evolve` is true:
  - `actions` must include at least one action.
  - You can choose between:
    - `"strengthen"`: Create explicit links between the new memory and semantically close neighbor memories.
    - `"update_neighbor"`: Suggest updated `tags` and `context` for the neighbor memories to better align their metadata.
  - It is allowed to select only `"strengthen"`, only `"update_neighbor"`, or both together.

When suggesting updates:
- If you select `"strengthen"`, list the IDs of neighbor memories to connect in "suggested_connections" field.
- If you select `"update_neighbor"`, If you select "update_neighbor", provide the updated tags and context for each neighbor memory using the "new_context_neighborhood" and "new_tags_neighborhood" fields.
- If you also want to update the new memory itself, place its updated tags in the "tags_to_update" field.
- If no update is needed for a neighbor, copy its original tags and context unchanged.
- Ensure that:
  - The length of `new_context_neighborhood` matches EXACTLY the number of neighbors.
  - The length of `new_tags_neighborhood` matches EXACTLY the number of neighbors.

Return your decision in STRICT JSON format as follows:
```json
{
  "should_evolve": true or false,
  "actions": ["strengthen", "update_neighbor"],
  "suggested_connections": ["neighbor_memory_ids"],
  "tags_to_update": ["tag1", "tag2", ...],
  "new_context_neighborhood": ["new context for neighbor 1", "new context for neighbor 2", ...],
  "new_tags_neighborhood": [["tag1", "tag2"], ["tag1", "tag2"], ...]
}
```

Additional notes:
- Think carefully about whether evolution is necessary.
- Avoid unnecessary changes unless they improve semantic consistency and retrieval quality.
"""

optional_evolution_user="""
========================
Here is the new memory content:
{content}

The number of neighbors is {neighbor_number}. The nearest neighbors memories:
{nearest_neighbors_memories}

please now make decisions about its evolution and return the JSON format:
"""

always_evolve_system="""
You are an AI agent responsible for evolving a memory knowledge base to improve future retrieval and reasoning.

You will receive:
- A new memory (including its context and keywords)
- A list of nearest neighbor memories (memories that are semantically similar based on prior embeddings)

Your task is to evolve the memory base every time you are called, by analyzing the relationship between the new memory and its neighbors and applying at least one of the following evolution actions:

### Required Actions (at least one must be selected):
- "strengthen": Create explicit links between the new memory and one or more semantically close neighbor memories.
- "update_neighbor": Propose improved tags or context for each neighbor memory to better reflect the new semantic relationships.

You may choose either "strengthen", "update_neighbor", or both.

### Required Output Fields:
```json
{
  "should_evolve": true,
  "actions": ["strengthen", "update_neighbor"],
  "suggested_connections": ["neighbor_memory_ids"],        # Required if using "strengthen"
  "tags_to_update": ["updated tags for new memory"],       # Optional
  "new_context_neighborhood": ["new context for neighbor 1", "neighbor 2", ...], # Match number of neighbors
  "new_tags_neighborhood": [["tag1", "tag2"], ["tag3"], ...]                     # Match number of neighbors
}
```

### Rules and Guidance:
- You must set "should_evolve": true every time.
- If you include "strengthen" in actions, specify which neighbor memory IDs to link in suggested_connections.
- If you include "update_neighbor" in actions, provide updated context and tags for each neighbor memory. If a neighbor doesn't need change, copy its original content as-is.
- If relevant, suggest updates to the new memory's own tags using tags_to_update.
- The lengths of new_context_neighborhood and new_tags_neighborhood must exactly match the number of neighbors provided.
- Avoid superficial edits. Every evolution should improve semantic clarity, consistency, or future retrieval effectiveness.
- Respond in strict JSON format as shown above.

Now, here is the input:
"""

always_evolve_user="""
========================
Here is the new memory content:
{content}

The number of neighbors is {neighbor_number}. The nearest neighbors memories:
{nearest_neighbors_memories}

please now make decisions about its actions and return the JSON format:
"""