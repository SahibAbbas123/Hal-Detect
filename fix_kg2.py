import re

path = "current/bidirectional_kg_resolver.py"
with open(path, "r") as f:
    text = f.read()

# Replace _SUPERLATIVE_PATTERNS fully
new_patterns = """_SUPERLATIVE_PATTERNS = [
    (r"^(.*?)\\s+is\\s+(?:the\\s+)?(?:highest|tallest)\\s+(?:mountain|peak|point)\\s+in\\s+(.*?)(?:\\.|$)", "highest_peak"),
    (r"^(.*?)\\s+is\\s+(?:the\\s+)?(?:lowest)\\s+(?:point)\\s+in\\s+(.*?)(?:\\.|$)", "lowest_point"),
    (r"^(.*?)\\s+is\\s+(?:the\\s+)?(?:capital|largest city)\\s+of\\s+(.*?)(?:\\.|$)", "capital")
]"""

# Just find where it starts and ends
start = text.find("_SUPERLATIVE_PATTERNS = [")
end = text.find("]", start) + 1
text = text[:start] + new_patterns + text[end:]

with open(path, "w") as f:
    f.write(text)
