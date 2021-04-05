.. _changelog:


*********
Changelog
*********

Not all changes will be documented here, only bigger updates.

============
Status 2.0.0
============

-------------------
User-facing changes
-------------------

- BREAKING CHANGES: Removed AWS, GCP, Twitter and Status.io. These will be automaticity removed when you update.
- Added the docs page :ref:`statusref` to see previews for different modes/webhook
- All updates will now included the impact and affected components (see an example at :ref:`statusref`)
- New service: GeForce NOW (``geforcenow``)

----------------------------
Event Changes for developers
----------------------------

I highly recommend you read the docs page again at the :ref:`statusdev` page.

There have been significant changes to both the events.

----------------
Internal changes
----------------

- Significant re-factoring into more files and folders
- Rewrite of update checking and sending logic
- Implementation of Status API instead of parsing RSS
- Changes to how incidents are stored including config wrapper
- No longer write ETags to config (just cache)