# Render the second GIF (the instrumentation self-audit) with charmbracelet/vhs:
#
#   vhs docs/check.tape     -> writes docs/check.gif
#
# This one belongs further down the README, in the "Check your own logging"
# section, where the reader already has the context.

Output docs/check.gif

Set Shell bash
Set FontSize 14
Set Width 1200
Set Height 720
Set Padding 20
Set Theme "Catppuccin Mocha"

Sleep 700ms
Type "python3 -m oversight_audit check examples/typical_audit_schema.json"
Sleep 500ms
Enter
Sleep 10s
