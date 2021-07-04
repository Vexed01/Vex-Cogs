# test data is from api docs (meta)

TEST_FEED_DATA_INCIDENTS = {
    "page": {
        "id": "y2j98763l56x",
        "name": "Atlassian Statuspage",
        "url": "http://metastatuspage.com",
        "updated_at": "2021-04-18T22:45:20-07:00",
    },
    "incidents": [
        {
            "created_at": "2014-05-14T14:22:39.441-06:00",
            "id": "cp306tmzcl0y",
            "impact": "critical",
            "incident_updates": [
                {
                    "body": "Our master database has ham sandwiches flying out of the rack, and we're working our hardest to stop the bleeding. The whole site is down while we restore functionality, and we'll provide another update within 30 minutes.",
                    "created_at": "2014-05-14T14:22:40.301-06:00",
                    "display_at": "2014-05-14T14:22:40.301-06:00",
                    "id": "jdy3tw5mt5r5",
                    "incident_id": "cp306tmzcl0y",
                    "status": "identified",
                    "updated_at": "2014-05-14T14:22:40.301-06:00",
                }
            ],
            "monitoring_at": None,
            "name": "Unplanned Database Outage",
            "page_id": "y2j98763l56x",
            "resolved_at": None,
            "shortlink": "http://stspg.co:5000/Q0E",
            "status": "identified",
            "updated_at": "2014-05-14T14:35:21.711-06:00",
        },
        {
            "created_at": "2014-05-12T14:22:39.441-06:00",
            "id": "2z5g29qrrxvl",
            "impact": "minor",
            "incident_updates": [
                {
                    "body": "A small display issue with the display of the website was discovered after a recent deploy. The deploy has been rolled back and the website is again functioning correctly.",
                    "created_at": "2014-05-12T14:22:40.301-06:00",
                    "display_at": "2014-05-12T14:22:40.301-06:00",
                    "id": "vlzc06gtjnrl",
                    "incident_id": "2z5g29qrrxvl",
                    "status": "resolved",
                    "updated_at": "2014-05-12T14:22:40.301-06:00",
                }
            ],
            "monitoring_at": None,
            "name": "Unplanned Database Outage",
            "page_id": "y2j98763l56x",
            "resolved_at": "2014-05-12T14:22:40.301-06:00",
            "shortlink": "http://stspg.co:5000/Q0R",
            "status": "resolved",
            "updated_at": "2014-05-12T14:22:40.301-06:00",
        },
    ],
}

TEST_FEED_DATA_SCHEDULED = {
    "page": {
        "id": "y2j98763l56x",
        "name": "Atlassian Statuspage",
        "url": "http://metastatuspage.com",
        "updated_at": "2021-04-18T22:45:20-07:00",
    },
    "scheduled_maintenances": [
        {
            "created_at": "2014-05-14T14:24:40.430-06:00",
            "id": "w1zdr745wmfy",
            "impact": "none",
            "incident_updates": [
                {
                    "body": "Our data center has informed us that they will be performing routine network maintenance. No interruption in service is expected. Any issues during this maintenance should be directed to our support center",
                    "created_at": "2014-05-14T14:24:41.913-06:00",
                    "display_at": "2014-05-14T14:24:41.913-06:00",
                    "id": "qq0vx910b3qj",
                    "incident_id": "w1zdr745wmfy",
                    "status": "scheduled",
                    "updated_at": "2014-05-14T14:24:41.913-06:00",
                }
            ],
            "monitoring_at": None,
            "name": "Network Maintenance (No Interruption Expected)",
            "page_id": "y2j98763l56x",
            "resolved_at": None,
            "scheduled_for": "2014-05-17T22:00:00.000-06:00",
            "scheduled_until": "2014-05-17T23:30:00.000-06:00",
            "shortlink": "http://stspg.co:5000/Q0F",
            "status": "scheduled",
            "updated_at": "2014-05-14T14:24:41.918-06:00",
        },
        {
            "created_at": "2014-05-14T14:27:17.303-06:00",
            "id": "k7mf5z1gz05c",
            "impact": "minor",
            "incident_updates": [
                {
                    "body": "Scheduled maintenance is currently in progress. We will provide updates as necessary.",
                    "created_at": "2014-05-14T14:34:20.036-06:00",
                    "display_at": "2014-05-14T14:34:20.036-06:00",
                    "id": "drs62w8df6fs",
                    "incident_id": "k7mf5z1gz05c",
                    "status": "in_progress",
                    "updated_at": "2014-05-14T14:34:20.036-06:00",
                },
                {
                    "body": "We will be performing rolling upgrades to our web tier with a new kernel version so that Heartbleed will stop making us lose sleep at night. Increased load and latency is expected, but the app should still function appropriately. We will provide updates every 30 minutes with progress of the reboots.",
                    "created_at": "2014-05-14T14:27:18.845-06:00",
                    "display_at": "2014-05-14T14:27:18.845-06:00",
                    "id": "z40y7398jqxc",
                    "incident_id": "k7mf5z1gz05c",
                    "status": "scheduled",
                    "updated_at": "2014-05-14T14:27:18.845-06:00",
                },
            ],
            "monitoring_at": None,
            "name": "Web Tier Recycle",
            "page_id": "y2j98763l56x",
            "resolved_at": None,
            "scheduled_for": "2014-05-14T14:30:00.000-06:00",
            "scheduled_until": "2014-05-14T16:30:00.000-06:00",
            "shortlink": "http://stspg.co:5000/Q0G",
            "status": "in_progress",
            "updated_at": "2014-05-14T14:35:12.258-06:00",
        },
    ],
}

STATUS_EXPECTED_EMBED_INCIDENTS_ALL = {
    "fields": [
        {
            "inline": False,
            "name": "Identified - <t:1400098960:f>",
            "value": "Our master database has ham sandwiches flying out of the rack, and we're working our hardest to stop the bleeding. The whole site is down while we restore functionality, and we'll provide another update within 30 minutes.",
        }
    ],
    "color": 15158332,
    "timestamp": "2014-05-14T20:22:40.301000+00:00",
    "type": "rich",
    "description": "Impact: **Critical**\nAffects: _Unknown_",
    "url": "http://stspg.co:5000/Q0E",
    "title": "Unplanned Database Outage",
}

STATUS_EXPECTED_PLAIN_INCIDENTS_ALL = """**Statuspage Status Update
Unplanned Database Outage**
Incident link: <http://stspg.co:5000/Q0E>
Impact: **Critical**
Affects: _Unknown_

**Identified - <t:1400098960:f>**
Our master database has ham sandwiches flying out of the rack, and we're working our hardest to stop the bleeding. The whole site is down while we restore functionality, and we'll provide another update within 30 minutes.
"""

STATUS_EXPECTED_EMBED_SCHEDULED_ALL = {
    "fields": [
        {
            "inline": False,
            "name": "Scheduled - <t:1400099081:f>",
            "value": "Our data center has informed us that they will be performing routine network maintenance. No interruption in service is expected. Any issues during this maintenance should be directed to our support center",
        }
    ],
    "color": 15105570,
    "timestamp": "2014-05-14T20:24:41.913000+00:00",
    "type": "rich",
    "description": "Impact: **None**\nAffects: _Unknown_\nScheduled for: **<t:1400385600:f>** to **<t:1400391000:f>**",
    "url": "http://stspg.co:5000/Q0F",
    "title": "Network Maintenance (No Interruption Expected)",
}

STATUS_EXPECTED_PLAIN_SCHEDULED_ALL = """**Statuspage Status Update
Network Maintenance (No Interruption Expected)**
Incident link: <http://stspg.co:5000/Q0F>
Impact: **None**
Affects: _Unknown_
Scheduled for: **<t:1400385600:f>** to **<t:1400391000:f>**

**Scheduled - <t:1400099081:f>**
Our data center has informed us that they will be performing routine network maintenance. No interruption in service is expected. Any issues during this maintenance should be directed to our support center
"""
