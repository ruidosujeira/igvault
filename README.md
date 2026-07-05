# igvault

**A simple, clean, and reliable CLI for downloading public Instagram Reels.**

Exclusive focus on public Reels. No login required. Strong anti-ban protection enabled by default.

![Demo](assets/igvault-demo.gif)

*Demo generated with [VHS](https://github.com/charmbracelet/vhs) from Charmbracelet.*

## ✨ Features

- Download Reels from any public profile (`@username`)
- Organized output: `./downloads/@username/reels/`
- Valid and playable `.mp4` files
- Humanized delays (3-9s) with stealth mobile + browser headers
- Intelligent rate limiting and cooldowns between profiles
- `--dry-run` mode for instant testing
- Beautiful modern CLI powered by Rich (colors, progress bars, panels)
- Intuitive commands: `reels`, `profile`, `bulk`

## 📦 Installation

```bash
# 1. Clone or download the project
cd igvault

# 2. Install in editable mode (recommended)
pip install -e .

# Or run directly using the module
python3 -m igvault.cli --help
```

## 🚀 Usage

### Download Reels from a profile

```bash
# Download up to 10 reels (default)
igvault reels @nasa

# Limit the number of reels
igvault reels @instagram --limit 5

# 'profile' alias
igvault profile nasa --limit 3

# Test without actually downloading (recommended first)
igvault reels @nasa --limit 5 --dry-run
```

### Bulk mode (multiple profiles)

Create a `profiles.txt` file:

```
nasa
instagram
# comments are ignored
```

```bash
igvault bulk profiles.txt --limit 4
igvault bulk profiles.txt --limit 4 --dry-run
```

### Help

```bash
igvault --help
igvault reels --help
igvault bulk --help
```

## 📁 Output Structure

```
downloads/
└── @nasa/
    └── reels/
        ├── Cxyz1234.mp4
        ├── Cabc9876.mp4
        └── ...
```

## 🛡️ Anti-ban (always active)

- Random human-like delays between 3 and 9.5 seconds
- Realistic mobile User-Agents + complete browser-like headers
- 10-18s cooldown between different profiles in bulk operations
- No cookies or login — public content only
- Proper redirect following and safe timeouts

## ✅ Requirements

- Python 3.10+
- httpx, rich, typer

Installed automatically with `pip install -e .`

## ⚠️ Important Notes

- Only works with **public** profiles
- Use responsibly
- Instagram may change their web interface at any time (this project uses public methods)
- For heavy usage, consider using proxies or longer intervals

## 🧪 Quick Test (macOS)

```bash
pip install -e .
igvault reels @instagram --limit 2 --dry-run
igvault reels @nasa --limit 1
```

Downloaded files should play normally in QuickTime, VLC, or any media player.

---

Built to be simple, robust, and work out of the box.