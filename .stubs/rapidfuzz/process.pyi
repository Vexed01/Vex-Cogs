from typing import Callable, Iterable, Optional, Tuple

# type hints from docs, assume score_cutoff is meant to be float from source and also assuming
# the last 2 return values in the tuple

def extractOne(
    query: str,
    choices: Iterable,
    scorer: Callable = ...,
    processor: Callable = ...,
    score_cutoff: float = ...,
    **kwargs,
) -> Optional[Tuple[str, float, int]]: ...
