"""
Volume / rate / mix decomposition of rooms revenue variance.  ***S3.***

Do not start this until S2 is committed.

WHY THIS MODULE EXISTS -- read the dataset before you write a line of code:

    HOTEL_A, 2026-06, Rooms Revenue
        budget 494,252   actual 497,120   variance +2,868  (+0.6%)

On the P&L that month looks like nothing happened. Underneath:

        Group     room nights   871 -> 664   (-24%)
        Transient room nights 1,597 -> 1,792 (+12%)

A group block collapsed and transient walk-in partly backfilled it at a
higher rate. Volume down, rate up, mix richer -- three large effects that
nearly cancel. The P&L cannot show you that. The bridge can. This single
month is the reason the project is worth putting on a resume, and it is the
example you should walk an interviewer through.

TODO(S3): implement the decomposition. Components must sum to the total
          rooms revenue variance, and a test must assert that tie-out.
"""
