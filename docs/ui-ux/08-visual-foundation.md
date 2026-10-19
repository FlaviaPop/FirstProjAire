# UI/UX Checkpoint 08 — Design System & Visual Foundation

**Date**: 2026-10-19 · **Author**: UI_UX_DESIGNER · **Resume point for Steps 09–12**
**Approvals**: Design system (Step 05) approved 2026-10-19 after modification (icons → Phosphor; spacing → role-based) · Visual foundation (Step 08) approved 2026-10-19

```yaml
design_tokens:
  colors:   # all text/UI pairs verified WCAG AA (ratio vs. its background)
    primary: "#0E7490"        # 5.36:1 on #FFF; white text on it 5.36:1
    primary_hover: "#155E75"  # 7.27:1
    accent: "#FBBF24"         # student highlight fill; text on it #1F2937 (8.79:1)
    focus: "#C2410C"          # 3px outline, 5.18:1
    success: "#15803D"        # 5.02:1
    error: "#B91C1C"          # 6.47:1
    warning: "#B45309"        # 5.02:1
    text: "#1F2937"           # 14.68:1
    muted: "#4B5563"          # 7.56:1 (also disabled-tile text on #F3F4F6, ≈6.9:1)
    input_border: "#6B7280"   # 4.83:1
    bg_student: "#FFF8EC"
    bg_staff: "#F5F7FA"
    surface: "#FFFFFF"
    disabled_bg: "#F3F4F6"
    pills:  # tinted bg + dark text, all ≥ 8:1; always paired with a text label
      ACTIVE: {bg: "#DCFCE7", fg: "#14532D"}
      FLAGGED: {bg: "#FEF3C7", fg: "#78350F"}
      BLOCKED: {bg: "#FEE2E2", fg: "#7F1D1D"}
      RESUBMITTED: {bg: "#CFFAFE", fg: "#164E63"}
      DRAFT: {bg: "#F3F4F6", fg: "#1F2937"}
      PUBLISHED: {bg: "#CFFAFE", fg: "#164E63"}
  spacing:
    unit: 4px
    student: [8, 16, 24, 32, 48, 64]
    staff: [4, 8, 12, 16, 24, 32, 48]
  typography:
    font_family: "'Atkinson Hyperlegible Next', system-ui, sans-serif"  # self-hosted woff2; verify ș ț ă â î
    base: {student: 18px, staff: 16px}
    scale: [14, 16, 18, 20, 24, 32, 40]
    weights: [400, 600, 700]
    line_height: {body: 1.6, heading: 1.25}
  radius: {student: 16px, staff: 8px, pill: 999px}
  elevation:
    0: none
    1: "0 1px 2px rgba(31,41,55,.08), 0 1px 3px rgba(31,41,55,.12)"   # cards
    2: "0 4px 8px rgba(31,41,55,.12)"                                   # menus
    3: "0 12px 32px rgba(31,41,55,.24)"                                 # dialog
  icons: {set: phosphor, source: local_svg_sprite, student: duotone, staff: regular, sizes: [20, 24, 32]}
  touch_targets: {desktop_min: 32px, student_controls: 44px}

visual_foundation:
  hierarchy:
    atoms: [button, icon, badge, status_pill, avatar, score, progress_meter]
    molecules: [form_field, alert, card, disabled_tile, empty_state, language_switcher, page_header, confirm_dialog, data_table]
    organisms_feature_local: [top_bar, catalogue_grid, lesson_reader, exercise_card, test_form, test_editor, teacher_dashboard, moderation_queue, progress_table, pilot_dashboard]
  grid: {columns: 12, gutter: 24px}
  content_max_width: {student: 960px, staff: 1200px}
  breakpoints: {lg: 1024px, xl: 1280px}   # desktop-only; <1024 no reflow, horizontal scroll allowed
  navigation: {type: top_bar, height: 64px, fixed: true, items: role_specific_3_to_5, right: [language_switcher, notification_badge_teacher, avatar_menu]}
  layout:
    student: {primary_actions_per_screen: 1, card_grid: 3_columns}
    staff: {tables: full_width, editors: two_columns_ro_en_side_by_side}
```
