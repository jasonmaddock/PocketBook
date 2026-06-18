from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Iterable, List, Optional, Tuple

from config import UNCATEGORISED_NAME, UNCATEGORISED_ID

@dataclass
class Rule:
    id: Optional[int]
    name: str
    merchant_pattern: Optional[str]
    description_pattern: Optional[str]
    category_id: Optional[int]
    category_name: str
    subcategory_id: Optional[int] = None
    subcategory_name: Optional[str] = None
    fuzzy_threshold: float = 0.75
    priority: int = 100

    @classmethod
    def from_row(cls, row) -> "Rule":
        return cls(
            id=row["id"],
            name=row["name"],
            merchant_pattern=row["merchant_pattern"],
            description_pattern=row["description_pattern"],
            category_id=row["category_id"],
            category_name=(row["category_name"] if "category_name" in row.keys() else None) or "Uncategorised",
            subcategory_id=row["subcategory_id"] if "subcategory_id" in row.keys() else None,
            subcategory_name=row["subcategory_name"] if "subcategory_name" in row.keys() else None,
            fuzzy_threshold=row["fuzzy_threshold"],
            priority=row["priority"],
        )


def _score(pattern: Optional[str], text: str) -> Optional[float]:
    if not pattern or not text:
        return None
    pattern = pattern.lower()
    text = text.lower()
    # Reward direct containment, otherwise fall back to fuzzy ratio
    if pattern in text:
        return 1.0
    return SequenceMatcher(None, pattern, text).ratio()


def classify_transaction(tx: dict, rules: Iterable[Rule]) -> Tuple[Optional[int], str, Optional[int], Optional[int], str, float]:
    merchant = (tx.get("merchant") or "").strip()
    description = (tx.get("description") or "").strip()

    for rule in sorted(rules, key=lambda r: (r.priority, r.id or 0)):
        scores: List[float] = []
        merchant_score = _score(rule.merchant_pattern, merchant)
        desc_score = _score(rule.description_pattern, description)

        if merchant_score is not None:
            scores.append(merchant_score)
        if desc_score is not None:
            scores.append(desc_score)

        score = max(scores) if scores else 0.0
        if score >= rule.fuzzy_threshold:
            return rule.category_id, rule.category_name, rule.subcategory_id, rule.subcategory_name or "", rule.id, score

    return UNCATEGORISED_ID, UNCATEGORISED_NAME, None, "", None, 0.0

def apply_rules(transactions: List[dict], rules: Iterable[Rule]) -> List[dict]:
    rules_list = list(rules)
    enriched = []
    for tx in transactions:
        category_id, category_name, subcategory_id, subcategory_name, rule_id, confidence = classify_transaction(tx, rules_list)
        enriched.append({
            **tx,
            "category_id": category_id,
            "category": category_name,
            "subcategory_id": subcategory_id,
            "subcategory": subcategory_name,
            "rule_id": rule_id,
            "confidence": confidence,
        })
    return enriched
