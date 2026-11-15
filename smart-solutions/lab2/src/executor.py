"""High-level execution boundary; this module never imports an MG400 client."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Protocol

from .models import AtomLetterJob, AtomPickPlaceJob, STABLE_REASONS


DEFAULT_LAB1_LETTERS = (
    Path(__file__).resolve().parents[2] / "lab1" / "config" / "letters.json"
)
# Lab 1 station draws letters missing from letters.json with this single-stroke
# font (station.py --letter-font, default "futural"); the catalog mirrors that.
DEFAULT_LAB1_FONT = DEFAULT_LAB1_LETTERS.parent / "fonts" / "futural.json"


@dataclass(frozen=True)
class ExecutionOutcome:
    status: str
    reason: str | None = None
    completion_confirmed: bool = False

    def __post_init__(self) -> None:
        if type(self.completion_confirmed) is not bool or (
            self.completion_confirmed and (self.status != "done" or self.reason is not None)
        ):
            raise ValueError("confirmed completion requires done without a refusal reason")

    @classmethod
    def done(cls, *, completion_confirmed: bool = False) -> "ExecutionOutcome":
        return cls("done", completion_confirmed=completion_confirmed)

    @classmethod
    def refused(cls, reason: str) -> "ExecutionOutcome":
        if reason not in STABLE_REASONS:
            raise ValueError("mock executor refusal reason is not stable")
        return cls("refused", reason)


class LetterExecutor(Protocol):
    @property
    def ready(self) -> bool: ...

    def execute_letter(
        self,
        letter: str,
        job_id: str,
        *,
        session: str,
        seq: int,
        atom_sent_ms: int | None,
    ) -> ExecutionOutcome: ...


class PickPlaceExecutor(Protocol):
    @property
    def ready(self) -> bool: ...

    def execute_pick_place(
        self,
        routine: str,
        job_id: str,
        *,
        session: str,
        seq: int,
        atom_sent_ms: int | None,
    ) -> ExecutionOutcome: ...


class Lab1LetterCatalog:
    """Read configured letters from Lab 1's canonical trajectory data.

    Loading the data file avoids changing Lab 1 or mutating ``sys.path`` only
    to import its script-style modules. Motion data never enters this adapter.
    """

    def __init__(
        self,
        path: str | Path = DEFAULT_LAB1_LETTERS,
        font_path: str | Path | None = DEFAULT_LAB1_FONT,
    ) -> None:
        source = Path(path)
        try:
            document = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise RuntimeError("Lab 1 letter catalog is unavailable") from exc
        if not isinstance(document, dict):
            raise RuntimeError("Lab 1 letter catalog has an unsupported format")
        letters = document.get("letters")
        if document.get("version") != 1 or not isinstance(letters, dict):
            raise RuntimeError("Lab 1 letter catalog has an unsupported format")
        self.letters = frozenset(
            letter
            for letter, definition in letters.items()
            if isinstance(letter, str)
            and len(letter) == 1
            and "A" <= letter <= "Z"
            and isinstance(definition, dict)
            and isinstance(definition.get("strokes"), list)
            and bool(definition["strokes"])
        ) | self._font_letters(font_path)

    @staticmethod
    def _font_letters(font_path: str | Path | None) -> frozenset[str]:
        if font_path is None:
            return frozenset()
        try:
            glyphs = json.loads(Path(font_path).read_text(encoding="utf-8")).get("glyphs", {})
        except (OSError, json.JSONDecodeError, AttributeError) as exc:
            raise RuntimeError("Lab 1 letter font is unavailable") from exc
        return frozenset(
            letter for letter, glyph in glyphs.items()
            if isinstance(letter, str) and len(letter) == 1 and "A" <= letter <= "Z" and glyph
        )

    def supports(self, letter: str) -> bool:
        return letter in self.letters


class MockLetterExecutor:
    """Controlled software-only executor used by tests and the local demo."""

    def __init__(
        self,
        *,
        ready: bool = True,
        refusals: dict[str, str] | None = None,
        failures: set[str] | None = None,
    ) -> None:
        self._ready = ready
        self.refusals = refusals or {}
        self.failures = failures or set()
        self.calls: list[AtomLetterJob] = []

    @property
    def ready(self) -> bool:
        return self._ready

    def execute_letter(
        self,
        letter: str,
        job_id: str,
        *,
        session: str,
        seq: int,
        atom_sent_ms: int | None,
    ) -> ExecutionOutcome:
        job = AtomLetterJob(letter, session, seq, job_id, atom_sent_ms)
        self.calls.append(job)
        if letter in self.failures:
            raise RuntimeError("controlled mock failure")
        if letter in self.refusals:
            return ExecutionOutcome.refused(self.refusals[letter])
        return ExecutionOutcome.done()


class MockPickPlaceExecutor:
    """Deterministic software-only executor; it has no hardware or network code."""

    hardware_used = False

    def __init__(self, *, ready: bool = True) -> None:
        self._ready = ready
        self.calls: list[AtomPickPlaceJob] = []

    @property
    def ready(self) -> bool:
        return self._ready

    def execute_pick_place(
        self,
        routine: str,
        job_id: str,
        *,
        session: str,
        seq: int,
        atom_sent_ms: int | None,
    ) -> ExecutionOutcome:
        if routine != "source_to_finished":
            return ExecutionOutcome.refused("invalid_routine")
        self.calls.append(AtomPickPlaceJob(routine, session, seq, job_id, atom_sent_ms))
        return ExecutionOutcome.done()
