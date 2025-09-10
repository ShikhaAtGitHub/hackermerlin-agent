# src/llm_agent.py
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

def extract_password_with_llm(response_text: str) -> str:
    """
    Use Llama3 via LangChain to extract the hidden secret password from Merlin's response.
    This version is fully generic and does not assume any prior password.
    """

    llm = Ollama(model="llama3")

    # generic, safe prompt
    prompt = PromptTemplate(
        input_variables=["merlin_response"],
        template="""
        You are a puzzle-solving assistant.  
        Merlin gives cryptic answers. Hidden in his response is a **single secret word** that serves as the puzzle password.  
        **Do not pick proper nouns, numbers, dates, or obvious facts.**  
        Focus on lowercase words that look like a hidden hint or puzzle.  
        Return **only the secret word**, nothing else.

        Merlin's response:
        {merlin_response}

        Secret password:
        """
        )

    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.run({"merlin_response": response_text})

    return result.strip()
