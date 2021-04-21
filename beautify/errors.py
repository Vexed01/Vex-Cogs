class NoData(Exception):
    """
    No argument or file was passed

    Has child errors AttachmentPermsError and AttachmentInvalid
    """

    # i think "child errors" might not be the right thing to say but oh well (PR a fix if you want)


class AttachmentPermsError(NoData):
    """Can't access attachment"""


class AttachmentInvalid(NoData):
    """Attachment has wrong file type"""


class JSONDecodeError(Exception):
    """Custom decoding error for either pyjson5 or json modules"""
