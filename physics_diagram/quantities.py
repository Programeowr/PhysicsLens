"""Quantity extraction and unit conversion; no NLP model is required here."""

from __future__ import annotations

import re
from dataclasses import dataclass
from math import degrees

WORD_NUMBERS: dict[str, int] = {
    "zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12, "thirteen": 13, "fourteen": 14,
    "fifteen": 15, "sixteen": 16, "seventeen": 17, "eighteen": 18,
    "nineteen": 19, "twenty": 20, "thirty": 30, "forty": 40,
    "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80, "ninety": 90,
}


@dataclass(frozen=True)
class Quantity:
    value: float
    unit: str
    start: int
    end: int


def replace_spelled_numbers(text: str) -> str:
    """Convert common number words (including 'thirty five') to digits."""
    words = "|".join(WORD_NUMBERS)
    pattern = re.compile(rf"\b(({words})(?:[ -]({words}))?)\b", re.IGNORECASE)

    def convert(match: re.Match[str]) -> str:
        first = WORD_NUMBERS[match.group(2).lower()]
        second = match.group(3)
        return str(first + (WORD_NUMBERS[second.lower()] if second else 0))

    return pattern.sub(convert, text)


def extract_quantities(text: str) -> list[Quantity]:
    normalized = replace_spelled_numbers(text.lower())
    pattern = re.compile(
        r"(?P<value>[-+]?\d+(?:\.\d+)?)\s*(?P<unit>kg|kgs?|g|grams?|lb|lbs?|"
        r"degrees?|deg|°|radians?|rad|m/s|mps|km/h|kmph|mph|newtons?|n)(?![a-z])"
    )
    return [Quantity(float(m.group("value")), m.group("unit"), m.start(), m.end()) for m in pattern.finditer(normalized)]


def mass_to_kg(value: float, unit: str) -> float:
    unit = unit.lower()
    if unit.startswith("g") and unit not in {"kg", "kgs"}:
        return value / 1000
    if unit.startswith("lb"):
        return value * 0.45359237
    return value


def angle_to_degrees(value: float, unit: str) -> float:
    return degrees(value) if unit.lower().startswith("rad") else value


def speed_to_ms(value: float, unit: str) -> float:
    unit = unit.lower()
    if unit in {"km/h", "kmph"}:
        return value / 3.6
    if unit == "mph":
        return value * 0.44704
    return value
