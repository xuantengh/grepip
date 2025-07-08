import abc
import dataclasses
import pathlib


@dataclasses.dataclass(frozen=True)
class CodeResult:
    file: str
    path: str
    http_url: str


class CodeSearcher(abc.ABC):
    artifact_path: pathlib.Path = None

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
    async def fetch_release(
        self,
        codebase: str,
    ) -> pathlib.Path:
        raise NotImplementedError

    @abc.abstractmethod
    async def zgrep(self, path: pathlib.Path, pattern: str) -> list[str]:
        """
        Search for a pattern in the codebase.

        Args:
            path (pathlib.Path): the path to the codebase.
            pattern (str): the pattern to search for.

        Returns:
            list[CodeResult]: a list of CodeResult objects containing the search results.
        """
        raise NotImplementedError
