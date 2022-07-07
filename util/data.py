import re
import warnings

import pandas as pd

from util.text import normalize_string

UNKNOWN_ID = "unknown"


def get_zoom_participants_df(participants_file: str) -> pd.DataFrame:
    """
    TODO: main docstring
    
    :param participants_file: Path to Zoom participants CSV file.
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
        # First, try to extract the ID from the name. Assume at least 3 digits, so something like
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
        # Then, try to extract the ID from the mail
        # If the mail is specified, it should be of the form "k<8-digit-matriculation-id>@students.jku.at",
        # other mail formats (e.g., personal mails or JKU account mails) are treated as if it were missing
        mail = row[mail_col]
        if not isinstance(mail, str):
            return UNKNOWN_ID
        match = re.search(r"k\d{8}", mail)
        if match is None:
            return UNKNOWN_ID
        return match.group()
    
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


def get_full_grading_df(grading_file: str) -> pd.DataFrame:
    """
    TODO: main docstring
    
    :param grading_file: Path to the full grading CSV file that contains "First name",
        "Surname", "ID number" and "grade" columns.
    :return: The processed grading DataFrame.
    """
    df = pd.read_csv(grading_file)
    df = df[["First name", "Surname", "ID number", "grade"]]
    df["name"] = (df["First name"] + " " + df["Surname"]).apply(normalize_string)
    df.columns = ["first_name", "last_name", "moodle_id", "grade", "name"]
    return df
