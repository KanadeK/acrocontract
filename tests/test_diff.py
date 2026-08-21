from acrocontract.diff import compare_contracts
from acrocontract.models import FieldContract, PdfContract, Severity


def contract(*fields: FieldContract, duplicates: tuple[str, ...] = ()) -> PdfContract:
    return PdfContract(
        page_count=1,
        has_acroform=True,
        has_xfa=False,
        need_appearances=False,
        fields=fields,
        duplicate_names=duplicates,
    )


def test_classifies_machine_facing_breaking_changes() -> None:
    before = contract(
        FieldContract(name="customer.email", field_type="text", max_length=120),
        FieldContract(name="customer.role", field_type="choice", options=("buyer", "seller")),
        FieldContract(name="terms", field_type="checkbox"),
    )
    after = contract(
        FieldContract(
            name="customer.email",
            field_type="choice",
            required=True,
            read_only=True,
            max_length=60,
        ),
        FieldContract(name="customer.role", field_type="choice", options=("buyer",)),
        duplicates=("customer.email",),
    )

    result = compare_contracts(before, after)

    assert result.has_breaking_changes is True
    assert {(finding.rule_id, finding.subject) for finding in result.findings} == {
        ("ACR201", "terms"),
        ("ACR202", "customer.email"),
        ("ACR203", "customer.email"),
        ("ACR204", "customer.email"),
        ("ACR205", "customer.email"),
        ("ACR206", "customer.role"),
        ("ACR207", "customer.email"),
    }
    assert all(finding.severity is Severity.BREAKING for finding in result.findings)


def test_optional_field_addition_is_compatible() -> None:
    before = contract(FieldContract(name="customer.email", field_type="text"))
    after = contract(
        FieldContract(name="customer.email", field_type="text"),
        FieldContract(name="customer.note", field_type="text"),
    )

    result = compare_contracts(before, after)

    assert result.has_breaking_changes is False
    assert [(finding.rule_id, finding.subject, finding.severity) for finding in result.findings] == [
        ("ACR001", "customer.note", Severity.INFO)
    ]
