/*
 * ui.js — behaviour for the Story 1.6 molecules (confirm dialog, dismissible alert).
 *
 * CSP: the app sends `script-src 'self'`, so this is a same-origin static ES module
 * (<script type="module" src>), with no inline handlers, no dynamic code evaluation and no globals.
 * Progressive enhancement: without JS the dialog trigger shows a <noscript> notice and alerts
 * simply stay visible. Event delegation on `document` covers markup added later (e.g. htmx swaps).
 *
 *   [data-dialog-open="<dialog id>"]  opens that <dialog> modally and focuses its first control.
 *   [data-dialog-close]              closes the enclosing <dialog>; Esc does the same natively.
 *   [data-dismiss]                   removes the enclosing .alert.
 * On close, focus returns to the control that opened the dialog.
 */

const openers = new WeakMap();

document.addEventListener('click', (event) => {
  if (!(event.target instanceof Element)) {
    return;
  }

  const opener = event.target.closest('[data-dialog-open]');
  if (opener) {
    const dialog = document.getElementById(opener.dataset.dialogOpen);
    if (dialog instanceof HTMLDialogElement && !dialog.open) {
      openers.set(dialog, opener);
      dialog.showModal();
      // The dialog form starts with hidden inputs (CSRF), which cannot take focus: skip them.
      const controls = dialog.querySelectorAll('input, textarea, select, button');
      Array.from(controls).find((control) => control.type !== 'hidden')?.focus();
    }
    return;
  }

  const closer = event.target.closest('[data-dialog-close]');
  if (closer) {
    closer.closest('dialog')?.close();
    return;
  }

  const dismiss = event.target.closest('[data-dismiss]');
  if (dismiss) {
    dismiss.closest('.alert')?.remove();
  }
});

// `close` does not bubble, so listen in the capture phase. Esc fires the native `cancel`
// event, which closes the dialog without submitting its form; this restores focus either way.
document.addEventListener('close', (event) => {
  if (event.target instanceof HTMLDialogElement) {
    openers.get(event.target)?.focus();
    openers.delete(event.target);
  }
}, true);
