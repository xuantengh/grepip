import grepip.search as gs
import grepip.pypi as gp
from tqdm.asyncio import tqdm
from aiolimiter import AsyncLimiter


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="Search code snippets in GitHub.")
    parser_group = parser.add_mutually_exclusive_group(required=True)
    parser_group.add_argument(
        "-p", "--package", type=str, help="PyPI package to search for"
    )
    parser_group.add_argument(
        "-t", "--top", type=int, help="Number of top PyPI packages to search"
    )

    parser.add_argument("--pattern", type=str, help="Search pattern")
    args = parser.parse_args()

    targets: list[str] = []
    if args.top:
        popular_packages = await gp.fetch_popular_pypi_packages()
        targets: list[str] = popular_packages[: args.top]
    elif args.package:
        targets = [args.package]
    else:
        raise ValueError("Either --top or --package must be specified")

    tasks: list[asyncio.Task] = []
    async with asyncio.TaskGroup() as tg:
        for pkg in targets:
            tasks.append(tg.create_task(gp.fetch_pypi_package_info(pkg)))

    valid_pkgs: list[gp.PypiPackageInfo] = []
    for task in tasks:
        pkg_info: gp.PypiPackageInfo = task.result()
        if gs.gh.GitHubSearch.is_acceptable(pkg_info.source_url):
            valid_pkgs.append(pkg_info)

    tasks = []
    with tqdm(total=len(valid_pkgs), desc="Downloading and searching") as pbar:
        async with asyncio.TaskGroup() as tg, AsyncLimiter(30, 60):
            for pkg_info in valid_pkgs:
                searcher = gs.gh.GitHubSearch()
                task = tg.create_task(
                    searcher.download_and_zgrep(pkg_info.source_url, args.pattern)
                )
                task.add_done_callback(lambda t: pbar.update(1))
                tasks.append(task)

    results = await asyncio.gather(*tasks)
    for i, result in enumerate(results):
        print(valid_pkgs[i].name)
        if len(result) > 0:
            for line in result:
                print(f"\t{line}")
        print("-" * 20)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
