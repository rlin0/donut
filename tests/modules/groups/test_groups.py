"""
Tests donut/modules/groups/
"""
from donut.testing.fixtures import client
from donut import app
from donut.modules.groups import helpers
from donut.modules.groups import routes

group = {
    "group_id": 1,
    "group_name": "Donut Devteam",
    "group_desc": None,
    "type": ""
}


# Helpers
def test_get_group_list_data(client):
    assert helpers.get_group_list_data(["not_a_real_field"]) == "Invalid field"
    assert helpers.get_group_list_data(["group_name"]) == [{
        "group_name":
        "Donut Devteam"
    }]
    groups = [group]
    assert helpers.get_group_list_data() == groups
    assert helpers.get_group_list_data(None, {"group_id": 1}) == groups
    assert helpers.get_group_list_data(None, {"group_id": 2}) == []


def test_get_group_positions_data(client):
    assert helpers.get_group_positions(1) == [{
        "pos_id": 1,
        "pos_name": "Head"
    }, {
        "pos_id": 2,
        "pos_name": "Secretary"
    }]
    assert helpers.get_group_positions(2) == []

def test_get_position_data(client):
    res = helpers.get_position_data()
    assert res is not None

def test_get_group_data(client):
    assert helpers.get_group_data(2) == {}
    assert helpers.get_group_data(1, ["not_a_real_field"]) == "Invalid field"
    assert helpers.get_group_data(1) == group
    assert helpers.get_group_data(1, ["group_name"]) == {
        "group_name": "Donut Devteam"
    }


def test_get_members_by_group(client):
    assert helpers.get_members_by_group(1)[0]["user_id"] == 1
    assert helpers.get_members_by_group(2) == {}


# Test Routes
# Difficult to test because query arguments are undefined outside Flask context
# def test_get_groups_list(client):
#     assert routes.get_groups_list() is not None


def test_get_group_positions(client):
    assert routes.get_group_positions(1) is not None


def get_groups(client):
    assert routes.get_groups(1) is not None


def test_get_group_members(client):
    assert routes.get_group_members(1) is not None