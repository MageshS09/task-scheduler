import pytest

from demo.app import MAX_TASKS, app

TASK = {"id": "a", "name": "A", "deadline": 1, "profit": 5, "resource_cost": 1}


@pytest.fixture
def client():
    app.config["TESTING"] = True
    return app.test_client()


def test_index_page_and_samples(client):
    assert client.get("/").status_code == 200
    sample = client.get("/sample").get_json()
    assert sample["resource_budget"] == 15 and len(sample["tasks"]) == 10
    assert len(client.get("/sample?circular=1").get_json()["tasks"]) == 2


def test_schedule_sample_matches_engine(client):
    response = client.post("/schedule", json=client.get("/sample").get_json())
    data = response.get_json()
    assert response.status_code == 200
    assert sorted(data["final_selected"]) == ["backend", "deploy", "frontend"]
    assert data["total_profit"] == 360.0 and data["resource_used"] == 15
    assert sum(1 for t in data["tasks"] if t["selected"]) == 3


def test_circular_example_is_rejected_with_a_clear_error(client):
    response = client.post("/schedule", json=client.get("/sample?circular=1").get_json())
    assert response.status_code == 400 and "Circular" in response.get_json()["error"]


def test_default_budget_when_omitted(client):
    response = client.post("/schedule", json={"tasks": [TASK]})
    assert response.status_code == 200 and response.get_json()["resource_budget"] == 12


@pytest.mark.parametrize(
    "body",
    [
        [1],
        "text",
        {"tasks": "x"},
        {"tasks": [1]},
        {"tasks": [{"id": "a"}]},
        {"tasks": [{**TASK, "deadline": "1"}]},
        {"tasks": [{**TASK, "profit": -1}]},
        {"tasks": [TASK, TASK]},
        {"tasks": [{**TASK, "dependencies": ["x"]}]},
        {"tasks": [TASK], "resource_budget": -1},
        {"tasks": [TASK], "resource_budget": 10**9},
        {"tasks": [TASK], "resource_budget": "5"},
        {"tasks": [TASK], "resource_budget": True},
        {"tasks": [TASK] * 0 + [{**TASK, "id": str(i)} for i in range(MAX_TASKS + 1)]},
    ],
)
def test_invalid_requests_return_400_json(client, body):
    response = client.post("/schedule", json=body)
    assert response.status_code == 400 and "error" in response.get_json()


def test_non_json_body_returns_400(client):
    assert client.post("/schedule", data="nope", content_type="text/plain").status_code == 400


def test_vercel_entrypoint_exposes_the_app():
    from api.index import app as exposed

    assert exposed is app
