"""
Generic, out-of-the-box scopes. Useful in building queries.
"""

def where(query):
    """
    Simply returns the given query to the scope builder. Useful when you need
    to combine arbritary query elements with other scopes.
    """
    return query
