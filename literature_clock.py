import json
import os
import random
from datetime import datetime

def get_current_time_quote():
    now = datetime.now()
    filepath = f"times/{now.hour:02d}_{now.minute:02d}.json"

    print(filepath)
    if not os.path.exists(filepath):
        return {
            "quote_first": None,
            "quote_time_case": None,
            "quote_last": None,
            "title": None,
            "author": None,
            }

    with open(filepath, "r", encoding="utf-8") as f:
        quotes = json.load(f)

    quote = random.choice(quotes)
    return quote

# Example usage
if __name__ == "__main__":
    result = get_current_time_quote()
    
    print(result["quote_first"] + result["quote_time_case"] + result["quote_last"])
    print("     -" + result["title"] + ", " + result["author"])
