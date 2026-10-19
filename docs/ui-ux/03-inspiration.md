# UI/UX Checkpoint 03 — Inspiration & Decisions

**Date**: 2026-10-19 · **Author**: UI_UX_DESIGNER · **Resume point for Steps 04–08**

```yaml
platform: web_desktop_only
tech: {templates: django, interactivity: htmx_2, css: plain_tokens, cdn: none}
emotion:
  student: friendly_playful   # warm accents, rounded, larger type, one task per screen
  staff: calm_efficient       # teacher, parent, admin
colour_psychology:
  primary: teal_blue          # trust + calm (staff), friendly when paired with warm accents
  student_accent: warm_yellow_orange
  avoid: red_as_main_colour   # red reads as "wrong" to children; error states only
design_system: custom
density: {student: low, staff: medium}
navigation: top_bar
error_display: inline_plus_top_banner
loading: button_spinner_disable
a11y: wcag_aa
inspiration: childrens_learning_best_practice  # large cards, single primary action, friendly icons
responsive: desktop_only
```
