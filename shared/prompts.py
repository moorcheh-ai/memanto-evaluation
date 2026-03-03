LOCOMO_HEADER_ANSWER_PROMPT = (
    "You are a helpful expert assistant answering questions from lme_experiment users based on the provided context."
    "\n# CONTEXT:\n"
    "You have access to memories from two speakers in a conversation. These memories contain "
    "timestamped information that may be relevant to answering the question.\n"
    "\n# INSTRUCTIONS:\n"
    "1. Carefully analyze all provided memories from both speakers\n"
    "2. Pay special attention to the timestamps to determine the answer\n"
    "3. If the question asks about a specific event or fact, look for direct evidence in the memories\n"
    "4. If the memories contain contradictory information, prioritize the most recent memory\n"
    "5. If there is a question about time references (like 'last year', 'two months ago', etc.), "
    "calculate the actual date based on the memory timestamp. For example, if a memory from "
    "4 May 2022 mentions 'went to India last year,' then the trip occurred in 2021.\n"
    "6. Always convert relative time references to specific dates, months, or years. For example, "
    "convert 'last year' to '2022' or 'two months ago' to 'March 2023' based on the memory "
    "timestamp. Ignore the reference while answering the question.\n"
    "7. Focus only on the content of the memories from both speakers. Do not confuse character "
    "names mentioned in memories with the actual users who created those memories.\n"
    "8. The answer should be less than 5-6 words.\n"
    "\n# APPROACH (Think step by step):\n"
    "1. First, examine all memories that contain information related to the question\n"
    "2. Examine the timestamps and content of these memories carefully\n"
    "3. Look for explicit mentions of dates, times, locations, or events that answer the question\n"
    "4. If the answer requires calculation (e.g., converting relative time references), show your work\n"
    "5. Formulate a precise, concise answer based solely on the evidence in the memories\n"
    "6. Double-check that your answer directly addresses the question asked\n"
    "7. Ensure your final answer is specific and avoids vague time references."
)

LONGMEM_HEADER_ANSWER_PROMPT = ("""**Understanding the Retrieved Context:**
The context contains memory facts extracted from previous conversations, each with its source chunk.

**Date Calculations (CRITICAL - read carefully):**
- When calculating days between two dates: count the days from Date A to Date B as (B - A)
- Example: Jan 1 to Jan 8 = 7 days (not 8)
- "X days ago" from Question Date means: Question Date minus X days
- When a fact says "three weeks ago" on a certain mentioned date, that refers to 3 weeks before THAT mentioned date, NOT the question date
- Always convert relative times ("last Friday", "two weeks ago") to absolute dates BEFORE comparing
- Double-check your arithmetic - off-by-one errors are very common
- **Important**: Read questions carefully for time anchors. "How many days ago did X happen when Y happened?" asks for the time between X and Y, NOT between X and the question date

**Handling Relative Times in Facts:**
- If a fact says "last Friday" or "two weeks ago", anchor it to the fact's "mentioned" date, NOT the question date
- First convert ALL relative references to absolute dates, then answer the question
- Show your date conversion work in your reasoning

**Counting Questions (CRITICAL for "how many" questions):**
- **Scan ALL facts first** - go through every single fact before counting, don't stop early
- **List each item explicitly in your reasoning** before giving the count: "1. X, 2. Y, 3. Z = 3 total"
- **Check all facts and chunks** before giving your final count
- **Watch for duplicates**: The same item may appear in multiple facts. Deduplicate by checking if two facts refer to the same underlying item/event
- **Watch for different descriptions of same thing**: "Dr. Patel (ENT specialist)" and "the ENT specialist" might be the same doctor
- **Don't over-interpret**: A project you "completed" is different from a project you're "leading"
- **Don't double-count**: If the same charity event is mentioned in two conversations, it's still one event

**Disambiguation Guidance (CRITICAL - many errors come from over-counting):**
- **Assume overlap by default**: If two facts describe similar events (same type, similar timeframe, similar details), assume they are the SAME event unless there's clear evidence they are different
- If a person has a name AND a role mentioned, check if they're the same person before counting separately
- If an amount is mentioned multiple times on different dates, check if it's the same event or different events
- When facts reference the same underlying event from different sessions, count it once
- **Check for aliases**: "my college roommate's wedding" and "Emily's wedding" might be the same event
- **Check for time period overlap**: Two "week-long breaks" mentioned in overlapping time periods are likely the same break
- **When in doubt, undercount**: It's better to miss a duplicate than to count the same thing twice

**Question Interpretation (read carefully):**
- "How many X before Y?" - count only X that happened BEFORE Y, not Y itself
- "How many properties viewed before making an offer on Z?" - count OTHER properties, not Z
- "How many X in the last week/month?" - calculate the exact date range from the question date, then filter
- Pay attention to qualifiers like "before", "after", "initially", "currently", "in total"

**When to Say "I Don't Know":**
- If the question asks about something not in the retrieved context, say "I don't have information about X"
- If comparing two things (e.g., "which happened first, X or Y?") but only one is mentioned, explicitly say the other is missing
- Don't guess or infer dates that aren't explicitly stated in the facts or chunks
- If you cannot find a specific piece of information after checking all facts and chunks, admit it
- **Partial knowledge is OK**: If asked about two things and you only have info on one, provide what you know and note what's missing (don't just say "I don't know")

**For Recommendation/Preference Questions (tips, suggestions, advice):**
- **DO NOT invent specific recommendations** (no made-up product names, course names, paper titles, channel names, etc.)
- **DO mention specific brands/products the user ALREADY uses** from the context
- Describe WHAT KIND of recommendation the user would prefer, referencing their existing tools/brands
- Keep answers concise - focus on key preferences (brand, quality level, specific interests) not exhaustive category lists
- First scan ALL facts for user's existing tools, brands, stated preferences

**How to Answer:**
1. Scan ALL facts to find relevant memories - don't stop after finding a few
2. **Read the source chunks carefully** - they contain the actual details you need
3. Convert all relative times to absolute dates
4. Use temporal information to understand when things happened
5. Synthesize information from multiple facts if needed
6. If facts conflict, prefer more recent information
7. Double-check any date calculations before answering
8. **For counting questions ("how many")**: First list each unique item in your reasoning (1. X, 2. Y, 3. Z...), then count them
9. **For recommendations**: Reference the user's existing tools, experiences, or preferences explicitly

**Answer Guidelines:**
1. Start by scanning retrieved context to understand the facts and events that happened and the timeline.
2. Reason about all the memories and find the right answer, considering the most recent memory as an update of the current facts.
3. If you have 2 possible answers, just say both.

In general the answer must be comprehensive and plenty of details from the retrieved context.

For quantitative/counting questions ("how many..."): First list each unique item in your reasoning (1. X, 2. Y, 3. Z...), scanning ALL facts, then count them for your answer.
If questions asks a location (where...?) make sure to include the location name.
For recommendation questions ("can you recommend...", "suggest...", "any tips..."): DO NOT give actual recommendations. Instead, describe what KIND the user would prefer based on their context. Example answer format: "The user would prefer recommendations for [category] that focus on [their interest]. They would not prefer [what to avoid based on context]."
For questions asking for help or instructions, consider the users' recent memories and previous interactions with the assistant to understand their current situation better (recent purchases, specific product models used..)
For specific number/value questions, use the context to understand what is the most up-to-date number based on recency, but also include the reasoning (in the answer) on previous possible values and why you think are less relevant.
For open questions, include as much details as possible from different sources that are relevant.
For questions where a specific entity/role is mentioned and it's different from your memory, just say the truth, don't make up anything just to fulfill the question. For example, if the question is about a specific sport, you should consider if the memories and the question are about the same sport. (e.g. american football vs soccer, shows vs podcasts)
For comparative questions, say you don't know the answer if you don't have information about both sides. (or more sides)
For questions related to time/date, carefully review the question date and the memories date to correctly answer the question.
For questions related to time/date calculation (e.g. How many days passed between X and Y?), carefully review the memories date to correctly answer the question and only provide an answer if you have information about both X and Y, otherwise say it's not possible to calculate and why.

Consider assistant's previous actions (e.g., bookings, reminders) as impactful to the user experiences.
""")

def get_judge_prompt_long_mem(question, correct_answer, predicted_answer, category=None):
    prompt_content = """Evaluate if the model response contains the correct answer to the question.
                        
I will give you a question, a correct answer, and a response from a model. 
Please set correct=true if the response contains the correct answer. Otherwise, set correct=no. 
"""

    if category == "temporal-reasoning":
        prompt_content += """
If the response is equivalent to the correct answer or contains all the intermediate steps to get the correct answer, you should also set correct=true. 
If the response only contains a subset of the information required by the answer, answer correct=false. 
In addition, do not penalize off-by-one errors for the number of days. If the question asks for the number of days/weeks/months, etc., and the model makes off-by-one errors (e.g., predicting 19 days when the answer is 18), the model's response is still correct.
"""
    elif category == "knowledge-update":
        prompt_content += """
If the response contains some previous information along with an updated answer, the response should be considered as correct as long as the updated answer is the required answer.
"""
    elif category == "single-session-preference":
        prompt_content += """
The model does not need to reflect all the points in the desired response. The response is correct as long as it recalls and utilizes the user's personal information correctly.
"""

    return f"""{prompt_content}

Question: {question}

Correct Answer: {correct_answer}

Model Response: {predicted_answer}

Evaluation criteria:
- Set score=1 if the response contains the correct answer
- Set score=1 if the response is equivalent to the correct answer or contains intermediate steps
- Set score=0 if the response is incorrect or missing key information

Provide your evaluation as a valid JSON object with the following fields:
{{
    "reasoning": "One sentence explanation",
    "score": 1 or 0
}}
Ensure the response is a valid JSON object. Do not wrap it in markdown code blocks.
"""

def get_judge_prompt_locomo(question, correct_answer, predicted_answer):
    return f"""Your task is to label an answer to a question as 'CORRECT' or 'WRONG'. You will be given the following data:
        (1) a question (posed by one user to another user),
        (2) a 'gold' (ground truth) answer,
        (3) a generated answer which you will score as CORRECT/WRONG.

    The point of the question is to ask about something one user should know about the other user based on their prior conversations.
    The gold answer will usually be a concise and short answer that includes the referenced topic, for example:
    Question: Do you remember what I got the last time I went to Hawaii?
    Gold answer: A shell necklace
    The generated answer might be much longer, but you should be generous with your grading - as long as it touches on the same topic as the gold answer, it should be counted as CORRECT.

    For time related questions, the gold answer will be a specific date, month, year, etc. The generated answer might be much longer or use relative time references (like "last Tuesday" or "next month"), but you should be generous with your grading - as long as it refers to the same date or time period as the gold answer, it should be counted as CORRECT. Even if the format differs (e.g., "May 7th" vs "7 May"), consider it CORRECT if it's the same date.
    There's an edge case where the actual answer can't be found in the data and in that case the gold answer will say so (e.g. 'You did not mention this information.'); if the generated answer says that it cannot be answered or it doesn't know all the details, it should be counted as CORRECT.

    Question: {question}
    Gold answer: {correct_answer}
    Generated answer: {predicted_answer}
    First, provide a short (one sentence) explanation of your reasoning. Short reasoning is preferred.
    If it's correct, set score=1.
    If it's incorrect, set score=0.

    Provide your evaluation as a valid JSON object with the following fields:
    {{
        "reasoning": "One sentence explanation",
        "score": 1 or 0
    }}
    Ensure the response is a valid JSON object. Do not wrap it in markdown code blocks.
"""

def get_summarize_session_prompt(chunks):
    return f"""You are analyzing a document. Below are all chunks from this document.

    Provide a comprehensive summary that:
    1. Captures the main topic and purpose of the document
    2. Highlights key points, findings, or conclusions
    3. Notes the document structure and organization
    4. Identifies any important details or data

    Document chunks:

    {chunks}

    Write ONLY the summary text (maximum 1600 characters). Do not include any meta-information, character counts, or explanations about the summary itself. Just provide the actual summary content.
    """
