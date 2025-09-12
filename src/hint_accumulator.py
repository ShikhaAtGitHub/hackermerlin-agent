class HintAccumulator:
    def __init__(self):
        self.clear()

    def clear(self):
        self.hints = {
            "first_letters": "",
            "last_letters": "",
            "length": "",
            "additional_hints": "",
            "tokens": [],
            "qa_pairs": []   # store Q/A pairs for LLM synthesis
        }

    def update(self, key: str, value: str):
        if key == "tokens":
            if value not in self.hints["tokens"]:
                self.hints["tokens"].append(value)
        elif key == "additional_hints":
            self.hints["additional_hints"] += value + " "
        else:
            self.hints[key] = value

    def add_qa(self, question: str, answer: str):
        self.hints["qa_pairs"].append({"q": question, "a": answer})

    def get(self, key: str):
        return self.hints.get(key, "")
