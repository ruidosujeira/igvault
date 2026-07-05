# VHS tape for igvault demo
# https://github.com/charmbracelet/vhs

Output assets/igvault-demo.gif

Set FontSize 16
Set Width 1200
Set Height 680
Set Theme "Catppuccin Mocha"
Set Padding 10
Set Margin 8
Set Framerate 24
Set Shell "zsh"

# Make sure igvault is in PATH (adjust for your machine after `pip install -e .`)
Env PATH "/Library/Frameworks/Python.framework/Versions/3.13/bin:/usr/local/bin:/usr/bin:/bin"

Type "clear"
Enter
Sleep 200ms

Type "igvault --help"
Enter
Sleep 1.8s

Type "clear"
Enter
Sleep 200ms

Type "igvault reels @nasa --limit 3 --dry-run"
Enter
Sleep 2.8s

Type "clear"
Enter
Sleep 200ms

Type "igvault profile @instagram --limit 2 --dry-run"
Enter
Sleep 2.5s

Type "clear"
Enter
Sleep 200ms

Type "igvault bulk profiles.txt --limit 2 --dry-run"
Enter
Sleep 3.2s

Type "clear"
Enter
Sleep 200ms

Type "igvault reels @nasa --limit 1"
Enter
Sleep 5s

Type "ls downloads/@nasa/reels/"
Enter
Sleep 800ms
