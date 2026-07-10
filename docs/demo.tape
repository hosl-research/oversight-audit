# Render the hero GIF with charmbracelet/vhs:
#
#   brew install vhs        (or: go install github.com/charmbracelet/vhs@latest)
#   vhs docs/demo.tape      -> writes docs/demo.gif
#
# One command, one idea. No `clear`, so the closing lines stay on screen, and a
# long final hold so a viewer can read the table before the GIF loops.

Output docs/demo.gif

Set Shell bash
Set FontSize 14
Set Width 1200
Set Height 860
Set Padding 20
Set Theme "Catppuccin Mocha"

Sleep 700ms
Type "python3 -m oversight_audit demo"
Sleep 500ms
Enter
Sleep 12s
