import Levenshtein
import distance
import numpy as np


# TODO: docstring
def multi_similarity(s1: str, s2: str, lower_threshold: float = 0.6, upper_threshold: float = 0.95):
    sims = [Levenshtein.ratio(s1, s2), 1 - distance.sorensen(s1, s2), 1 - distance.jaccard(s1, s2)]
    min_sim = min(sims)
    if min_sim < lower_threshold:
        return min_sim
    max_sim = max(sims)
    if max_sim >= upper_threshold:
        return max_sim
    return np.mean(sims)


# TODO: docstring
def multi_similarity_splits(s1: str, s2: str, lower_threshold: float = 0.5, min_size_subset_comparison: int = 1):
    s1_splits = s1.split()
    s2_splits = s2.split()
    if len(s1_splits) != len(s2_splits):
        if min(len(s1_splits), len(s2_splits)) >= min_size_subset_comparison:
            if len(s1_splits) < len(s2_splits):
                shorter = set(s1_splits)
                longer = set(s2_splits)
            else:
                shorter = set(s2_splits)
                longer = set(s1_splits)
            # TODO: replace strict set comparison (strict string equality check) with fuzzy
            #  set comparison (fuzzy string similarity check with some threshold)
            if shorter.issubset(longer):
                return 1.0
        # TODO: include additional multi_similarity.lower_threshold and multi_similarity.upper_threshold parameters
        return multi_similarity(s1, s2)
    s1_splits.sort()
    s2_splits.sort()
    sims = []
    for s1_split, s2_split in zip(s1_splits, s2_splits):
        sim = multi_similarity(s1_split, s2_split)
        if sim < lower_threshold:
            return sim
        sims.append(sim)
    return np.mean(sims)
