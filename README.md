This is entirely a frontend application, so you can run it pretty easily on your own computer.

Your browser makes the request directly to the Lichess API to get the games. Then the games are analyzed with javascript (again, in your own browser). Each move from every game is played through and analyzed for specific positions or other criteria.

## Setup
***You must install git, and bun or npm, preferably bun***

```bash
git clone https://github.com/manjaroblack/holygambitgrail.git
cd holygambitgrail
bun install
bun run dev
```

Will start a local server at http://localhost:5173/

```bash
## Run the test suite
bun run test
## or
bun run watch

## Check code coverage
bun run coverage
open coverage/index.html
```

To build for a production website

```bash
## From within the holygambitgrail folder
bun run build
## This will create a folder: ./build which contains the files to deploy to your web host
```

To enable the youtube links, you will need to configure the YouTube API, which is outside the scope of this tutorial. 

For setup assistance, post a question to the [VampireChicken Discord Channel #code-and-scripting](https://discord.gg/3MgpdBf4Eb)

## Frameworks/Libraries Used

-   [chess.js](https://github.com/jhlywa/chess.js), [chessops](https://github.com/niklasf/chessops), [pgn-parser](https://github.com/mliebelt/pgn-parser) - JS chess libraries to handle chess logic
-   Vue.js - Framework for building the app
-   Tailwind - CSS framework for the UI

## Understanding How It Works

### Piece Structures

FENs are converted to a 64-character string representing the position:

```js
// Starting position FEN
let fen = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'

// Convert the FEN to a 64-character string that starts at a8 and ends at h1
let position = fenToPosition(fen)
// rnbqkbnrpppppppp................................PPPPPPPPRNBQKBNR
```

And now you can do regex to look for pawn/piece structures:

```js
// To look for a white pawn cube, it is essentially:
position.match(/PP([A-Za-z\.]{6})PP/) // 2 white pawns, 6 squares, then 2 white pawns
```
##
This project was copied from https://github.com/fitztrev/rosen-score
