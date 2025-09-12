from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

_DEFAULT_PROMPT = """
You are a puzzle assistant. Your task is to reconstruct the hidden password.

Use conversation Q/A and hints. Apply these rules:
- If asked for reverse/descending order and an ALL-CAPS token appears, reverse it back.
- If asked for first/last N letters, stitch them.
- Validate with length if provided.
- Prefer ALL-CAPS tokens that fit hints.
- Return ONE WORD only. If uncertain, return WAIT.

QA Pairs:
{qa_pairs}

Hints:
first_letters: {first_letters}
last_letters: {last_letters}
length: {length}
tokens: {tokens}
additional_hints: {additional_hints}

Merlin’s latest response:
{merlin_response}

Final password:
"""

def extract_password_with_llm(
    response_text: str,
    first_letters: str = "",
    last_letters: str = "",
    length: str = "",
    additional_hints: str = "",
    question_context: dict = None,
    qa_pairs=None,
    tokens=None,
) -> str:
    if question_context is None:
        question_context = {}
    if qa_pairs is None:
        qa_pairs = []
    if tokens is None:
        tokens = []

    llm = Ollama(model="llama3")

    qa_pairs_str = "\n".join([f"Q: {qa['q']} A: {qa['a']}" for qa in qa_pairs])

    prompt = PromptTemplate(
        input_variables=[
            "qa_pairs", "merlin_response", "first_letters",
            "last_letters", "length", "tokens", "additional_hints"
        ],
        template=_DEFAULT_PROMPT
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.run({
        "qa_pairs": qa_pairs_str,
        "merlin_response": response_text,
        "first_letters": first_letters,
        "last_letters": last_letters,
        "length": length,
        "tokens": " ".join(tokens),
        "additional_hints": additional_hints
    }).strip()

    if not result or result.upper() == "WAIT":
        return ""
    return result.split()[0].strip()
