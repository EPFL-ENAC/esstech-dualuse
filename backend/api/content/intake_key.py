"""Answer key and scoring rules for the M0 intake.

PLACEHOLDER CONTENT. None of this is validated assessment material: the items,
the correct options, the threshold and the scaffolding rule are all stand-ins
for content that has not been written yet.

This module is the *only* place the correct answers exist. The frontend's
`src/content/intake.ts` carries the same item and option ids with their prompts
and labels, and never carries which option is right; responses report outcomes
(a score, a boolean) and never an option id.

The two files are kept aligned by hand. Changing an id here means changing it
there in the same commit, or scoring silently breaks -- `KeyedItem.options`
exists partly so a mismatch surfaces as a rejected submission rather than as a
wrong score.
"""

from dataclasses import dataclass

from api.models.enums import ScaffoldingDepth


@dataclass(frozen=True)
class KeyedItem:
    """One multiple-choice item, with its valid options and its answer."""

    id: str
    # Every option id the frontend offers for this item. Used to reject
    # unknown ids outright: knowing which ids are *valid* reveals nothing
    # about which one is *correct*.
    options: tuple[str, ...]
    # Never leaves the backend, in any response, at any point in the flow.
    correct: str


DIAGNOSTIC_ITEMS: tuple[KeyedItem, ...] = (
    KeyedItem(id="d1", options=("d1a", "d1b", "d1c", "d1d"), correct="d1c"),
    KeyedItem(id="d2", options=("d2a", "d2b", "d2c", "d2d"), correct="d2a"),
    KeyedItem(id="d3", options=("d3a", "d3b", "d3c", "d3d"), correct="d3b"),
)

COMPREHENSION_ITEM = KeyedItem(id="c1", options=("c1a", "c1b", "c1c"), correct="c1b")

# Score at or above this and the micro-primer is skipped. Placeholder: 2 of 3.
DIAGNOSTIC_THRESHOLD = 2


def score_diagnostic(answers: list[str]) -> int:
    """Count how many of the submitted option ids are the correct ones.

    Answers are positional: the nth answer belongs to the nth item in
    DIAGNOSTIC_ITEMS. Validation of length and membership happens in the
    service before this is called.
    """

    return sum(
        1
        for item, answer in zip(DIAGNOSTIC_ITEMS, answers, strict=True)
        if answer == item.correct
    )


def derive_scaffolding_depth(
    *, above_threshold: bool, comprehension_correct: bool
) -> ScaffoldingDepth:
    """Pick a scaffolding depth from the two intake outcomes.

    PLACEHOLDER RULE, and a deliberately crude one: two signals collapsed onto
    three levels, with no weighting and no evidence behind the cut points. It
    lives here beside the answer key so the whole guessed-at part of M0 is one
    deletable file.
    """

    signals = sum((above_threshold, comprehension_correct))
    if signals == 2:
        return ScaffoldingDepth.LOW
    if signals == 1:
        return ScaffoldingDepth.STANDARD
    return ScaffoldingDepth.HIGH
