```yaml
version: 1.0
platform: web_desktop_only
tech_stack: [django, htmx, css_tokens]
detail: docs/ui-ux/08-visual-foundation.md
design_tokens:
  colors: {primary: "#0E7490", primary_hover: "#155E75", accent: "#FBBF24", focus: "#C2410C", success: "#15803D", error: "#B91C1C", warning: "#B45309", text: "#1F2937", muted: "#4B5563", border: "#6B7280", bg_student: "#FFF8EC", bg_staff: "#F5F7FA", surface: "#FFF", disabled: "#F3F4F6"}
  pills_bg_fg: {ACTIVE: DCFCE7/14532D, FLAGGED: FEF3C7/78350F, BLOCKED: FEE2E2/7F1D1D, RESUBMITTED: CFFAFE/164E63, DRAFT: F3F4F6/1F2937, PUBLISHED: CFFAFE/164E63}
  breakpoints: {lg: 1024px, xl: 1280px}
  spacing: {unit: 4px, student: [8,16,24,32,48,64], staff: [4,8,12,16,24,32,48]}
  typography: {font: Atkinson Hyperlegible Next, base: {student: 18px, staff: 16px}, scale: [14,16,18,20,24,32,40], weights: [400,600,700]}
  radius: {student: 16px, staff: 8px}
  elevation: [none, card, menu, dialog]
  touch_targets: {min: 32px, student: 44px}
  icons: {set: phosphor, student: duotone, staff: regular}
responsive_behavior:
  layout: {nav: top_bar_64px, grid: 12_col, max_width: {student: 960px, staff: 1200px}, below_lg: scroll, editors: ro_en_side_by_side}
ux_logic:
  validation: on_submit
  error_display: inline+top_banner
  success_feedback: {staff: banner, student: in_place}
  loading_states: button_spinner_disable
  navigation: top_bar_role_menu
  data_density: {student: low, staff: medium}
component_map: {navigation: top_bar, forms: form_field, tables: data_table, modals: confirm_dialog, notifications: [badge, alert]}
user_journey:
  primary_path: catalogue>chapter>lesson>exercises>test>score
  critical: [author_publish, block_resubmit, parent_progress]
a11y: {level: AA, focus: 3px_outline, keyboard: [skip_link, dialog_trap_esc], aria_labels: required, contrast: {text: 4.5, ui: 3}, sr: [semantic_html, aria_live, lang]}
patterns: {confirm: [test_submit, block, clear, publish], empty_states: all_lists, bulk_actions: none, filters: staff_inline_get}
```
