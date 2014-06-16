#!/usr/bin/env python

'''
Copyright [2013] [Jon Robson]

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

See the License for the specific language governing permissions and
limitations under the License.
'''
import json
import operator
import urllib2
from datetime import datetime as dt
import time
import subprocess
import sys
import argparse

def get_project():
    command = "git remote -v | head -n1 | awk '{print $2}' | sed -e 's,.*:\(.*/\)\?,,' -e 's/\.git$//'"
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

    #Launch the shell command:
    output, error = process.communicate()
    return "/".join( output.split('/')[-3:] ).replace( '\n', '' )

def calculate_age(timestamp):
    time_string = timestamp[0:18]
    format = "%Y-%m-%d %H:%M:%S"
    d = dt.strptime(time_string, format)
    delta = d.now() - d
    age = delta.days
    if age < 0:
        age = 0
    return age


def calculate_score(change):
    #go through reviews..
    reviews = change["labels"]["Code-Review"]
    likes = 0
    dislikes = 0
    status = 0
    reviewers = []

    if "approved" in reviews:
        likes += 2

    if "recommended" in reviews:
        likes += 1

    if "disliked" in reviews:
        dislikes += 1

    if "rejected" in reviews:
        dislikes += 2

    #calculate status
    if dislikes > 0:
        status = -dislikes
    else:
        status = likes
    return status

def query_gerrit(url):
    req = urllib2.Request(url)
    req.add_header('Accept',
                   'application/json,application/json,application/jsonrequest')
    req.add_header('Content-Type', "application/json; charset=UTF-8")
    resp, data = urllib2.urlopen(req)
    data = json.loads(data)
    return data

def filter_patches(patches, args):
    result = []

    def filter_by_score(patch):
        if patch['score'] > args.gtscore and \
           patch['score'] < args.ltscore:
            return True
        else:
            return False

    def filter_by_user(patch):
        if args.excludeuser:
            return patch['user'].lower() not in args.excludeuser
        if args.byuser:
            return patch['user'] == args.byuser
        else:
            return True

    def filter_by_age(patch):
        age = patch['age']
        if args.ltage:
            return age > args.gtage and age < args.ltage
        else:
            return age > args.gtage

    def filter_by_pattern(patch):
        if args.ignorepattern:
            return args.ignorepattern not in patch['subject']
        else:
            return True

    for patch in patches:
        if filter_by_score(patch) and \
           filter_by_pattern(patch) and \
           filter_by_user(patch) and filter_by_age(patch):
            result.append(patch)
    return result

def get_patches(url):
    patches = []
    for change in query_gerrit(url):
        user = change["owner"]["name"]
        subj = change["subject"]
        number = change["_number"]
        url = 'https://gerrit.wikimedia.org/r/%s' % number

        patch = {"user": user,
                 "subject": subj,
                 "project": change["project"],
                 "score": calculate_score(change),
                 "id": str(number),
                 "url": url,
                 "age": calculate_age(change["created"])}
        patches.append(patch)
    patches = sorted(patches,
                     key=operator.itemgetter("score", "age"), reverse=True)
    return patches

def get_incoming_patches(reviewer, project=None):
    params = 'reviewer:"%s"+is:open'%reviewer
    if project:
        params += '+project:"%s"'% project

    url = 'https://gerrit.wikimedia.org/r/changes/?q=%s&n=25&O=1'%params
    return get_patches(url)

def get_project_patches(project):
    url = "https://gerrit.wikimedia.org/r/changes/?q=status:open+project:" \
        + project + "&n=25&O=1"
    return get_patches(url)

def choose_project(match_pattern=None):
    url = "https://gerrit.wikimedia.org/r/projects/?type=ALL&all&d"
    projects = query_gerrit(url)
    keys = sorted(iter(projects))
    index = 0
    available = []
    for project in keys:
        if (not match_pattern) or (match_pattern in project):
            print '#%s: %s'%(index, project)
            index += 1
            available.append(project)

    prompt = 'Enter number of project'
    prompt += ' (Press enter to exit):'
    choice = raw_input(prompt)
    if choice:
        try:
            return available[int(choice)]
        except IndexError:
            return None
    else:
        return None

def get_parser():
    help = {
        'project': 'A valid project name on http://gerrit.wikimedia.org',
        'reviewee': 'Show all patches for a given reviewee',
        'action': 'Action to perform on patchset. Values: checkout|open',
        'gtscore': 'Only show patches with a score greater than this value',
        'ignorepattern': 'Ignore any patches where commit subject matches given string',
        'ltscore': 'Only show patches with a score less than this value',
        'byuser': 'Only show patches from this user',
        'excludeuser': 'Do not show patches from this user (username should be lowercase)',
        'ltage': 'Only show patches with an age less than this value',
        'gtage': 'Only show patches with an age greater than this value',
        'list': 'List all available projects',
        'pattern': 'When used alongside list shows only project names that contain the given string',
        'show': 'Show additional information. Valid values: url, id'
    }
    parser = argparse.ArgumentParser()
    parser.add_argument('--list', help=help['list'], type=bool, default=False)
    parser.add_argument('--project', help=help['project'])
    parser.add_argument('positional_project', nargs='?', default=None,
                        help=help['project'])
    parser.add_argument('--action', help=help['action'], default='checkout')
    parser.add_argument('--gtscore',
                        help=help['gtscore'], default=-3, type=int)
    parser.add_argument('--ltscore', help=help['gtscore'], default=3, type=int)
    parser.add_argument('--gtage', help=help['gtage'], default=-1, type=int)
    parser.add_argument('--ltage', help=help['ltage'], type=int)
    parser.add_argument('--byuser', help=help['byuser'])
    parser.add_argument('--excludeuser', help=help['excludeuser'], action="append", default=[])
    parser.add_argument('--pattern', help=help['pattern'])
    parser.add_argument('--show', help=help['show'], type=str, action="append", default=[])
    parser.add_argument('--reviewee', help=help['reviewee'])
    parser.add_argument('--ignorepattern', help=help['ignorepattern'])
    return parser

def determine_project(parser, args):
    if args.project:
         project = args.project
    elif args.positional_project:
         project = args.positional_project
    elif args.list:
         project = choose_project(args.pattern)
    else:
         project = args.project

    return project

if __name__ == '__main__':
    parser = get_parser()
    args = parser.parse_args()
    project = determine_project(parser, args)
    if args.reviewee:
        if not project:
            args.show.append('project')
            args.excludeuser.append(args.reviewee.lower())
        patches = get_incoming_patches(args.reviewee, project)
    # A project is mandatory if no reviewee
    else:
        if project is None:
            project = get_project()
            if project is None:
                print "Provide a project name as a parameter e.g. mediawiki/core"
                parser.print_help()
                sys.exit()
        patches = get_project_patches(project)

    RED = '\033[91m'
    GREEN = '\033[92m'
    GRAY = '\033[90m'
    ENDC = '\033[0m'
    BOLD = "\033[1m"
    try:
        action = args.action
        if action is None:
            action = 'checkout'
    except KeyError:
        action = 'checkout'

    if len(patches) == 0:
        print "No patches found for project %s \
- did you type it correctly?" % project
        sys.exit()

    patches = filter_patches(patches, args)
    if len(patches) == 0:
        print "No patches met the filter."
        sys.exit()
    #start on 1 since 1 is the easiest key to press on the keyboard
    key = 1
    last_score = 3
    print 'Open patchsets listed below in priority order:\n'
    for patch in patches:
        score = patch["score"]
        if score < 0 and last_score > -1:
            # add an additional new line when moving down
            # from positive to negative scores
            # to give better visual separation of patches
            print '\n'
        last_score = score
        if score < 0:
            color = RED
        else:
            color = GREEN
        score = '%s%s%s%s' % (color, BOLD, score, ENDC)
        string_args = (key, patch["subject"], patch["user"],
                patch["age"], score)
        print '%02d: %s (by %s, %s days old) [%s]' % string_args
        if 'url' in args.show:
            print '\t%s%s%s'% (GRAY, patch['url'], ENDC )
        if 'id' in args.show:
            print '\t%s%s%s'% (GRAY, patch['id'], ENDC )
        if 'project' in args.show:
            print '\t%s%s%s'% (GRAY, patch['project'], ENDC )
        key += 1
    print '\n'
    if action == 'open':
        prompt = 'Enter number of patchset to open'
    else:
        prompt = 'Enter number of patchset to checkout'
    prompt += ' (Press enter to exit):'
    choice = raw_input(prompt)
    try:
        change = patches[int(choice) - 1]
        if action == 'open':
            try:
                import platform
                if platform.system() == 'Linux':
                    import os
                    if os.environ['DESKTOP_SESSION'] == 'gnome':
                        subprocess.call(["gnome-www-browser", change["url"]])
                else:
                    subprocess.call(["open", change["url"]])
            except KeyError as e:
                # Try to fallback gracefully
                subprocess.call(["open", change["url"]])
        else:
            subprocess.call(["git", "review", "-d", change["id"]])
            print '\nReview this patch at:\n%s' % change["url"]
    except ValueError:
        pass
