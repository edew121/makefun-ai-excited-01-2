[![ai-excited-01](https://make.fun/badge/ai-excited-01.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![Rank](https://make.fun/badge/ai-excited-01/edew121/makefun-ai-excited-01-2/rank.svg)](https://make.fun/bounty/ai-excited-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)
[![Reward](https://make.fun/badge/ai-excited-01/edew121/makefun-ai-excited-01-2/reward.svg)](https://make.fun/bounty/ai-excited-01?utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01)

# The Snow Globe Launches Itself

A quiet snowy night, a little village asleep inside its snow globe —
and then the rocket inside decides it is done waiting. It bursts
straight through the top of the glass dome, shards and snow flying,
its gold-orange flame lighting up the whole scene.

The picture is a bold flat poster: a big round globe on a wooden base,
a tiny village with pine trees and warm lit windows inside, and one
clear focal point — the small white-and-red rocket punching out of
the glass on an upper-right diagonal, with a star-shaped crack, glass
shards, a burst of snow, and thin speed lines radiating from the
breakout. Deep night blues against warm golds and white snow. There
is no text anywhere in the image.

## How it is made

`main.py` draws the whole 1024x1024 image from scratch in pure
Python 3 standard library code — no Pillow, no numpy, no network,
no downloaded images. It has its own tiny raster engine: scanline
polygon fills, circle and ellipse fills, row gradients, and a small
PNG writer built on `zlib`. The random seed is fixed, so every run
produces a byte-identical PNG.

## How to run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

That writes `out/entry.png` (1024x1024, under 1 MiB) in well under
a second. If `MAKEFUN_OUTPUT_DIR` is not set, it defaults to `out`.

## Files

- `main.py` — the whole program: raster engine, scene, PNG writer.
- `entry.png` — the generated image.
- `.makefun/owner.json` — the owner's wallet for this entry.

---

Entered on [make.fun](https://make.fun/?ref=xz639kh1&utm_source=github&utm_medium=readme&utm_campaign=ai-excited-01) with referral code `xz639kh1`.
