import re
import warnings

import pandas as pd

from util.text import normalize_string


def get_zoom_participants_df(participants_file: str, unknown_id: str = "unknown") -> pd.DataFrame:
    """
    TODO: main docstring
    
    :param participants_file: Path to Zoom participants CSV file.
    :param unknown_id: The ID to use if a valid ID cannot be inferred. Default: "unknown"
    :return: The processed participants DataFrame.
    """
    df = pd.read_csv(participants_file)
    
    name_col = "Name (Originalname)"
    mail_col = "Benutzer-E-Mail:"
    assert name_col in df.columns and mail_col in df.columns
    duration_cols = [c for c in df.columns if "(Minuten)" in c]
    assert len(duration_cols) == 1
    duration_col = duration_cols[0]
    
    df = df[[name_col, mail_col, duration_col]]
    
    def extract_id(row: pd.Series):
        # First, try to extract the ID from the mail
        # If the mail is specified, it should be of the form "k<8-digit-matriculation-id>@students.jku.at",
        # other mail formats (e.g., personal mails or JKU account mails) are treated as if it were missing
        mail = row[mail_col]
        if isinstance(mail, str):
            match = re.search(r"k\d{8}", mail)
            if match is not None:
                return match.group()
        # Otherwise, try to extract the ID from the name. Assume at least 3 digits, so something like
        # "some name 2", e.g., due to double login (or other reasons), does not match
        name = row[name_col]
        match = re.search(r"[kK]?\d{3,}", name)
        if match is not None:
            id_ = match.group().lower()
            # Could be with or without "k" and then >= 1 digit
            if id_.startswith("k"):
                id_ = id_[1:]
            if len(id_) < 8:
                # Fill up with leading zeros
                return "k" + "0" * (8 - len(id_)) + id_
            elif len(id_) > 8:
                warnings.warn(f"{row}: ID '{id_}' too long")
            else:
                # ID is without "k" and exactly 8 digits longs
                assert re.match(r"\d{8}", id_) is not None
                return "k" + id_
        return unknown_id
    
    def clean_name(name: str):
        name = normalize_string(name)
        # Remove unnecessary name additions, e.g., "some name (k12345678)" --> "some name"
        # If the pattern occurrs, it results in empty parts (where the pattern was) and the remainder of
        # the name. If the empty parts are not actually empty, it was due to some unexpected input format
        splits = re.split(r"\(.*\)|k\d+|\d+", name)
        if len(splits) == 1:
            return name
        remainder = None
        for s in splits:
            s = s.strip()
            if s:
                assert remainder is None, f"unexpected pattern match: {name} -> {splits}"
                remainder = s
        return remainder
    
    df["id"] = df.apply(extract_id, axis=1)
    df["name"] = df[name_col].apply(clean_name)
    df = df[[name_col, "name", "id", duration_col]]
    df.columns = ["original_name", "name", "id", "duration"]
    return df


def get_moodle_df(moodle_file: str, first_name_col: str = "First name", surname_col: str = "Surname",
                  full_name_col: str = None, id_col: str = "ID number", **kwargs) -> pd.DataFrame:
    """
    TODO: main docstring
    
    :param moodle_file: Path to the Moodle CSV file that contains at least the columns
        ``id_col`` and either ``first_name_col`` together with ``surname_col`` or just
        ``full_name_col``. If ``full_name_col`` is specified, ``first_name_col`` and
        ``surname_col`` are both ignored.
    :param first_name_col: The column name containing the first name. Default: "First name"
    :param surname_col: The column name containing the surname/last name. Default: "Surname"
    :param full_name_col: The column name containing the full name (combination of first
        name followed by the surname, in exactly this order). Default: None (unspecified)
    :param id_col: The column name containing the matriculation ID. Default: "ID number"
    :param kwargs: Additional keyword arguments that are passed to ``pd.read_csv``.
    :return: The processed grading DataFrame.
    """
    df = pd.read_csv(moodle_file, **kwargs)
    if full_name_col is not None:
        df["name"] = df[full_name_col]
    else:
        df["name"] = df[first_name_col] + " " + df[surname_col]
    df["name"] = df["name"].apply(normalize_string)
    new_cols = []
    for col in df.columns:
        if col == id_col:
            new_cols.append("moodle_id")
        else:
            new_cols.append(col)
    df.columns = new_cols
    return df
