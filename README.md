GerritCommandLine
=================

#Patchsets that have a score greater than -1 on the MobileFrontend project.
python gerrit.py --project 'mediawiki/extensions/MobileFrontend' --gtscore -1

#Patchsets that have been around over over 100 days on mediawiki/core repository
python gerrit.py --project 'mediawiki/core' --gtage 100

# Patchsets that have a -1 or -2 and are more than 10 days old
python gerrit.py --project 'mediawiki/core' --gtage 10 --ltscore 0

# All patchsets by jdlrobson on MobileFrontend extension
python gerrit.py --project 'mediawiki/extensions/MobileFrontend' --byuser 'Jdlrobson'
