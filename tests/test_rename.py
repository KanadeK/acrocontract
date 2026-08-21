from pathlib import Path

from acrocontract.diff import compare_contracts
from acrocontract.inspect import inspect_pdf


def test_proposes_mutual_high_confidence_rename_with_component_scores(
    pdf_fixtures: Path,
) -> None:
    before = inspect_pdf(pdf_fixtures / "customer-intake-v1.pdf")
    after = inspect_pdf(pdf_fixtures / "customer-intake-v2.pdf")

    result = compare_contracts(before, after)

    assert len(result.rename_proposals) == 1
    proposal = result.rename_proposals[0]
    assert proposal.source == "customer.email"
    assert proposal.target == "contact.email"
    assert proposal.confidence >= 0.8
    assert proposal.label_score == 1.0
    assert proposal.position_score == 1.0
    assert proposal.reasons
    assert ("ACR101", "customer.email -> contact.email") in {
        (finding.rule_id, finding.subject) for finding in result.findings
    }


def test_does_not_propose_ambiguous_rename() -> None:
    from acrocontract.models import FieldContract, PdfContract

    before = PdfContract(1, True, False, False, (FieldContract("old", "text"),))
    after = PdfContract(
        1,
        True,
        False,
        False,
        (FieldContract("new-a", "text"), FieldContract("new-b", "text")),
    )

    assert compare_contracts(before, after).rename_proposals == ()
