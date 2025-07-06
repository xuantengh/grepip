import abc
import dataclasses


@dataclasses.dataclass(frozen=True)
class CodeResult:
    file: str
    path: str
    http_url: str


class CodeSearcher(abc.ABC):
    @classmethod
    @abc.abstractmethod
    def is_acceptable(cls, codebase_url: str) -> bool:
        """
        Check if the codebase URL is acceptable for this searcher.

        Args:
            codebase_url (str): the URL of the codebase to check.

        Returns:
            bool: True if the codebase is acceptable, False otherwise.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def search(
        self,
        codebase: str,
        pattern: str,
        languages: list[str] | None = None,
    ) -> list[CodeResult]:
        """
        Search for code snippets based on the provided pattern.

        Args:
            codebase (str): the codebase to search within.
            pattern (str): the search pattern.

        Returns:
            list[dict]: a list of search results.
        """
        raise NotImplementedError
