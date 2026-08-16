# 016 — REAL_MAC_DESCRIPTOR_PHASE_TOO_AGGRESSIVE

RC2 terminated working obfs4 bridges at bootstrap 50% after 240 seconds without a percentage change. Tor documents phase 50 (loading relay descriptors) as typically the bulk of bootstrap, especially on slow links. RC3 uses a 900-second no-progress limit from phase >=40 and a 1200-second overall attempt ceiling, while early-stage failures remain bounded sooner.
