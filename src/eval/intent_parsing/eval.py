import json

import laya
from laya import Router

def parse_intent(router:Router, query: str):
    questions = {
        "intent": {
            "type": "choice",
            "instructions": "Based on the user's query, determine the user's intent",
            "criteria": {
                "qna": "Queries seeking conceptual explanations, factual recall, theoretical/mathematical formulations, design rationales, or comparative analyses that require natural language answers without asking to write, execute, or debug code.",
                "dev": "Queries requesting actionable programmatic tasks, such as writing or refactoring code, debugging explicit errors or tracebacks, applying specific library/API syntax, or setting up software/framework pipelines.",
            }
        }
    }
    state = {
        "query": query,
    }
    res = router.predict(state, questions)
    return res

def main():
    router = Router(preload=True)

    with open(f"eval/intent_parsing/queries.json", "r", encoding="utf-8") as f:
        test_cases_data = json.load(f)
    is_correct = 0
    for i, case in enumerate(test_cases_data):
        res = parse_intent(router, case["query"])
        pred_intent = res['answers']['intent']
        intent = case['intent']
        if intent == pred_intent["choice"]:
            is_correct += 1
        print(f"Query {i + 1} => Truth: {intent} Predicted: {pred_intent['choice']}")
    print("="*70)
    print(f"Total correct parsing: {is_correct}/{len(test_cases_data)}")
    


if __name__ == "__main__":
    main()
