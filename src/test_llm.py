from llm_agent import extract_password_with_llm

response = """Ah, young traveler, the first President of the United States was George Washington, 
a stalwart leader who guided the nation with wisdom."""

password = extract_password_with_llm(response)
print("Extracted password:", password)



