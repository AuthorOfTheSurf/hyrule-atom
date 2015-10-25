#! /usr/bin/env python
"""
Unit tests
"""

import unittest
import os
import parser
import aggregator
from service import WaferService
from py2neo import Graph
from py2neo import Node, Relationship
import requests
import datetime


class test_pipeline(unittest.TestCase):
    LEN_DATETIME = 26
    LEN_TEST_FILE = 632

    def setUp(self):
        try:
            __location__ = os.path.realpath(
                os.path.join(os.getcwd(), os.path.dirname(__file__)))
            self.src = open(
                os.path.join(__location__, "data/bit-test-data.txt"))
            self.badFreq = open(
                os.path.join(__location__, "data/bad-frequency.txt"))
            self.badStartTime = open(
                os.path.join(__location__, "data/bad-starttime.txt"))
            self.graph = Graph("http://localhost:8484/db/data")
            self.graph.delete_all()
            self.service = WaferService(self.graph)
        except:
            print "Error during unittest setup"

    def tearDown(self):
        self.graph.delete_all()

    #
    # File tests
    #
    def test_open(self):
        self.assertEquals(len(self.src.read().split("\n")), 20)

    #
    # Parser tests
    #
    def test_parser(self):
        bitdo = parser.BITdo(self.src)
        self.assertEquals(len(bitdo.toJson()), test_pipeline.LEN_TEST_FILE)
        self.assertEquals(len(bitdo.channels.keys()), 5)
        self.assertEquals(bitdo.header["SamplingFrequency"], "1000")
        self.assertEquals(len(bitdo.channels["EMG"]), 16)
        # Assure that datetime is to microsecond precision
        self.assertEquals(
            len(bitdo.header["StartDateTime"]), test_pipeline.LEN_DATETIME)


    def test_parser_errors(self):
        self.assertRaises(AttributeError, parser.BITdo, (self.badFreq))
        self.assertRaises(AttributeError, parser.BITdo, (self.badStartTime))

    #
    # Aggregator tests
    #
    def test_aggregator_nums(self):
        a = [0, 0, 1, 1, 1]
        s = aggregator.streaksIn(a)
        self.assertEquals(s[0].getStreaks(), [2])
        self.assertEquals(s[0].getStreakExp(2), [4])
        self.assertEquals(s[1].getStreaks(), [3])
        self.assertEquals(s[1].getStreakExp(2), [9])


    def test_aggregator_bools(self):
        b = [True, False, False, True, False]
        s = aggregator.streaksIn(b)
        self.assertEquals(s[True].getStreaks(), [1, 1])
        self.assertEquals(s[False].getStreaks(), [2, 1])
        self.assertEquals(s[False].getStreakExp(2), [4, 1])


    def test_aggregator_strings(self):
        c = ["cat", "826", "826", "826", "~~", "~~", "cat", "cat", "~~"]
        s = aggregator.streaksIn(c)
        self.assertEquals(s["cat"].getStreaks(), [1, 2])
        self.assertEquals(s["cat"].getStreakExp(2), [1, 4])
        self.assertEquals(s["826"].getStreaks(), [3])
        self.assertEquals(s["826"].getStreakExp(3), [27])
        self.assertEquals(s["~~"].getStreaks(), [2, 1])
        self.assertEquals(s["~~"].getStreakExp(-1), [0.5, 1])


    def test_aggregator_average(self):
        bitdo = parser.BITdo(self.src)
        self.assertEquals(aggregator.average(bitdo.channels['EMG']), 525.4375)
        self.assertEquals(aggregator.average([1, 2, 3]), 2)
        self.assertEquals(aggregator.average([x for x in range(1000)]), 499.5)

    #
    # Graph Service
    #
    def test_add_new_user(self):
        user = self.service.add_user("Duke")
        userid = user.properties["userid"]
        activity = self.service.add_activity(
            userid, "Free Throws", "no description")
        activityname = activity.properties["name"]
        self.service.add_moment(
            userid, activityname, "timestamp", ["a1:true", "a2:false"])
        self.service.add_moment(
            userid, activityname, "timestamp", ["a1:true", "a2:false"])
        self.assertEquals(count(self.graph.find("User")), 1)
        self.assertEquals(count(self.graph.find("Activity")), 1)
        self.assertEquals(count(self.graph.find("Moment")), 2)
        self.assertEquals(count(self.graph.find("Annotation")), 2)

    #
    # Graph API
    #
    def test_post_user(self):
        r = newUser('Thaddeus')
        self.assertEquals(r.status_code, 200)


    def test_post_user_fails(self):
        r = requests.post('http://localhost:8000/users', {})
        self.assertEquals(r.status_code, 400)


    def test_post_activity(self):
        r = newUser('Thaddeus')
        self.assertEquals(r.status_code, 200)
        r = newActivity('Thaddeus', 'Free-throw shooting')
        self.assertEquals(r.status_code, 200)


    def test_post_activity_fails(self):
        r = newUser('Thaddeus')
        self.assertEquals(r.status_code, 200)

        # Test explicitly, i.e. not using the helper function
        # so we are able to neglect parameters
        r = requests.post('http://localhost:8000/activities', {
            'userid': 'Thaddeus'})
        self.assertEquals(r.status_code, 400)
        r = requests.post('http://localhost:8000/users', {
            'name': 'Free-throw shooting'})
        self.assertEquals(r.status_code, 400)


    def test_post_moment(self):
        r = newUser('Thaddeus')
        self.assertEquals(r.status_code, 200)
        r = newActivity('Thaddeus', 'Free-throw shooting')
        self.assertEquals(r.status_code, 200)

        r = newMoment('Thaddeus', 'Free-throw shooting', now(), ["make:true", "swish:true"])
        self.assertEquals(r.status_code, 201)


    def test_post_moment_fails(self):
        r = newUser('Thaddeus')
        self.assertEquals(r.status_code, 200)
        r = newActivity('Thaddeus', 'Free-throw shooting')
        self.assertEquals(r.status_code, 200)

        # Test explicitly, i.e. not using the helper function
        # so we are able to neglect parameters
        annotations = ["make:true", "swish:true"]
        r = requests.post('http://localhost:8000/moments', {
            # missing userid
            'name': 'Free-throw shooting',
            'timestamp': now(),
            'annotations[]': annotations})
        self.assertEquals(r.status_code, 400)

        r = requests.post('http://localhost:8000/moments', {
            'userid': 'Thaddeus',
            'name': 'Free-throw shooting',
            'timestamp': now()
            # missing annotations
        })
        self.assertEquals(r.status_code, 400)

        r = requests.post('http://localhost:8000/moments', {
            'userid': 'Thaddeus',
            'name': 'Free-throw shooting',
            'timestamp': now(),
            # it's `annotations[]`... sigh
            'annotations': annotations})
        self.assertEquals(r.status_code, 400)


    def test_get_moment(self):
        r = newUser('Thaddeus')
        self.assertEquals(r.status_code, 200)
        r = newActivity('Thaddeus', 'Free-throw shooting')
        self.assertEquals(r.status_code, 200)

        newMoment('Thaddeus', 'Free-throw shooting', now(), ["make:true", "swish:true"])
        newMoment('Thaddeus', 'Free-throw shooting', now(), ["make:false", "swish:false"])
        newMoment('Thaddeus', 'Free-throw shooting', now(), ["make:true", "swish:false"])
        r = getMoments('Thaddeus', 'Free-throw shooting')
        self.assertEquals(r.status_code, 200)
        self.assertEquals(len(r.json()), 3)


    def test_get_moment_fails(self):
        r = newUser('Thaddeus')
        self.assertEquals(r.status_code, 200)
        r = newActivity('Thaddeus', 'Basketball')
        self.assertEquals(r.status_code, 200)

        newMoment('Thaddeus', 'Free-throw shooting', now(), ["make:true", "swish:true"])
        newMoment('Thaddeus', 'Free-throw shooting', now(), ["make:false", "swish:false"])
        newMoment('Thaddeus', 'Free-throw shooting', now(), ["make:true", "swish:false"])
        # wrong acitivity name
        r = getMoments('Thaddeus', 'B_sketb_ll')
        self.assertEquals(r.status_code, 400)

##
## Test Helpers
##

api_url = 'http://localhost:8000'
users_url = api_url + '/users'
activities_url = api_url + '/activities'
moments_url = api_url + '/moments'


def newUser(userid):
    return requests.post(users_url, {
        'userid': userid
    })


def newActivity(userid, name):
    return requests.post(activities_url, {
        'userid': userid,
        'name': name
    })


def newMoment(userid, name, timestamp, annotations):
    return requests.post(moments_url, {
        'userid': userid,
        'name': name,
        'timestamp': timestamp,
        'annotations[]': annotations
    })


def getMoments(userid, name):
    return requests.get(moments_url, params={
        'userid': userid,
        'name': name
    })


def count(iter):
    try:
        return len(iter)
    except TypeError:
        return sum(1 for _ in iter)


def now():
    return datetime.datetime.now().isoformat(" ")

if __name__ == '__main__':
    unittest.main()
