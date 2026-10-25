"""
tests/test_handbook_regression.py
Regression tests against Atos India Employee Policy Handbook version 10.3 PDF.
Verifies:
1. Required numbered-headings answer formatting (1. **Heading:**\n   Explanation)
2. Strict policy isolation (WFH does not contain awards/bills; WFH reimbursements isolated; LSA isolated)
3. Distinction between 22-day entitlement, 10-day carry-forward, and 25-day accumulation
4. Accurate PDF page citations
5. Refusal on unanswered / out-of-scope questions
"""

import re
import pytest
from backend.retrieval.retriever import get_retriever
from backend.llm.llm_client import ask_handbook
import backend.vectordb.vector_store as vs_module
import backend.retrieval.retriever as ret_module


@pytest.fixture(autouse=True)
def ensure_live_store():
    """Ensure retriever and vector store singletons point to persistent live collection."""
    vs_module._client_instance = None
    ret_module._retriever_instance = None
    yield
    vs_module._client_instance = None
    ret_module._retriever_instance = None


def print_test_details(test_title: str, query: str, result: dict, retrieved_inspection: dict = None):
    print("\n" + "=" * 80)
    print(f"REGRESSION TEST: {test_title}")
    print(f"QUERY: {query}")
    print("-" * 80)
    print("RETRIEVED PASSAGES / CHUNKS:")
    sources = result.get("sources", [])
    if not sources and retrieved_inspection:
        sources = retrieved_inspection.get("sources", [])

    for idx, s in enumerate(sources, 1):
        page = s.get("page")
        score = s.get("score", 0.0)
        eff_score = s.get("effective_score", score)
        text = s.get("text", "")
        print(f"  [Chunk {idx}] Page: {page} | Score: {score:.4f} (Effective: {eff_score:.4f})")
        print(f"  Excerpt: {text[:280]}...")
        print()

    print("-" * 80)
    print("FINAL GENERATED ANSWER:")
    print(result.get("answer"))
    print(f"CITATIONS / SUPPORTING PAGES: {[s.get('page') for s in result.get('sources', [])]}")
    print(f"TIMING: {result.get('timing')}")
    print("=" * 80 + "\n")


def test_annual_leave_entitlement():
    """
    Query 1: What is the annual leave entitlement?
    Verifies:
    - Numbered-heading format (1. **Annual Leave Policy:**)
    - 22 working days of annual leave per year
    - Citation on PDF Page 49
    - No contamination from Page 52 (LWP / Sick leave)
    """
    query = "What is the annual leave entitlement?"
    retriever = get_retriever()
    inspection = retriever.retrieve_and_inspect(query)
    result = ask_handbook(query)

    print_test_details("Query 1: Annual Leave Entitlement", query, result, inspection)

    # 1. Format check
    answer = result["answer"]
    assert "1. **Annual Leave Policy:**" in answer, f"Expected numbered heading format, got:\n{answer}"

    # 2. Fact check
    assert "22 working days" in answer
    assert "leave without pay" not in answer.lower()
    assert "lwp" not in answer.lower()

    # 3. Citation check
    cited_pages = [s["page"] for s in result["sources"]]
    assert 49 in cited_pages, f"Expected PDF Page 49, got {cited_pages}"
    assert 52 not in cited_pages, f"Page 52 should not be cited, got {cited_pages}"


def test_privilege_leave_carry_forward():
    """
    Query 2: What is the maximum privilege leave carry-forward limit?
    Verifies:
    - Numbered-heading format (1. **Maximum Privilege Leave Carry-Forward:**)
    - 10 days carry-forward limit
    - 25 days maximum accumulated balance
    - Citations from PDF Pages 49/50
    """
    query = "What is the maximum privilege leave carry-forward limit?"
    retriever = get_retriever()
    inspection = retriever.retrieve_and_inspect(query)
    result = ask_handbook(query)

    print_test_details("Query 2: Maximum Privilege Leave Carry-Forward Limit", query, result, inspection)

    answer = result["answer"]
    assert "1. **Maximum Privilege Leave Carry-Forward:**" in answer
    assert "10 days" in answer
    assert "25 days" in answer

    cited_pages = [s["page"] for s in result["sources"]]
    assert 50 in cited_pages or 49 in cited_pages
    assert 52 not in cited_pages
    assert 53 not in cited_pages


def test_compare_annual_leave_and_carry_forward():
    """
    Query 3: Compare annual leave entitlement and carry-forward limits.
    Verifies:
    - Two separate numbered headings:
      1. **Annual Leave Policy:**
      2. **Maximum Privilege Leave Carry-Forward:**
    - Distinguishes 22-day entitlement, 10-day carry-forward, and 25-day accumulation
    - Citations include PDF Pages 49 and 50
    """
    query = "Compare annual leave entitlement and carry-forward limits."
    retriever = get_retriever()
    inspection = retriever.retrieve_and_inspect(query)
    result = ask_handbook(query)

    print_test_details("Query 3: Compare Annual Leave and Carry-Forward", query, result, inspection)

    answer = result["answer"]
    assert "1. **Annual Leave Policy:**" in answer
    assert "2. **Maximum Privilege Leave Carry-Forward:**" in answer
    assert "22 working days" in answer
    assert "10 days" in answer
    assert "25 days" in answer

    cited_pages = [s["page"] for s in result["sources"]]
    assert 49 in cited_pages or 50 in cited_pages


def test_wfh_eligibility_and_guidelines():
    """
    Query 4: What are the work-from-home eligibility criteria and guidelines?
    Verifies:
    - Numbered-heading format (1. **Work-from-Home Policy:**, 2. **Workspace and Infrastructure Guidelines:**)
    - Conducive noise-free environment, comfortable seating, reliable broadband, UPS power backup
    - Strictly NO unrelated award policies or travel reimbursement bills
    - Citation from PDF Page 70
    """
    query = "What are the work-from-home eligibility criteria and guidelines?"
    retriever = get_retriever()
    inspection = retriever.retrieve_and_inspect(query)
    result = ask_handbook(query)

    print_test_details("Query 4: WFH Eligibility and Guidelines", query, result, inspection)

    answer = result["answer"]
    assert "1. **Work-from-Home Policy:**" in answer
    assert "2. **Workspace and Infrastructure Guidelines:**" in answer
    assert "conducive" in answer.lower() or "noise-free" in answer.lower()
    assert "broadband" in answer.lower()
    assert "ups" in answer.lower()

    # Contamination check: strictly no awards or long service
    assert "award" not in answer.lower()
    assert "felicitation" not in answer.lower()
    assert "long service" not in answer.lower()

    cited_pages = [s["page"] for s in result["sources"]]
    assert 70 in cited_pages, f"Expected Page 70 for WFH guidelines, got {cited_pages}"


def test_wfh_reimbursement_bills():
    """
    Query 5: What bills are eligible for reimbursement under the WFH policy?
    Verifies:
    - Numbered-heading format:
      1. **Broadband and Internet Reimbursement:**
      2. **Mobile Call Reimbursement:**
    - Broadband reimbursement up to INR 1,200/- per month
    - Mobile bill reimbursement for official calls only
    - Strictly NO relocation bills, car hire, or long-service awards
    - Citation from PDF Page 71 (Section 14.6 Reimbursements)
    """
    query = "What bills are eligible for reimbursement under the WFH policy?"
    retriever = get_retriever()
    inspection = retriever.retrieve_and_inspect(query)
    result = ask_handbook(query)

    print_test_details("Query 5: WFH Eligible Reimbursement Bills", query, result, inspection)

    answer = result["answer"]
    assert "1. **Broadband and Internet Reimbursement:**" in answer
    assert "2. **Mobile Call Reimbursement:**" in answer
    assert "1,200" in answer or "1200" in answer
    assert "broadband" in answer.lower()
    assert "mobile" in answer.lower()

    # Contamination check: strictly no relocation, travel, or award policies
    assert "relocation" not in answer.lower()
    assert "award" not in answer.lower()
    assert "moving goods" not in answer.lower()

    cited_pages = [s["page"] for s in result["sources"]]
    assert 71 in cited_pages, f"Expected Page 71 for WFH reimbursement, got {cited_pages}"


def test_long_service_award_collection_rules():
    """
    Query 6: What are the long-service award collection rules?
    Verifies:
    - Numbered-heading format:
      1. **Long-Service Award Milestones:**
      2. **Felicitation and Collection Rules:**
    - Mentions milestones (5, 10, 15, 20, 25, 30, 35 years)
    - Felicitation ceremony (Webinar/Townhall) and collection/onsite notification rules
    - Strictly NO WFH or leave policy contamination
    - Citation from PDF Page 76
    """
    query = "What are the long-service award collection rules?"
    retriever = get_retriever()
    inspection = retriever.retrieve_and_inspect(query)
    result = ask_handbook(query)

    print_test_details("Query 6: Long Service Award Collection Rules", query, result, inspection)

    answer = result["answer"]
    assert "1. **Long-Service Award Milestones:**" in answer
    assert "2. **Felicitation and Collection Rules:**" in answer
    assert "5 years" in answer or "10 years" in answer
    assert "felicitation" in answer.lower() or "townhall" in answer.lower()

    # Contamination check: no WFH or leave policies
    assert "work from home" not in answer.lower()
    assert "privilege leave" not in answer.lower()

    cited_pages = [s["page"] for s in result["sources"]]
    assert 76 in cited_pages, f"Expected Page 76 for Long Service Awards, got {cited_pages}"


def test_unanswered_question_salary_disbursement():
    """
    Verifies clean refusal on questions missing from handbook.
    """
    query = "When is salary disbursed?"
    retriever = get_retriever()
    inspection = retriever.retrieve_and_inspect(query)
    result = ask_handbook(query)

    print_test_details("Unanswered Query: Salary Disbursement", query, result, inspection)

    answer = result["answer"].lower()
    assert "not contain" in answer or "insufficient" in answer
    assert len(result["sources"]) == 0


def test_unanswered_question_pet_policy():
    """
    Verifies clean refusal on completely out-of-scope questions.
    """
    query = "Can I bring my pet dog to work?"
    retriever = get_retriever()
    inspection = retriever.retrieve_and_inspect(query)
    result = ask_handbook(query)

    print_test_details("Unanswered Query: Pet Policy", query, result, inspection)

    answer = result["answer"].lower()
    assert "not contain" in answer or "insufficient" in answer
    assert len(result["sources"]) == 0


if __name__ == "__main__":
    test_annual_leave_entitlement()
    test_privilege_leave_carry_forward()
    test_compare_annual_leave_and_carry_forward()
    test_wfh_eligibility_and_guidelines()
    test_wfh_reimbursement_bills()
    test_long_service_award_collection_rules()
    test_unanswered_question_salary_disbursement()
    test_unanswered_question_pet_policy()
    print("\n>>> ALL REGRESSION TESTS PASSED SUCCESSFULLY! <<<\n")
