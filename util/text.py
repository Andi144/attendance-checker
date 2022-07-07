from sklearn.feature_extraction.text import strip_accents_ascii


def normalize_string(s: str):
    """
    Normalize the specified string, which means: 1) lower case, 2) replacement of
    dash "-" characters with space " " characters, 3) replacement of accented
    characters (e.g., "à") with non-accented characters (e.g., "a").
    
    The accent replacement is done via ``sklearn.feature_extraction.text.strip_accents_ascii``.
    
    :param s: The string to normalize.
    :return: The normalized string.
    """
    return strip_accents_ascii(s.lower()).replace("-", " ")
