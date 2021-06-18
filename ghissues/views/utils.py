from typing import Dict, Generator, List, Tuple


def make_label_content(page: int = 0, total_pages: int = 0):
    base = (
        "Click a label to toggle it. Labels in GREEN are on the issue, labels in GREY "
        "are not on the issue."
    )
    page_info = (
        "\nAs you've got lots of labels, click the bottons at the bottom to change "
        f"pages.\n\nPage {page + 1} of {total_pages}"
        if total_pages > 1
        else ""
    )

    return base + page_info


def get_menu_sets(raw_labels: Dict[str, bool]) -> Generator[List[Tuple[str, bool]], None, None]:
    # partially from a sketchy site and SO
    sorted_labels = {k: v for k, v in sorted(raw_labels.items(), key=lambda item: not item[1])}
    labels = list(sorted_labels.items())
    for i in range(0, len(labels), 20):
        yield labels[i : i + 20]
