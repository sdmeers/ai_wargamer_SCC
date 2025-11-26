import re

def format_llm_output(text):
    """
    Formats raw LLM output by replacing custom tags with HTML styles.
    Target tags: [**BOLD RED: ...**] and [**BOLD GREEN: ...**]
    """
    if not isinstance(text, str):
        return str(text)

    def replace_match(match):
        color_name = match.group(1).upper()
        content = match.group(2)
        # Define colors: Red for bad/damaged, Green for good/operational
        color_code = "#cc3333" if color_name == "RED" else "#28a745"
        return f'<span style="color: {color_code}; font-weight: bold;">{content}</span>'

    # Regex to capture COLOR and Content. Handles optional ** markers.
    # Matches: [BOLD RED: Text], [**BOLD RED: Text**], [**BOLD RED: Text] etc.
    pattern = r"\[(?:\*\*)?BOLD (RED|GREEN): (.*?)(?:\*\*)?\]"
    
    return re.sub(pattern, replace_match, text)

def test_formatting():
    test_cases = [
        (
            "HMS Queen Elizabeth: [**BOLD RED: Damaged / On Fire**]",
            'HMS Queen Elizabeth: <span style="color: #cc3333; font-weight: bold;">Damaged / On Fire</span>'
        ),
        (
            "UK SSN: [**BOLD GREEN: Operational**]",
            'UK SSN: <span style="color: #28a745; font-weight: bold;">Operational</span>'
        ),
        (
            "Mixed: [BOLD RED: Bad] and [BOLD GREEN: Good]",
            'Mixed: <span style="color: #cc3333; font-weight: bold;">Bad</span> and <span style="color: #28a745; font-weight: bold;">Good</span>'
        ),
        (
            "No tags here",
            "No tags here"
        )
    ]

    for input_text, expected in test_cases:
        result = format_llm_output(input_text)
        if result == expected:
            print(f"PASS: {input_text}")
        else:
            print(f"FAIL: {input_text}")
            print(f"  Expected: {expected}")
            print(f"  Got:      {result}")

if __name__ == "__main__":
    test_formatting()
