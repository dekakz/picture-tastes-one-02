# The Picture That Tastes of One — Glossy Burger

[![make.fun](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047.svg)](https://make.fun/competitions/the-picture-that-tastes-of-one-20261122-2047)
[![rank](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/dekakz/picture-tastes-one-02/rank.svg)](https://make.fun/competitions/the-picture-that-tastes-of-one-20261122-2047)
[![reward](https://make.fun/badge/the-picture-that-tastes-of-one-20261122-2047/dekakz/picture-tastes-one-02/reward.svg)](https://make.fun/competitions/the-picture-that-tastes-of-one-20261122-2047)

Entry for the [make.fun competition "the-picture-that-tastes-of-one-20261122-2047"](https://make.fun/competitions/the-picture-that-tastes-of-one-20261122-2047).

## What it is

One picture of food that you can almost taste: a big glossy cheeseburger,
drawn from scratch in pure Python. A golden toasted sesame bun with a buttery
sheen, a sheet of bright melted cheese dripping down over fresh green
lettuce and red tomato, a thick juicy patty, all on a dark plate under warm
light from above. No text in the image — the food alone has to win.

## How it works

`main.py` uses only the Python 3.13 standard library — no PIL, no network.
It draws the burger with its own small raster helpers (scanline ellipse
fills with vertical gradients, per-column wavy shapes for the lettuce and
cheese drips, soft radial highlights, deterministic speckles for baked and
grilled texture) and encodes the result with its own PNG writer
(`zlib` + `struct`).

Run it:

```sh
python3 main.py
```

It writes a 1024×1024 PNG to `/output/entry.png` in under two seconds.

## License

MIT — see [LICENSE](LICENSE).
