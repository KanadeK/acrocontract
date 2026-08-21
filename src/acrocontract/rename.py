"""Explainable, advisory rename detection for removed and added fields."""

from difflib import SequenceMatcher
from math import hypot

from .models import FieldContract, RenameProposal

MIN_CONFIDENCE = 0.72
MIN_MARGIN = 0.05


def propose_renames(
    removed: list[FieldContract], added: list[FieldContract]
) -> tuple[RenameProposal, ...]:
    """Return only mutual, unambiguous best matches above the confidence threshold."""
    candidates = [
        _score(source, target)
        for source in removed
        for target in added
        if source.field_type == target.field_type
    ]
    accepted: list[RenameProposal] = []
    for proposal in candidates:
        source_candidates = sorted(
            (item for item in candidates if item.source == proposal.source),
            key=lambda item: (-item.confidence, item.target),
        )
        target_candidates = sorted(
            (item for item in candidates if item.target == proposal.target),
            key=lambda item: (-item.confidence, item.source),
        )
        if proposal is not source_candidates[0] or proposal is not target_candidates[0]:
            continue
        if proposal.confidence < MIN_CONFIDENCE:
            continue
        if len(source_candidates) > 1 and (
            proposal.confidence - source_candidates[1].confidence < MIN_MARGIN
        ):
            continue
        if len(target_candidates) > 1 and (
            proposal.confidence - target_candidates[1].confidence < MIN_MARGIN
        ):
            continue
        accepted.append(proposal)
    return tuple(sorted(accepted, key=lambda item: (item.source, item.target)))


def _score(source: FieldContract, target: FieldContract) -> RenameProposal:
    name_score = SequenceMatcher(None, source.name.casefold(), target.name.casefold()).ratio()
    label_score = 0.0
    position_score = 0.0
    weighted_score = 0.35 * name_score
    weight = 0.35
    reasons = [f"Field type is unchanged ({source.field_type})."]

    if source.alternate_name and target.alternate_name:
        label_score = SequenceMatcher(
            None, source.alternate_name.casefold(), target.alternate_name.casefold()
        ).ratio()
        weighted_score += 0.4 * label_score
        weight += 0.4
        if label_score == 1.0:
            reasons.append("Alternate name is identical.")

    if source.widgets and target.widgets:
        before = source.widgets[0]
        after = target.widgets[0]
        if before.page == after.page:
            before_center = (
                (before.rect[0] + before.rect[2]) / 2,
                (before.rect[1] + before.rect[3]) / 2,
            )
            after_center = (
                (after.rect[0] + after.rect[2]) / 2,
                (after.rect[1] + after.rect[3]) / 2,
            )
            distance = hypot(before_center[0] - after_center[0], before_center[1] - after_center[1])
            position_score = max(0.0, 1.0 - distance / 144.0)
        weighted_score += 0.25 * position_score
        weight += 0.25
        if position_score == 1.0:
            reasons.append("First widget position is identical.")

    confidence = weighted_score / weight
    reasons.append(f"Field-name similarity is {name_score:.2f}.")
    return RenameProposal(
        source=source.name,
        target=target.name,
        confidence=round(confidence, 4),
        name_score=round(name_score, 4),
        label_score=round(label_score, 4),
        position_score=round(position_score, 4),
        reasons=tuple(reasons),
    )
