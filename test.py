from ollama import chat

SYSTEM_PROMPT = """
You are a physics parser.

Return ONLY valid JSON.

Schema:

{
    "scenario_type":"",
    "objects":[],
    "geometry":{},
    "friction":"",
    "mu":null,
    "applied_forces":[],
    "unknowns":[]
}
"""

QUESTION = """
A box of mass 5 kg is placed on a frictionless inclined plane of 30 degrees.
Find the force required to keep it at rest.
"""

response = chat(
    model="qwen2.5:7b",
    messages=[
        {"role":"system","content":SYSTEM_PROMPT},
        {"role":"user","content":QUESTION}
    ]
)

print(response["message"]["content"])