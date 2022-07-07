import pandas as pd

from util.data import UNKNOWN_ID
from util.similarity import multi_similarity_splits


class AttendanceChecker:
    
    def __init__(self, participants_df: pd.DataFrame, grading_df: pd.DataFrame,
                 name_similarity_threshold: float, attendance_duration_threshold: int):
        self.participants_df = participants_df
        self.grading_df = grading_df
        self.name_similarity_threshold = name_similarity_threshold
        self.attendance_duration_threshold = attendance_duration_threshold
    
    def _id_from_moodle(self, row: pd.Series):
        name = row["name"]
        matching_rows = []
        for grading_df_row in self.grading_df.itertuples():
            # Fuzzy string equality matching due to manual name entering in participants lists.
            # This will most likely not work in 100% of the cases, but if the majority of manual
            # name entries can be mapped to the actual Moodle/KUSSS names, it is good enough.
            # Naturally, this heavily depends on what the manual names actually look like and
            # which similarity metric (and parameterization thereof) is applied here.
            # TODO: include kwargs for multi_similarity_splits in __init__
            if multi_similarity_splits(grading_df_row.name, name) >= self.name_similarity_threshold:
                matching_rows.append(grading_df_row)
        if len(matching_rows) == 0:
            return pd.Series([0 if row["id"] == UNKNOWN_ID else 1, row["id"]])
        if len(matching_rows) == 1:
            return pd.Series([1, matching_rows[0].moodle_id])
        if row["id"] in {mr.moodle_id for mr in matching_rows}:
            return pd.Series([1, row["id"]])
        return pd.Series([len(matching_rows), ",".join([row.moodle_id for row in matching_rows])])
    
    def get_attendance_df(self):
        df = self.participants_df.copy()
        df[["id_count", "moodle_id"]] = df.apply(self._id_from_moodle, axis=1)
        
        too_many_moodle_ids_df = df[df["id_count"] > 1].drop_duplicates(subset="name")
        print(f"{len(too_many_moodle_ids_df)} with > 1 IDs")
        
        no_moodle_id = df[df["id_count"] == 0].drop_duplicates(subset="name")
        print(f"{len(no_moodle_id)} with 0 IDs")
        
        one_moodle_id_df = df[df["id_count"] == 1][["moodle_id", "duration"]].reset_index(drop=True)
        attendance_df = one_moodle_id_df[one_moodle_id_df["duration"] >= self.attendance_duration_threshold].copy()
        
        dropped_df = one_moodle_id_df.drop(index=attendance_df.index)
        assert len(dropped_df) == len(one_moodle_id_df) - len(attendance_df)
        print(f"dropped {len(dropped_df)} with duration < {self.attendance_duration_threshold} minutes")
        
        attendance_df["attendance_count"] = 1
        attendance_df = attendance_df.groupby("moodle_id").sum().reset_index()
        attendance_df = pd.merge(attendance_df, self.grading_df, on="moodle_id").sort_values("attendance_count")
        return attendance_df
