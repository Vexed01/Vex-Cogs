from gidgethub import HTTPException

from .errors import CustomError

GET_ISSUE = "get_issue"
GET_REPO_LABELS = "get_repo_labels"
GET_ISSUE_LABELS = "get_issue_labels"

ADD_LABEL = "add_label"
REMOVE_LABEL = "remove_label"

CREATE_ISSUE = "create_issue"
COMMENT = "comment"
CLOSE = "close"
CHECK_REAL = "check_real"

EXCEPTIONS = (HTTPException, CustomError)


CHECK = "\N{HEAVY CHECK MARK}\N{VARIATION SELECTOR-16}"
CROSS = "\N{CROSS MARK}"
