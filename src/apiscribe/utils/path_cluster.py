def cluster_paths(paths):

    clusters = {}

    for path in paths:

        parts = path.strip("/").split("/")
        key = len(parts)

        clusters.setdefault(key, []).append(path)

    return list(clusters.values())