## grepip

`grepip` is a utility help to search the occurrances of strings in the source codes given a PyPI package.
Initially, it was designed to serve for the purpose of find the impact scope the when deprecating and removing a public C API from CPython.

You need a [GitHub personal access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens) (without any permissions) to fetch the artifact URLs for a repository.

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

## Acknowledgements

- https://hugovk.github.io/top-pypi-packages/
