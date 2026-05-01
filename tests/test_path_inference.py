import pytest
import uuid as uuid_lib
from apiscribe.utils.path_inference import infer_path_template


@pytest.mark.parametrize("paths, expected_template, expected_params_len", [
    # Пустой список – нет путей
    ([], "/", 0),
    # Один путь без параметров
    (["/users/list"], "/users/list", 0),
    # Один путь с потенциальным параметром – но поскольку один элемент, он считается константой
    (["/users/123"], "/users/123", 0),
    # Несколько путей с целыми числами
    (["/users/123", "/users/456", "/users/789"], "/users/{users_id}", 1),
    # Несколько путей с UUID
    ([f"/items/{uuid_lib.uuid4()}", f"/items/{uuid_lib.uuid4()}"], "/items/{items_uuid}", 1),
    # Смесь строк (не всё целые, уникальных >3 → параметр-строка)
    (["/user/alice", "/user/bob", "/user/charlie", "/user/dave"], "/user/{user_param}", 1),
    # Уникальных строк <=3, но не все целые → константа
    (["/v1/status", "/v2/status", "/v3/status"], "/v1/status", 0),
    # Два параметра подряд
    (["/users/123/posts/456", "/users/789/posts/101"], "/users/{users_id}/posts/{posts_id}", 2),
    # Разная длина путей – шаблон строится по максимальной длине
    (["/users/123", "/users/456/profile"], "/users/{users_id}/profile", 1),
    # Первый сегмент – параметр (нет prev, fallback "param")
    (["/123", "/456", "/789"], "/{param_id}", 1),
    # Смешанные типы: целые и строки → параметр-строка
    (["/items/1", "/items/abc", "/items/2"], "/items/{items_param}", 1),
])
def test_infer_path_template(paths, expected_template, expected_params_len):
    template, params = infer_path_template(paths)
    assert template == expected_template
    assert len(params) == expected_params_len
    
# Отдельная параметризация для проверки схемы параметров с типом integer
@pytest.mark.parametrize("paths, param_name, param_type, param_format", [
    (["/users/123", "/users/456"], "users_id", "integer", None),
    (["/posts/1/edit", "/posts/2/edit"], "posts_id", "integer", None),
])
def test_integer_param_schema(paths, param_name, param_type, param_format):
    template, params = infer_path_template(paths)
    assert params[0]["name"] == param_name
    assert params[0]["schema"]["type"] == param_type
    if param_format:
        assert params[0]["schema"]["format"] == param_format

# Отдельная параметризация для UUID
@pytest.mark.parametrize("paths, param_name", [
    ([f"/docs/{uuid_lib.uuid4()}", f"/docs/{uuid_lib.uuid4()}"], "docs_uuid"),
])
def test_uuid_param_schema(paths, param_name):
    template, params = infer_path_template(paths)
    assert params[0]["name"] == param_name
    assert params[0]["schema"]["type"] == "string"
    assert params[0]["schema"]["format"] == "uuid"

# Проверка обязательных полей параметра
def test_parameter_required_fields():
    paths = ["/orders/123", "/orders/456"]
    template, params = infer_path_template(paths)
    param = params[0]
    assert param["in"] == "path"
    assert param["required"] is True