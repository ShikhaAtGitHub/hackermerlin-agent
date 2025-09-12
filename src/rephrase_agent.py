from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

_REPHRASE_PROMPT = """
You are a rephrasing assistant. 
Reword the given password-related questions into new phrasings 
that avoid repetition but keep the same intent. 
Provide {n} alternate variants per question.

Questions:
{questions}

Rephrased versions:
"""

def generate_rephrases(questions, n=2):
    """Generate rephrased questions using Ollama."""
    llm = Ollama(model="llama3")
    prompt = PromptTemplate(
        input_variables=["questions", "n"],
        template=_REPHRASE_PROMPT
    )
    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.run({"questions": "\n".join(questions), "n": n})
    rephrased = []
    for line in result.splitlines():
        line = line.strip("-• ").strip()
        if line:
            rephrased.append(line)
    return rephrased if rephrased else questions
