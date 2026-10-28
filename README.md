# Heterodyne FM catalog

Radio station lists for the [Heterodyne FM](https://github.com/krasotinpa/heterodyne-fm) Android app.
The app takes only releases of this repository, never the `main` branch.

## Terms

| Term | Meaning |
|---|---|
| Catalog | The list of radio stations of one Region. |
| Region | A geographic area with its own Catalog, for example Moscow. |
| Station | A radio station with a name and an FM frequency. |
| Revision | A date. A Region file and a Catalog set each have one. The app accepts a set only if its Revision is newer than the current one. |
| Catalog set | All Regions of one release. |

## Layout

```text
regions/<id>.json          one Region, schema 1
scripts/catalog.py         validation and release build (Python 3, standard library only)
tests/                     unit tests and fixtures; the app copies the fixtures
```

`index.json` is not stored here. A release builds it from the Region files.

## Release assets

Each release `vYYYY-MM-DD` contains these files. The names carry no folders.

1. `index.json`: `schema`, the set `revision`, and for each Region `id`, `name`, `file`, `sha256`, `revision`.
2. One `<id>.json` file for each Region.
3. `catalog-<revision>.zip`: all the files above, for import without a network.

Permanent address of the latest `index.json`:
`https://github.com/krasotinpa/heterodyne-fm-catalog/releases/latest/download/index.json`

## Check your changes

```sh
python3 scripts/catalog.py validate            # rules
python3 scripts/catalog.py validate --base origin/main   # also checks that revision changed
python3 -m unittest discover -s tests          # tests
```

Limits: a Region file is at most 64 KiB and has at most 500 Stations. A name has at most 80 characters.
A set has at most 100 Regions. `index.json` is at most 32 KiB and the ZIP at most 8 MiB.
The app applies the same rules and rejects the whole set on any violation.

See [CONTRIBUTING.md](CONTRIBUTING.md) to add or change data, and [PROVENANCE.md](PROVENANCE.md) for the data sources.

## License

The data is licensed under [CC BY 4.0](LICENSE). Attribute "Heterodyne FM catalog contributors" and keep each Region's `source`.
The scripts in `scripts/` and `tests/` are licensed under [GPL-3.0-or-later](LICENSES/GPL-3.0-or-later.txt).
