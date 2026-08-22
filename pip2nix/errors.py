"""
The failures a generation run reports to its user.
"""


class ReportError(Exception):
    pass


class UnresolvableRevision(ReportError):
    pass
