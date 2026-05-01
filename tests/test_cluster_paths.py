import pytest
from apiscribe.utils.path_cluster import cluster_paths


@pytest.mark.parametrize("paths, expected", [
    # Пустой список
    ([], []),
    # Один путь
    (["/a/b/c"], [["/a/b/c"]]),
    # Пути одинаковой глубины
    (["/users/123", "/users/456"], [["/users/123", "/users/456"]]),
    # Разная глубина
    (
        ["/a", "/a/b", "/a/b/c"],
        [["/a"], ["/a/b"], ["/a/b/c"]]
    ),
    # Перемешанная глубина
    (
        ["/x/y", "/x", "/x/y/z", "/w"],
        [["/x", "/w"], ["/x/y"], ["/x/y/z"]]  # порядок кластеров не важен, тест будет сортировать
    ),
    # Пути с лидирующими и завершающими слешами
    (
        ["/users/", "users/123", "/users/123/profile/"],
        [["/users/"], ["users/123"], ["/users/123/profile/"]]
    ),
    # Глубина считается по количеству сегментов после обрезки слешей
    (
        ["/", "/a/", "b/c"],
        [["/", "/a/"], ["b/c"]]  # глубина 0 (пустой путь -> 0), 0, 1, 2
    ),
    # Пути с повторяющимися значениями – группировка по глубине, а не по содержимому
    (
        ["/users/123", "/posts/123", "/users/456"],
        [["/users/123", "/posts/123", "/users/456"]]  # все глубины 2
    ),
])
def test_cluster_paths(paths, expected):
    result = cluster_paths(paths)
    # Сортируем кластеры для детерминированного сравнения (каждый кластер сортируем внутри)
    result_sorted = sorted([sorted(cluster) for cluster in result])
    expected_sorted = sorted([sorted(cluster) for cluster in expected])
    assert result_sorted == expected_sorted

# Проверка, что кластеры действительно сгруппированы по глубине
def test_clustering_key_is_depth():
    paths = ["/a/b/c", "/d/e", "/f/g/h", "/i"]
    clusters = cluster_paths(paths)
    depths = [len(p.strip("/").split("/")) if p.strip("/") else 0 for cluster in clusters for p in cluster]
    # Каждый кластер должен содержать пути только одной глубины
    for cluster in clusters:
        cluster_depths = set(len(p.strip("/").split("/")) if p.strip("/") else 0 for p in cluster)
        assert len(cluster_depths) == 1