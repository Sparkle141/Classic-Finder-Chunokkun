from __future__ import annotations

from expand_multilingual_queries import expand_queries
from expand_korean_keywords import expand_keywords


def assert_contains(items: list[str], needle: str) -> None:
    haystack = "\n".join(items).lower()
    if needle.lower() not in haystack:
        raise AssertionError(f"Missing expected query fragment: {needle}")


def main() -> None:
    keyword_plan = expand_keywords("홉스: 자연상태는 만인에 대한 만인의 투쟁 상태이다")
    keyword_queries = [item["query"] for item in keyword_plan["queries"]]
    assert_contains(keyword_queries, "war of every man against every man")
    assert_contains(keyword_queries, "Thomas Hobbes")
    assert_contains(keyword_queries, "Leviathan")

    hobbes = expand_queries("홉스: 자연상태는 만인에 대한 만인의 투쟁 상태이다")
    hobbes_queries = [item["query"] for item in hobbes["queries"]]
    assert_contains(hobbes_queries, "Thomas Hobbes")
    assert_contains(hobbes_queries, "Leviathan")
    assert_contains(hobbes_queries, "war of every man against every man")
    assert_contains(hobbes_queries, "Leviathan Chapter 13")

    rousseau = expand_queries("인간은 자유롭게 태어났지만 어디에서나 사슬에 묶여 있다", author="Rousseau", work="Social Contract")
    rousseau_queries = [item["query"] for item in rousseau["queries"]]
    assert_contains(rousseau_queries, "Man is born free")
    assert_contains(rousseau_queries, "dans les fers")

    print("reverse trace smoke tests passed")


if __name__ == "__main__":
    main()
