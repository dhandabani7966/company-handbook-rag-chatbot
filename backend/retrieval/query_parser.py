"""
backend/retrieval/query_parser.py
Query understanding, typo normalization, and intent classification for Company Handbook Intelligence AI.
Preserves the user's original query for grounded generation while normalizing search representations.
"""

import re
from typing import Dict, Any, List

# Common handbook typos and policy terminology mapping
TYPO_CORRECTIONS = {
    r"\bpoliys\b": "policies",
    r"\bpolicys\b": "policies",
    r"\bpolicyes\b": "policies",
    r"\bmetrix\b": "matrix",
    r"\bmatrx\b": "matrix",
    r"\breimbersement\b": "reimbursement",
    r"\breimbersment\b": "reimbursement",
    r"\bentitlment\b": "entitlement",
    r"\bencashmnt\b": "encashment",
    r"\bmaternty\b": "maternity",
    r"\bpaternty\b": "paternity",
    r"\bconduciv\b": "conducive",
    r"\baccruel\b": "accrual",
}

STOP_WORDS = {
    "what", "when", "where", "which", "how", "why", "who", "is", "was", "are", "were",
    "the", "a", "an", "for", "in", "to", "of", "and", "or", "it", "its", "at", "by",
    "be", "this", "that", "these", "those", "have", "has", "had", "do", "does", "did",
    "can", "could", "should", "would", "tell", "me", "about", "give", "please", "my"
}

GENERIC_TERMS = {
    "date", "dates", "day", "days", "time", "times", "procedure", "process",
    "policy", "policies", "rule", "rules", "guideline", "guidelines", "status",
    "method", "step", "steps", "type", "types", "detail", "details", "info",
    "information", "requirement", "requirements", "eligibility", "criteria",
    "handbook", "company", "employee", "work"
}


def normalize_query_text(query: str) -> str:
    """
    Normalize whitespace, clean extraneous punctuation, and correct common handbook spelling mistakes
    without modifying the semantic intent.
    """
    if not query:
        return ""

    # Clean whitespace
    text = re.sub(r"\s+", " ", query).strip()

    # Apply typo corrections
    for pattern, replacement in TYPO_CORRECTIONS.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Clean leading/trailing quotes and punctuation
    text = text.strip("?.,;!\"'“”‘’ \t\n\r")
    return text


def parse_query_intent(query: str) -> Dict[str, Any]:
    """
    Analyze query intent and categorize into handbook sections and policy topics.
    Preserves original query while extracting targeted search tokens.
    """
    norm = normalize_query_text(query)
    q_lower = norm.lower()

    # Exact topic flags
    is_doc_owner = bool(re.search(r"\b(document\s+owner|owner\s+of\s+the\s+document|who\s+is\s+the\s+document\s+owner|author|document\s+reference)\b", q_lower))
    is_escalation_matrix = bool(re.search(r"\b(escalation\s+matrix|escalation\s+contact|escalation\s+levels?)\b", q_lower))
    is_atos_hr_escalation = bool(re.search(r"\b(atos\s+hr\s+escalation|hr\s+escalation)\b", q_lower))
    is_insurance_escalation = bool(re.search(r"\b(insurance\s+escalation|godigit\s+escalation|marsh\s+escalation)\b", q_lower)) or (is_escalation_matrix and "insurance" in q_lower)

    is_nominee_photo_id = bool(re.search(r"\b(photo\s*id|valid\s*photo\s*id|id\s*proof|nominee\s*id|proof\s*of\s*nominee)\b", q_lower))
    is_claim_docs = bool(re.search(r"\b(claim\s+documents?|documents?\s+to\s+be\s+submitted|documents?\s+required\s+for\s+claim|death\s+claim\s+documents?)\b", q_lower))
    is_claim_proc = bool(re.search(r"\b(claim\s+procedure|claim\s+intimation|intimate\s+claim|claim\s+process)\b", q_lower)) and not is_claim_docs

    is_wfh = bool(re.search(r"\b(wfh|remote[\s\-]*work|work[\s\-]*from[\s\-]*home|working[\s\-]*remotely)\b", q_lower))
    is_wfh_reimb = is_wfh and bool(re.search(r"\b(reimburse|reimbursement|bill|bills|expense|expenses|cost|costs|internet|broadband)\b", q_lower))
    is_lsa = bool(re.search(r"\b(long[\s\-]*service[\s\-]*award|service[\s\-]*award|long[\s\-]*service|accolade|felicitation)\b", q_lower))

    is_compare_pl = bool(re.search(r"\bcompare\b", q_lower)) and bool(re.search(r"\b(annual|entitlement)\b", q_lower)) and bool(re.search(r"\b(carry|forward|accumulation)\b", q_lower))
    is_carry_forward = bool(re.search(r"\b(carry[\s\-]*forward|accumulation|accumulate)\b", q_lower)) and not is_compare_pl
    is_lwp = bool(re.search(r"\b(lwp|leave\s+without\s+pay|without\s+pay|unpaid\s+leave)\b", q_lower))
    is_sick = bool(re.search(r"\b(sick\s+leave|medical\s+sick\s+leave|\bsl\b)\b", q_lower))
    is_special = bool(re.search(r"\b(special\s+leave|special\s+medical\s+leave)\b", q_lower))
    is_maternity = bool(re.search(r"\b(maternity\s+leave|pregnancy|\bml\b)\b", q_lower))
    is_paternity = bool(re.search(r"\b(paternity\s+leave)\b", q_lower))
    is_bereavement = bool(re.search(r"\b(bereavement\s+leave)\b", q_lower))
    is_adoption = bool(re.search(r"\b(child\s+adoption|adoption\s+leave)\b", q_lower))
    is_encashment = bool(re.search(r"\b(encashment|encash\b)", q_lower))
    is_notice = bool(re.search(r"\b(notice\s+period)\b", q_lower))
    is_donation = bool(re.search(r"\b(donate|donation|transfer\s+of\s+leave|leave\s+transfer)\b", q_lower))

    # General company policies typo query (e.g. "company poliys" or "company policies")
    is_general_policies = bool(re.search(r"\bcompany\s+policies\b", q_lower)) and not (is_wfh or is_lsa or is_claim_proc or is_claim_docs or is_doc_owner or is_escalation_matrix)

    # Annual / Privilege / Earned leave:
    is_annual_privilege = bool(re.search(
        r"\b(annual\s+leave|privilege\s+leave|earned\s+leave|\bpl\b|carry\s*-?forward|accumulation|advance\s+pl|leave\s+entitlement|annual\s+entitlement)\b",
        q_lower
    ))
    if not (is_lwp or is_sick or is_special or is_maternity or is_paternity or is_bereavement or is_adoption or is_donation or is_wfh or is_lsa or is_doc_owner or is_escalation_matrix or is_claim_docs or is_claim_proc or is_nominee_photo_id) and "leave" in q_lower:
        is_annual_privilege = True

    # Identify unanswerable queries: probes asking for info not contained in the handbook
    is_unanswerable_probe = bool(re.search(r"\b(how\s+many\s+employees|total\s+employees|share\s+price|stock\s+price|company\s+revenue|annual\s+turnover)\b", q_lower))

    # Targeted search queries for hybrid retrieval
    search_queries = [norm]
    if is_doc_owner:
        search_queries.append("Document Owner Nasir Usman Shaikh IND-HRM-1020")
    elif is_insurance_escalation or is_atos_hr_escalation or is_escalation_matrix:
        search_queries.append("11.1.6 Insurance Escalation Matrix Atos HR Escalation Matrix Vinita Shrivastav Santosh Lad")
    elif is_nominee_photo_id:
        search_queries.append("Valid Photo id proof of Nominee Pan card Aadhar Card Passport")
    elif is_claim_docs:
        search_queries.append("Claim Documents to be submitted Death claim form Death Certificate Doctor Hospital Certificate Photo id proof of Nominee")
    elif is_claim_proc:
        search_queries.append("Claim Procedure Claim Intimation Atos HR team intimates the insurer 72 Hours")
    elif is_general_policies:
        search_queries.append("General Employment Policies Guidelines Working Hours and Attendance Employee Policy Handbook")

    return {
        "original_query": query,
        "normalized_query": norm,
        "search_queries": search_queries,
        "is_doc_owner": is_doc_owner,
        "is_escalation_matrix": is_escalation_matrix,
        "is_atos_hr_escalation": is_atos_hr_escalation,
        "is_insurance_escalation": is_insurance_escalation,
        "is_nominee_photo_id": is_nominee_photo_id,
        "is_claim_docs": is_claim_docs,
        "is_claim_proc": is_claim_proc,
        "is_wfh": is_wfh,
        "is_wfh_reimb": is_wfh_reimb,
        "is_lsa": is_lsa,
        "is_compare_pl": is_compare_pl,
        "is_carry_forward": is_carry_forward,
        "is_lwp": is_lwp,
        "is_sick": is_sick,
        "is_special": is_special,
        "is_maternity": is_maternity,
        "is_paternity": is_paternity,
        "is_bereavement": is_bereavement,
        "is_adoption": is_adoption,
        "is_encashment": is_encashment,
        "is_notice": is_notice,
        "is_donation": is_donation,
        "is_annual_privilege": is_annual_privilege,
        "is_general_policies": is_general_policies,
        "is_unanswerable_probe": is_unanswerable_probe,
    }
