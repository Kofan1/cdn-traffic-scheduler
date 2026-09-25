import importlib

def module():
    import app.main as main
    return importlib.reload(main)


def test_selects_lowest_score_for_region():
    main = module()
    response = main.choose_endpoint(main.ScheduleRequest(region="us-west", size_gb=2))
    assert response.endpoint_id == "edge-us-west"
    assert response.estimated_cost == 0.036


def test_falls_back_to_healthy_endpoint_when_region_has_no_match():
    main = module()
    response = main.choose_endpoint(main.ScheduleRequest(region="ap-southeast", size_gb=1))
    assert response.endpoint_id


def test_unhealthy_endpoint_is_not_selected():
    main = module()
    main.ENDPOINTS["edge-us-west"].healthy = False
    response = main.choose_endpoint(main.ScheduleRequest(region="us-west", size_gb=1))
    assert response.endpoint_id != "edge-us-west"


def test_returns_503_when_all_endpoints_are_unhealthy():
    main = module()
    for endpoint_id in ["edge-us-west", "edge-us-central", "edge-us-east", "edge-eu-west"]:
        main.ENDPOINTS[endpoint_id].healthy = False
    try:
        main.choose_endpoint(main.ScheduleRequest(region="us-west", size_gb=1))
    except main.HTTPException as error:
        assert error.status_code == 503
    else:
        raise AssertionError("Expected no healthy endpoint error")
