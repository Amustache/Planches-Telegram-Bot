# Planches Telegram Bot
Telegram bot for https://planches.arnalo.ch/

## Setup

## Usage
### API
API from https://gitlab.com/maltherd/planches/-/blob/master/planches/main/urls.py

`````python
ENDPOINT = "https://planches.arnalo.ch/api/{board}/{op}"
BOARDS = ["b", "n", "c", "smol"]
OPS = ["", "ops", "post/{num}"]
`````

### Commands
- /sub \<board>: Get new updates from a board
- /unsub \<board>: Unsub from a board
- /list: Show currently subscribed boards
- /read \<board>: List last five OPs of a board
- (Soon ™️) Reply to a post: 🤷‍♀️
