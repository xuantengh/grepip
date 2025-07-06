import aiolimiter
import grepip.search as gs
import grepip.pypi as gp


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
    parser.add_argument(
        "--languages",
        nargs="*",
        default=None,
        help="List of programming languages to filter results",
    )
    args = parser.parse_args()

    targets: list[str] = []
    if args.top:
        popular_packages = await gp.fetch_popular_pypi_packages()
        targets: list[str] = popular_packages[: args.top]
    elif args.package:
        targets = [args.package]
    else:
        raise ValueError("Either --top or --package must be specified")

    searcher = gs.gh.GitHubSearch()

    tasks = []
    async with asyncio.TaskGroup() as tg:
        for pkg in targets:
            tasks.append(tg.create_task(gp.fetch_pypi_package_info(pkg)))

    valid_pkgs: list[gp.PypiPackageInfo] = []
    for task in tasks:
        pkg_info: gp.PypiPackageInfo = task.result()
        if searcher.is_acceptable(pkg_info.source_url):
            valid_pkgs.append(pkg_info)

    tasks = []
    limiter = aiolimiter.AsyncLimiter(5, 60)
    async with asyncio.TaskGroup() as tg, limiter:
        for pkg_info in valid_pkgs:
            codebase = searcher.extract_codebase(pkg_info.source_url)
            task = tg.create_task(
                searcher.search(codebase, args.pattern, args.languages)
            )
            tasks.append(task)

    for i, task in enumerate(tasks):
        results: list[gs.CodeResult] = task.result()
        for result in results:
            print(
                f"Project: {valid_pkgs[i].name}, File: {result.file}, Path: {result.path}, URL: {result.http_url}"
            )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
