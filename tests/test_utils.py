# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

from django.test import TestCase

from drf_haystack.utils import merge_dict


class MergeDictTestCase(TestCase):

    def setUp(self):
        self.dict_a = {
            "person": {
                "lastname": "Holmes",
                "combat_proficiency": [
                    "Pistol",
                    "boxing"
                ]
            },
        }
        self.dict_b = {
            "person": {
                "gender": "male",
                "firstname": "Sherlock",
                "location": {
                    "address": "221B Baker Street"
                },
                "combat_proficiency": [
                    "sword",
                    "Martial arts",
                ]
            }
        }

    def test_utils_merge_dict(self):
        self.assertEqual(merge_dict(self.dict_a, self.dict_b), {
            "person": {
                "gender": "male",
                "firstname": "Sherlock",
                "lastname": "Holmes",
                "location": {
                    "address": "221B Baker Street"
                },
                "combat_proficiency": [
                    "Martial arts",
                    "Pistol",
                    "boxing",
                    "sword",
                ]
            }
        })

    def test_utils_merge_dict_invalid_input(self):
        self.assertEqual(merge_dict(self.dict_a, "I'm not a dict!"), "I'm not a dict!")
