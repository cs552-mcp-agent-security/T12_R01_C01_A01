# Algorithm: token bucket

Each bucket has two parameters set at construction:

- `capacity`: maximum tokens in the bucket
- `refill_per_sec`: tokens regenerated per real second, capped at `capacity`

On each `check(key, cost=1)` call:

1. Read `tokens` and `ts` (timestamp of last update) from the bucket.
2. Compute `tokens += (now - ts) * refill_per_sec`, capped at `capacity`.
3. If `tokens >= cost`, decrement and return `(allowed=True, remaining)`.
4. Otherwise, leave `tokens` unchanged and return `(allowed=False, remaining)`.
5. Persist `tokens` and `ts = now`.

## Why an atomic script

Steps 1–5 must run without interleaving from other clients against
the same key. If two clients each independently `GET` + recompute +
`SET`, both can see the same starting state and each decrement, but
only the last `SET` wins — effectively allowing one of them through
even though combined cost exceeds available tokens. Putting the whole
sequence in a Lua script run via `EVAL`/`EVALSHA` makes it execute
as a single Redis command, removing the interleaving window.

This is the only reason the implementation uses Lua rather than a
plain sequence of Python-side Redis calls.
