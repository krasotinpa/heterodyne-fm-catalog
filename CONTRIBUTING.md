# Contributing

Write PRs, commits and documents in English. Station and Region names stay in the local language.
The owner reviews and merges every PR by hand. CI must pass first.

## Region file rules

1. The file is `regions/<id>.json` with `schema: 1`. Use an existing file as a template.
2. `region.id` equals the file name. Use lowercase latin letters, digits and hyphens.
3. A Station `id` starts with the Region `id` and a hyphen, for example `moskva-radio-7`.
4. Never reuse or rename an `id`. The app keeps user data under it. To remove a Station, delete its entry.
5. `band` is `FM`. `frequencyKhz` is an integer from 87500 to 108000 in steps of 100.
6. Every Region has a `source` with `text` and `url`.
7. Set `revision` to the date of your change. CI rejects a changed file with an unchanged `revision`.
8. Use LF line endings, UTF-8 and one final newline.

## Before you open a PR

1. Run the checks from [README.md](README.md#check-your-changes).
2. Confirm in the PR that your source allows this use under CC BY 4.0.
3. Do not add personal data of any person to the files or to the PR.

## Release (owner only)

1. Pick the date of the release. It must not be earlier than the previous release.
2. Tag a commit on `main` as `vYYYY-MM-DD`. For a second release on the same day use `vYYYY-MM-DD-2`.
3. Push the tag. CI recomputes all SHA-256 values and publishes `index.json`, the Region files and the ZIP.

Never edit hashes by hand.
