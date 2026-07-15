from services.json_parser import JSONParser


def test_parse_json_from_markdown_code_block():
    parser = JSONParser()

    text = """
Here is the result:

```json
{
    "research_problem": "Robot navigation",
    "main_contributions": [
        "A new method"
    ]
}
```
"""

    result = parser.parse(text)

    assert result["research_problem"] == "Robot navigation"
    assert result["main_contributions"] == ["A new method"]


def test_parse_plain_json():
    parser = JSONParser()

    text = """
{
    "research_problem": "Vision-language navigation",
    "main_contributions": [
        "Structured analysis",
        "Reflection support"
    ]
}
"""

    result = parser.parse(text)

    assert result["research_problem"] == "Vision-language navigation"
    assert result["main_contributions"] == [
        "Structured analysis",
        "Reflection support",
    ]