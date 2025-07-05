import abc


class CodeSearcher(abc.ABC):
    @abc.abstractmethod
    async def search(
        self,
        codebase: str,
        pattern: str,
        languages: list[str] | None = None,
    ) -> list[dict]:
        """
        Search for code snippets based on the provided pattern.

        Args:
            codebase (str): the codebase to search within.
            pattern (str): the search pattern.

        Returns:
            list[dict]: a list of search results.
        """
        raise NotImplementedError
