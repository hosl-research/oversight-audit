# Render the demo as a GIF with charmbracelet/vhs:
#
#   brew install vhs        (or: go install github.com/charmbracelet/vhs@latest)
#   vhs docs/demo.tape      -> writes docs/demo.gif
#
# Drop the result into the README to give people the result before they clone.

Output docs/demo.gif

Set Shell bash
Set FontSize 14
Set Width 1100
Set Height 780
Set Padding 18
Set Theme "Catppuccin Mocha"

Sleep 500ms
Type "python3 -m oversight_audit demo"
Sleep 400ms
Enter
Sleep 6s

Type "clear"
Enter
Sleep 300ms

Type "python3 -m oversight_audit check examples/typical_audit_schema.json"
Sleep 400ms
Enter
Sleep 6s
