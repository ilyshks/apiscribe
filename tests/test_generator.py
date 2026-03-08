
def test_path_clustering(endpoint_factory, generator):

    endpoints = [
        endpoint_factory("/users/1"),
        endpoint_factory("/users/2"),
        endpoint_factory("/users/3"),
    ]

    spec = generator.generate(endpoints)

    assert "/users/{users_id}" in spec["paths"]


def test_nested_paths(endpoint_factory, generator):

    endpoints = [
        endpoint_factory("/users/1/orders/10"),
        endpoint_factory("/users/2/orders/20"),
    ]

    spec = generator.generate(endpoints)

    assert "/users/{users_id}/orders/{orders_id}" in spec["paths"]

def test_multiple_methods(endpoint_factory, generator):

    endpoints = [
        endpoint_factory("/users/1", "GET"),
        endpoint_factory("/users/2", "GET"),
        endpoint_factory("/users/1", "POST"),
        endpoint_factory("/users/2", "POST"),
    ]

    spec = generator.generate(endpoints)

    path = "/users/{users_id}"

    assert "get" in spec["paths"][path]
    assert "post" in spec["paths"][path]