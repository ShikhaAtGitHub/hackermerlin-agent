# src/llm_agent.py
from langchain_community.llms import Ollama
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain

def extract_password_with_llm(
    response_text: str,
    first_letters: str = "",
    last_letters: str = "",
    length: str = "",
    additional_hints: str = ""
) -> str:
    """
    Use Llama3 via LangChain to extract the hidden secret password from Merlin's response,
    considering both the latest response and accumulated hints.
    """

    llm = Ollama(model="llama3")

    prompt = PromptTemplate(
        input_variables=["merlin_response", "first_letters", "last_letters", "length", "additional_hints"],
        template="""
        You are a puzzle-solving assistant. 
        Merlin gives cryptic answers. Hidden in his responses is a **single secret word** that serves as the password.  

        Use the hints collected so far if available:
        - First letters (if known): {first_letters}
        - Last letters (if known): {last_letters}
        - Expected length (if known): {length}
        - Additional hints: {additional_hints}

        Current Merlin response:
        {merlin_response}

        Rules:
        - Return only the final predicted password (a single word).
        - Do not explain or add punctuation.
        - Prefer uppercase words if they appear to be the password.
        - If hints form a clear word, use them to override vague guesses.

        Predicted password:
        """
    )

    chain = LLMChain(llm=llm, prompt=prompt)
    result = chain.run({
        "merlin_response": response_text,
        "first_letters": first_letters,
        "last_letters": last_letters,
        "length": length,
        "additional_hints": additional_hints
    })

    return result.strip()
