GerritCommandLine
=================

Patchsets that have a score greater than -1 on the MobileFrontend project.
`python gerrit.py --project 'mediawiki/extensions/MobileFrontend' --gtscore -1`

Patchsets that have been around over over 100 days on mediawiki/core repository
`python gerrit.py --project 'mediawiki/core' --gtage 100`

Patchsets that have a -1 or -2 and are more than 10 days old
`python gerrit.py --project 'mediawiki/core' --gtage 10 --ltscore 0`

Patchsets in core that were not written by users jdlrobson or kaldari
`python gerrit.py --project 'mediawiki/core' --excludeuser jdlrobson --excludeuser kaldari`

All patchsets by jdlrobson on MobileFrontend extension
`python gerrit.py --project 'mediawiki/extensions/MobileFrontend' --byuser 'Jdlrobson'`

All patchsets requesting review from Jdlrobson across all repositories
`gerrit.py --reviewee jdlrobson`

All patchsets requesting review from Jdlrobson  across all repositories with a positive score
`gerrit.py --reviewee jdlrobson --gtscore -1`

All patchsets requesting review from Jdlrobson in the core mediawiki repository with a positive score
`gerrit.py --reviewee jdlrobson --gtscore -1 --project mediawiki/core`
