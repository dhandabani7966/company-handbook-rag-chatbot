"""
tests/test_evaluation_suite.py
Automated 10-Query RAG Retrieval & Grounded Generation Evaluation Suite.
Measures retrieval precision, recall@k, answer correctness, citation validity,
unsupported claim count, and stage latencies.
"""

import time
import pytest
from typing import Dict, Any, List
from backend.llm.llm_client import ask_handbook

EVALUATION_DATASET = [
    {
        "id": "Q1",
        "query": "What is the annual leave entitlement?",
        "expected_pages": [49],
        "acceptable_pages": [49, 50, 2],
        "must_include": ["22 working days", "pro-rata", "semester"],
        "must_not_include": ["leave without pay", "8 days", "sick leave"],
        "is_answerable": True,
        "description": "Annual leave entitlement: 22 working days, pro-rata, advance semester credit."
    },
    {
        "id": "Q2",
        "query": "What is the maximum privilege leave carry-forward?",
        "expected_pages": [50],
        "acceptable_pages": [49, 50],
        "must_include": ["10 days", "25 days", "carry"],
        "must_not_include": ["leave without pay", "8 days carry-forward"],
        "is_answerable": True,
        "description": "Carry-forward: up to 10 days, max accumulated 25 days."
    },
    {
        "id": "Q3",
        "query": "Insurance Escalation Matrix",
        "expected_pages": [60],
        "acceptable_pages": [60],
        "must_include": ["escalation", "vinita shrivastav", "santosh lad"],
        "must_not_include": ["pro-rata refund", "reimbursement for education"],
        "is_answerable": True,
        "description": "Insurance escalation matrix on Page 60 (do not substitute claim procedure)."
    },
    {
        "id": "Q4",
        "query": "Atos HR Escalation Matrix",
        "expected_pages": [60],
        "acceptable_pages": [60],
        "must_include": ["vinita shrivastav", "santosh lad"],
        "must_not_include": ["reimbursement", "leave without pay"],
        "is_answerable": True,
        "description": "Atos HR escalation contacts on Page 60."
    },
    {
        "id": "Q5",
        "query": "Claim Procedure & Claim Intimation",
        "expected_pages": [63],
        "acceptable_pages": [63, 61],
        "must_include": ["atos hr team", "insurer", "death", "72 hours"],
        "must_not_include": ["exam fee", "disturbance allowance", "education assistance"],
        "is_answerable": True,
        "description": "Insurance claim procedure & intimation on Page 63 (prefer over pages 55 or 83)."
    },
    {
        "id": "Q6",
        "query": "Claim Documents to be submitted",
        "expected_pages": [63, 61],
        "acceptable_pages": [61, 63],
        "must_include": ["death claim form", "death certificate", "photo id", "cancelled cheque"],
        "must_not_include": ["higher education", "relocation", "disturbance allowance"],
        "is_answerable": True,
        "description": "Required insurance claim documents on Pages 61 & 63."
    },
    {
        "id": "Q7",
        "query": "Valid Photo ID proof of Nominee",
        "expected_pages": [61],
        "acceptable_pages": [61, 63],
        "must_include": ["photo id proof of nominee", "pan card", "aadhar card", "passport"],
        "must_not_include": ["disturbance allowance", "relocation", "leave without pay"],
        "is_answerable": True,
        "description": "Nominee Photo ID proof (PAN card / Aadhaar Card / Passport)."
    },
    {
        "id": "Q8",
        "query": "company poliys",
        "expected_pages": [18],
        "acceptable_pages": [18, 1, 16],
        "must_include": ["policies", "working", "attendance"],
        "must_not_include": ["leave without pay is mandatory"],
        "is_answerable": True,
        "description": "Typo handling for 'company poliys' without hallucination."
    },
    {
        "id": "Q9",
        "query": "What is the document owner?",
        "expected_pages": [1],
        "acceptable_pages": [1],
        "must_include": ["nasir usman shaikh", "nus", "document owner"],
        "must_not_include": ["leave", "reimbursement"],
        "is_answerable": True,
        "description": "Document owner: Nasir Usman Shaikh (NUS) on Page 1."
    },
    {
        "id": "Q10",
        "query": "How many employees work in the company?",
        "expected_pages": [],
        "acceptable_pages": [],
        "must_include": ["not contain", "enough information"],
        "must_not_include": ["employees work in the company"],
        "is_answerable": False,
        "description": "Unanswerable query probe: must return insufficient-evidence with 0 citations."
    }
]


def evaluate_single_query(item: Dict[str, Any]) -> Dict[str, Any]:
    t0 = time.perf_counter()
    result = ask_handbook(item["query"])
    latency_ms = (time.perf_counter() - t0) * 1000

    answer = result.get("answer", "")
    sources = result.get("sources", [])
    retrieved_pages = [int(s.get("page", 0)) for s in sources]

    expected = set(item["expected_pages"])
    acceptable = set(item["acceptable_pages"])

    # Precision & Recall calculation
    if not item["is_answerable"]:
        precision = 1.0 if len(retrieved_pages) == 0 else 0.0
        recall = 1.0 if len(retrieved_pages) == 0 else 0.0
    else:
        retrieved_set = set(retrieved_pages)
        hits = retrieved_set.intersection(acceptable)
        precision = len(hits) / max(1, len(retrieved_set))
        expected_hits = retrieved_set.intersection(expected) if expected else hits
        recall = len(expected_hits) / max(1, len(expected)) if expected else 1.0

    # Answer correctness checks
    answer_lower = answer.lower()
    has_must_include = all(phrase.lower() in answer_lower for phrase in item["must_include"])
    has_no_forbidden = not any(phrase.lower() in answer_lower for phrase in item["must_not_include"])
    answer_correct = has_must_include and has_no_forbidden

    # Citation correctness
    if not item["is_answerable"]:
        citation_correct = (len(retrieved_pages) == 0)
    else:
        citation_correct = all(p in acceptable for p in retrieved_pages) and len(retrieved_pages) > 0

    # Unsupported claims count
    unsupported_claims = 0 if has_no_forbidden else 1

    return {
        "id": item["id"],
        "query": item["query"],
        "expected_pages": list(expected),
        "retrieved_pages": retrieved_pages,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "answer_correct": answer_correct,
        "citation_correct": citation_correct,
        "unsupported_claims": unsupported_claims,
        "latency_ms": round(latency_ms, 2),
        "answer_snippet": answer[:150].replace("\n", " "),
        "timing": result.get("timing", {})
    }


def test_regression_q1_annual_leave():
    res = evaluate_single_query(EVALUATION_DATASET[0])
    assert res["answer_correct"], f"Failed Q1: {res}"
    assert res["citation_correct"], f"Failed Q1 citations: {res}"
    assert 49 in res["retrieved_pages"]


def test_regression_q2_carry_forward():
    res = evaluate_single_query(EVALUATION_DATASET[1])
    assert res["answer_correct"], f"Failed Q2: {res}"
    assert res["citation_correct"], f"Failed Q2 citations: {res}"
    assert any(p in [49, 50] for p in res["retrieved_pages"])


def test_regression_q3_insurance_escalation():
    res = evaluate_single_query(EVALUATION_DATASET[2])
    assert res["answer_correct"], f"Failed Q3: {res}"
    assert res["citation_correct"], f"Failed Q3 citations: {res}"
    assert 60 in res["retrieved_pages"]


def test_regression_q4_atos_hr_escalation():
    res = evaluate_single_query(EVALUATION_DATASET[3])
    assert res["answer_correct"], f"Failed Q4: {res}"
    assert res["citation_correct"], f"Failed Q4 citations: {res}"
    assert 60 in res["retrieved_pages"]


def test_regression_q5_claim_procedure():
    res = evaluate_single_query(EVALUATION_DATASET[4])
    assert res["answer_correct"], f"Failed Q5: {res}"
    assert res["citation_correct"], f"Failed Q5 citations: {res}"
    assert 63 in res["retrieved_pages"]
    assert 83 not in res["retrieved_pages"]  # No education reimbursement pollution


def test_regression_q6_claim_documents():
    res = evaluate_single_query(EVALUATION_DATASET[5])
    assert res["answer_correct"], f"Failed Q6: {res}"
    assert res["citation_correct"], f"Failed Q6 citations: {res}"
    assert any(p in [61, 63] for p in res["retrieved_pages"])
    assert 83 not in res["retrieved_pages"]
    assert 103 not in res["retrieved_pages"]


def test_regression_q7_nominee_photo_id():
    res = evaluate_single_query(EVALUATION_DATASET[6])
    assert res["answer_correct"], f"Failed Q7: {res}"
    assert res["citation_correct"], f"Failed Q7 citations: {res}"
    assert any(p in [61, 63] for p in res["retrieved_pages"])


def test_regression_q8_company_poliys_typo():
    res = evaluate_single_query(EVALUATION_DATASET[7])
    assert res["answer_correct"], f"Failed Q8: {res}"
    assert res["citation_correct"], f"Failed Q8 citations: {res}"


def test_regression_q9_document_owner():
    res = evaluate_single_query(EVALUATION_DATASET[8])
    assert res["answer_correct"], f"Failed Q9: {res}"
    assert res["citation_correct"], f"Failed Q9 citations: {res}"
    assert 1 in res["retrieved_pages"]


def test_regression_q10_unanswerable_probe():
    res = evaluate_single_query(EVALUATION_DATASET[9])
    assert res["answer_correct"], f"Failed Q10: {res}"
    assert res["citation_correct"], f"Failed Q10 citations: {res}"
    assert len(res["retrieved_pages"]) == 0


if __name__ == "__main__":
    print("\n=======================================================")
    print("RUNNING 10-QUERY RETRIEVAL & GENERATION EVALUATION SUITE")
    print("=======================================================\n")
    all_results = []
    for item in EVALUATION_DATASET:
        r = evaluate_single_query(item)
        all_results.append(r)
        status = "PASS" if (r["answer_correct"] and r["citation_correct"]) else "FAIL"
        print(f"[{status}] {r['id']} | Query: '{r['query']}'")
        print(f"       Expected Pages: {r['expected_pages']} | Retrieved: {r['retrieved_pages']}")
        print(f"       Precision: {r['precision']} | Recall: {r['recall']} | Latency: {r['latency_ms']}ms")
        print(f"       Answer: {r['answer_snippet']}...")
        print("-------------------------------------------------------")

    total_pass = sum(1 for r in all_results if r["answer_correct"] and r["citation_correct"])
    print(f"\nEvaluation Complete: {total_pass}/{len(all_results)} Tests Passed (100% Target).")
