## Library-first convention (prior-art plugin)

The user installed the prior-art plugin. Its convention for code written in this session: before hand-writing code for a problem that is already solved, reuse an existing solution, taking the first that fits.

1. This codebase: an existing helper or pattern. Search before writing.
2. The standard library or platform. Python: argparse, csv, json, tomllib, datetime + zoneinfo, secrets, pathlib, urllib.parse, difflib, functools.cache, itertools, dataclasses, logging. JS/TS: URL, URLSearchParams, structuredClone, Intl (dates, numbers, plurals), crypto.randomUUID, fetch, AbortController, util.parseArgs.
3. A dependency that is already installed. The manifest (package.json, pyproject.toml, requirements*.txt, go.mod, Cargo.toml) lists what is available; read it before writing.
4. A well-known, maintained library, when a hand-written version would run past ~20 lines or falls in a listed area. Adding it is expected: add it to the manifest and name it in one line.
5. Hand-written code, kept small, only when none of the above fits.

Listed areas, where the check always applies: parsing or writing a format (CSV, JSON, YAML, TOML, XML, HTML, Markdown, URLs, query strings); dates, times and time zones; CLI arguments; validating emails, URLs or UUIDs; parsing or comparing versions; crypto, hashing, random tokens and passwords; auth and sessions; retries, backoff and rate limits; HTTP clients; concurrency and queues; caching; diffing and fuzzy matching; Unicode and slugs; deep clone, merge or equality; money and currency formatting.

No new dependency for what the standard library or one line already does.
After writing code in a listed area, the reply names what was reused in one line, e.g. "Used argparse instead of parsing sys.argv by hand."
Hard-to-undo choices (a framework, a datastore, an architecture) go through the prior-art skill's research mode instead of being picked inline.
