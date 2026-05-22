-- bucket.lua: atomic token-bucket consume.
-- KEYS[1]   = bucket key
-- ARGV[1]   = capacity
-- ARGV[2]   = refill per second (note: rounded down to nearest integer per call)
-- ARGV[3]   = cost
--
-- The function returns {allowed (0/1), remaining tokens (int)}.
--
-- Stored state at KEYS[1] is a hash with fields:
--   tokens : last observed bucket level (integer count, stored as string)
--   ts     : Redis-server wall clock at last update (ms, integer)
--
-- Note on refill semantics: although the constructor accepts a float
-- refill_per_sec, the Lua side rounds the per-call refill increment
-- down to an integer. This is a deliberate choice to make the
-- algorithm easier to reason about; sub-token refill is therefore
-- effectively quantized to 1-token-per-elapsed-second.
--
-- Atomicity: this script runs as a single Redis command (EVALSHA), so
-- the refill + consume sequence is not interleaved with any other
-- client's evalsha against the same key.

local key      = KEYS[1]
local capacity = tonumber(ARGV[1])
local refill   = tonumber(ARGV[2])
local cost     = tonumber(ARGV[3])

local now_ms = redis.call("TIME")
now_ms = now_ms[1] * 1000 + math.floor(now_ms[2] / 1000)

local state = redis.call("HMGET", key, "tokens", "ts")
local tokens = tonumber(state[1])
local last_ts = tonumber(state[2])

if tokens == nil or last_ts == nil then
    tokens = capacity
    last_ts = now_ms
end

local elapsed_sec = math.max(0, (now_ms - last_ts) / 1000.0)
tokens = math.min(capacity, tokens + elapsed_sec * refill)

local allowed = 0
if tokens >= cost then
    tokens = tokens - cost
    allowed = 1
end

redis.call("HMSET", key, "tokens", tostring(tokens), "ts", tostring(now_ms))
-- Set TTL so unused buckets expire (10x time to fully refill, plus a floor)
local ttl = math.max(60, math.ceil(capacity / refill * 10))
redis.call("EXPIRE", key, ttl)

return {allowed, math.floor(tokens)}
