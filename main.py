import argparse
import os
from glob import glob

import pandas as pd

from attendance_checker import AttendanceChecker
from util.data import get_zoom_participants_df, get_moodle_df

# TODO: General TODO in this project: Currently, lots of hard-coded values (e.g, column names) --> parameterize
# TODO: only print if verbosity is enabled
if __name__ == "__main__":
    pd.options.display.width = 0
    
    parser = argparse.ArgumentParser()
    parser.add_argument("-pf", "--participants_file", type=str, required=True,
                        help="Path to participants CSV file. Can also be a directory, in which case all '*.csv' files "
                             "within this directory will be used (non-recursively).")
    parser.add_argument("-mf", "--moodle_file", type=str, required=True,
                        help="Path to Moodle CSV file (e.g., Moodle export, grading file, etc.).")
    parser.add_argument("--moodle_file_filter_col", type=str, default=None,
                        help="If specified, the name of the column in 'moodle_file' which will be used to filter "
                             "entries/rows according to 'filter_values', i.e., only those entries/rows are kept where "
                             "the values in this column (exactly) match any of 'filter_values'.")
    parser.add_argument("--filter_values", type=str, nargs="+", default=None,
                        help="Must be specified if 'moodle_file_filter_col' is specified, otherwise, it is ignored. "
                             "A list of values that will be used to check if the values in 'moodle_file_filter_col' "
                             "(exactly) match any of them. If so, entries/rows are kept, otherwise, they are dropped.")
    args = parser.parse_args()
    
    if os.path.isfile(args.participants_file):
        participants_files = [args.participants_file]
    else:
        participants_files = glob(os.path.join(args.participants_file, "*.csv"))
    zoom_dfs = [get_zoom_participants_df(pf) for pf in participants_files]
    zoom_df = pd.concat(zoom_dfs, ignore_index=True)
    
    # TODO: if other sources (other than Zoom participant lists) are included here, make sure 
    #  to merge all the DFs, so AttendanceChecker.participants_df contains all possible entries.
    #  If those other sources do not contain a "duration" column, a solution would be to just
    #  assign a dummy value, e.g., AttendanceChecker.attendance_duration_threshold (which would
    #  lead to those entries never being dropped, which is perfectly fine).
    
    moodle_df = get_moodle_df(args.moodle_file)
    if args.moodle_file_filter_col is not None:
        if args.filter_values is None:
            raise ValueError("if 'moodle_file_filter_col' is specified, 'filter_values' must be specified as well")
        len_before = len(moodle_df)
        # Convert to string, so the filtering is simplified to a plain string comparison and
        # we do not have to worry about datatype mismatches and things like that
        moodle_df = moodle_df[moodle_df[args.moodle_file_filter_col].astype(str).isin(args.filter_values)]
        print(f"dropped {len_before - len(moodle_df)}")
    
    ac = AttendanceChecker(participants_df=zoom_df, moodle_df=moodle_df,
                           name_similarity_threshold=0.9, attendance_duration_threshold=5)
    attendance_df = ac.get_attendance_df()
    # print(attendance_df[attendance_df["attendance_count"] < 3])
    print(attendance_df)
