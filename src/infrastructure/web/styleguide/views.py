"""GET /<lang>/_styleguide/ — every atom and variant in both themes (DEBUG only, never deployed)."""

from dataclasses import dataclass

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from infrastructure.web.templatetags.ui import ICON_NAMES, ICON_SIZES, STATUS_LABELS


@dataclass(frozen=True)
class Swatch:
    """A colour token, its spec value and the colour it is read against (for the contrast note)."""

    token: str
    hex: str
    against: str

    @property
    def slug(self) -> str:
        return self.token.removeprefix("--")

    @property
    def ratio(self) -> str:
        return f"{_contrast(self.hex, self.against):.2f}:1"


@dataclass(frozen=True)
class SampleUser:
    full_name: str

    def get_full_name(self) -> str:
        return self.full_name


SURFACE, TEXT = "#FFFFFF", "#1F2937"
SWATCHES = (
    Swatch("--color-primary", "#0E7490", SURFACE),
    Swatch("--color-primary-hover", "#155E75", SURFACE),
    Swatch("--color-accent", "#FBBF24", TEXT),
    Swatch("--color-focus", "#C2410C", SURFACE),
    Swatch("--color-success", "#15803D", SURFACE),
    Swatch("--color-error", "#B91C1C", SURFACE),
    Swatch("--color-warning", "#B45309", SURFACE),
    Swatch("--color-text", "#1F2937", SURFACE),
    Swatch("--color-muted", "#4B5563", SURFACE),
    Swatch("--color-border", "#6B7280", SURFACE),
    Swatch("--color-bg-student", "#FFF8EC", TEXT),
    Swatch("--color-bg-staff", "#F5F7FA", TEXT),
    Swatch("--color-surface", "#FFFFFF", TEXT),
    Swatch("--color-disabled", "#F3F4F6", "#4B5563"),
    Swatch("--pill-active-bg", "#DCFCE7", "#14532D"),
    Swatch("--pill-flagged-bg", "#FEF3C7", "#78350F"),
    Swatch("--pill-blocked-bg", "#FEE2E2", "#7F1D1D"),
    Swatch("--pill-resubmitted-bg", "#CFFAFE", "#164E63"),
    Swatch("--pill-draft-bg", "#F3F4F6", "#1F2937"),
    Swatch("--pill-published-bg", "#CFFAFE", "#164E63"),
)
SPACES = (1, 2, 3, 4, 6, 8, 12, 16)
TYPE_SCALE = (14, 16, 18, 20, 24, 32, 40)
WEIGHTS = (400, 600, 700)
BUTTONS = (
    ("primary", _("Save"), "check-circle"),
    ("secondary", _("Cancel"), "x-circle"),
    ("danger", _("Delete"), "prohibit"),
    ("link", _("Learn more"), "caret-right"),
)


def _luminance(hex_colour: str) -> float:
    channels = [int(hex_colour.lstrip("#")[i : i + 2], 16) / 255 for i in (0, 2, 4)]
    linear = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    lighter, darker = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (lighter + 0.05) / (darker + 0.05)


def index(request: HttpRequest) -> HttpResponse:
    """Render the reference page; LocaleMiddleware (Story 1.4) activates the prefix language."""
    context = {
        "themes": ["student", "staff"],
        "swatches": SWATCHES,
        "spaces": SPACES,
        "type_scale": TYPE_SCALE,
        "weights": WEIGHTS,
        "buttons": BUTTONS,
        "icon_names": sorted(ICON_NAMES),
        "icon_sizes": sorted(ICON_SIZES),
        "statuses": list(STATUS_LABELS),
        "sample_user": SampleUser("Ana Popescu"),
        "unread_label": _("unread notifications"),
        "progress_label": _("Exercises"),
        "diacritics": "ș ț ă â î Ș Ț Ă Â Î — Matematică și explorarea mediului",
    }
    return render(request, "styleguide/index.html", context)
