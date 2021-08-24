import vexcogutils  # noqa

from status.objects import SendCache, UpdateField
from status.objects.incidentdata import Update
from status.updateloop import processfeed

from .consts import (
    STATUS_EXPECTED_EMBED_INCIDENTS_ALL,
    STATUS_EXPECTED_EMBED_SCHEDULED_ALL,
    STATUS_EXPECTED_PLAIN_INCIDENTS_ALL,
    STATUS_EXPECTED_PLAIN_SCHEDULED_ALL,
    TEST_FEED_DATA_INCIDENTS,
    TEST_FEED_DATA_SCHEDULED,
)


# this critical edge case stuff that needs to work
def test_field_handler():
    VALID = [UpdateField(name="", value="A" * 1023, update_id="...")]
    BOUNDARY = [UpdateField(name="", value="A" * 1024, update_id="...")]
    INVALID = [UpdateField(name="", value="A" * 1025, update_id="...")]
    EXTREME = [UpdateField(name="", value="A" * 2049, update_id="...")]

    split_under = processfeed._handle_long_fields(VALID)
    split_at = processfeed._handle_long_fields(BOUNDARY)
    split_over = processfeed._handle_long_fields(INVALID)
    split_very_over = processfeed._handle_long_fields(EXTREME)

    assert len(split_under) == 1
    assert len(split_at) == 1
    assert len(split_over) == 2
    assert len(split_very_over) == 3

    assert split_under[0].value == VALID[0].value
    assert split_at[0].value == BOUNDARY[0].value

    # uses cf pagify, in this case it will not loose anything as there are no new lines
    assert len(split_over[0].value) + len(split_over[1].value) == len(INVALID[0].value)
    assert split_over[0].update_id == split_over[1].update_id == INVALID[0].update_id

    # uses cf pagify, in this case it will not loose anything as there are no new lines
    assert len(split_very_over[0].value) + len(split_very_over[1].value) + len(
        split_very_over[2].value
    ) == len(EXTREME[0].value)
    assert (
        split_very_over[0].update_id
        == split_very_over[1].update_id
        == split_very_over[2].update_id
        == EXTREME[0].update_id
    )


# this one is here because why not
def test_example_incident():
    incidents = processfeed.process_json(TEST_FEED_DATA_INCIDENTS, "incidents")
    scheduled = processfeed.process_json(TEST_FEED_DATA_SCHEDULED, "scheduled")

    up_inc = Update(incidents[0], [incidents[0].fields[0]])
    up_sch = Update(scheduled[0], [scheduled[0].fields[0]])

    sc_inc = SendCache(up_inc, "statuspage")
    sc_sch = SendCache(up_sch, "statuspage")

    assert sc_inc.embed_all.to_dict() == STATUS_EXPECTED_EMBED_INCIDENTS_ALL
    assert sc_sch.embed_all.to_dict() == STATUS_EXPECTED_EMBED_SCHEDULED_ALL
    assert sc_inc.plain_all == STATUS_EXPECTED_PLAIN_INCIDENTS_ALL
    assert sc_sch.plain_all == STATUS_EXPECTED_PLAIN_SCHEDULED_ALL
