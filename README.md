## grepip

`grepip` is a utility help to search the occurrances of regex strings in the source codes given a PyPI package.
It is designed to serve for the purpose of find the impact scope the when deprecating and removing a public C API from CPython, initially.

You need a GitHub personal access token (without any permissions) to search code online.

## Run

```bash
export GITHUB_TOKEN="<your token>"
# search the top 100 popular packages for string "PyWeakref_GetObject"
python -m grepip.run -t 100 --pattern PyWeakref_GetObject
# search on a specific pacakge
python -m grepip.run -p pygame --pattern PyWeakref_GetObject
python -m grepip.run -p cupy --pattern cudaMemcpy
```

## Tests

```bash
export GITHUB_TOKEN="<your token>"
python3 -m unittest
```

## Acknowledgement

- https://hugovk.github.io/top-pypi-packages/