from collections import defaultdict


def cluster_paths(paths: list[str]):

    clusters = defaultdict(list)

    for path in paths:
        segments = path.strip("/").split("/")
        key = len(segments)
        clusters[key].append(path)

    return list(clusters.values())