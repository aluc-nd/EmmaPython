from datetime import datetime
import unittest
from emma import exceptions as ex
from emma.enumerations import DeliveryType, MemberStatus, MemberChangeType
from emma.model import SERIALIZED_DATETIME_FORMAT
from emma.model.account import Account
from emma.model.member import (Member, MemberGroupCollection,
                                 MemberMailingCollection)
from emma.model.group import Group
from emma.model.mailing import Mailing
from tests.model import MockAdapter


class MemberTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.member = Member(
            Account(account_id="100", public_key="xxx", private_key="yyy"),
            {
                'member_id':1000,
                'email':u"test@example.com",
                'status':u"opt-out",
                'member_status_id':u"o",
                'change_type':u"u",
                'last_modified_at': datetime.now().strftime(SERIALIZED_DATETIME_FORMAT),
                'member_since': datetime.now().strftime(SERIALIZED_DATETIME_FORMAT),
                'deleted_at': None
            }
        )
        self.member.account.fields._dict = {
            2000: {'shortcut_name': u"first_name"},
            2001: {'shortcut_name': u"last_name"}
        }

    def test_can_parse_special_fields_correctly(self):
        self.assertIsInstance(self.member['last_modified_at'], datetime)
        self.assertIsInstance(self.member['member_since'], datetime)
        self.assertIsNone(self.member.get('deleted_at'))

    def test_can_represent_a_member(self):
        self.assertEquals(
            u"<Member" + repr(self.member._dict) + u">",
            repr(self.member))

    def test_can_set_valid_field_value_with_dictionary_access(self):
        self.member['first_name'] = u"Emma"
        self.assertEquals(u"Emma", self.member['first_name'])

    def test_group_collection_can_be_accessed(self):
        self.assertIsInstance(self.member.groups, MemberGroupCollection)

    def test_mailing_collection_can_be_accessed(self):
        self.assertIsInstance(self.member.mailings, MemberMailingCollection)

    def test_can_get_opt_out_detail_for_member(self):
        MockAdapter.expected = []
        detail = self.member.get_opt_out_detail()
        self.assertIsInstance(detail, list)
        self.assertEquals(self.member.account.adapter.called, 1)

    def test_can_get_opt_out_detail_for_member2(self):
        MockAdapter.expected = []
        member = Member(self.member.account)
        with self.assertRaises(ex.NoMemberIdError):
            member.get_opt_out_detail()
        self.assertEquals(member.account.adapter.called, 0)

    def test_can_get_opt_out_detail_for_member3(self):
        MockAdapter.expected = []
        self.member['member_status_id'] = MemberStatus.Active
        self.member.get_opt_out_detail()
        self.assertEquals(self.member.account.adapter.called, 0)

    def test_can_ask_if_member_has_opted_out(self):
        has_opted_out = self.member.has_opted_out()
        self.assertIsInstance(has_opted_out, bool)
        self.assertTrue(has_opted_out)
        self.assertEquals(self.member.account.adapter.called, 0)

    def test_can_ask_if_member_has_opted_out2(self):
        member = Member(
            self.member.account,
            {
                'member_id':1000,
                'email':u"test@example.com",
                'member_status_id':u"active"
            }
        )
        has_opted_out = member.has_opted_out()
        self.assertIsInstance(has_opted_out, bool)
        self.assertFalse(has_opted_out)
        self.assertEquals(member.account.adapter.called, 0)

    def test_can_ask_if_member_has_opted_out3(self):
        member = Member(self.member.account)
        with self.assertRaises(ex.NoMemberStatusError):
            member.has_opted_out()
        self.assertEquals(member.account.adapter.called, 0)

    def test_can_opt_out_a_member(self):
        member = Member(self.member.account)
        with self.assertRaises(ex.NoMemberEmailError):
            member.opt_out()
        self.assertEquals(member.account.adapter.called, 0)

    def test_can_opt_out_a_member2(self):
        member = Member(
            self.member.account,
            {
                'member_id':1000,
                'email':u"test@example.com",
                'member_status_id':u"a"
            }
        )
        MockAdapter.expected = True
        self.assertFalse(member.has_opted_out())
        result = member.opt_out()
        self.assertIsNone(result)
        self.assertEquals(member.account.adapter.called, 1)
        self.assertEquals(
            member.account.adapter.call,
            ('PUT', '/members/email/optout/test@example.com', {}))
        self.assertTrue(member.has_opted_out())

    def test_can_save_a_member(self):
        mbr = Member(self.member.account, {'email':u"test@example.com"})
        MockAdapter.expected = {
            'status': u"a",
            'added': True,
            'member_id': 1024
        }
        result = mbr.save()
        self.assertIsNone(result)
        self.assertEquals(mbr.account.adapter.called, 1)
        self.assertEquals(
            mbr.account.adapter.call,
            ('POST', '/members/add', {'email':u"test@example.com"}))
        self.assertEquals(1024, mbr['member_id'])
        self.assertEquals(MemberStatus.Active, mbr['member_status_id'])

    def test_can_save_a_member2(self):
        mbr = Member(
            self.member.account,
            {'email':u"test@example.com",
             'first_name':u"Emma"})
        MockAdapter.expected = {
            'status': u"a",
            'added': True,
            'member_id': 1024
        }
        result = mbr.save()
        self.assertIsNone(result)
        self.assertEquals(mbr.account.adapter.called, 1)
        self.assertEquals(
            mbr.account.adapter.call,
            ('POST', '/members/add', {'email':u"test@example.com",
                                      'fields': {'first_name': u"Emma"}}))
        self.assertEquals(1024, mbr['member_id'])
        self.assertEquals(MemberStatus.Active, mbr['member_status_id'])

    def test_can_save_a_member3(self):
        mbr = Member(
            self.member.account,
            {'email':u"test@example.com",
             'first_name':u"Emma"})
        MockAdapter.expected = {
            'status': u"a",
            'added': True,
            'member_id': 1024
        }
        result = mbr.save(signup_form_id=u"http://example.com/signup")
        self.assertIsNone(result)
        self.assertEquals(mbr.account.adapter.called, 1)
        self.assertEquals(
            mbr.account.adapter.call,
            ('POST', '/members/add', {
                'email':u"test@example.com",
                'fields': {'first_name': u"Emma"},
                'signup_form_id': u"http://example.com/signup"}
            ))
        self.assertEquals(1024, mbr['member_id'])
        self.assertEquals(MemberStatus.Active, mbr['member_status_id'])

    def test_can_save_a_member4(self):
        mbr = Member(
            self.member.account,
            {
                'member_id': 200,
                'email':u"test@example.com",
                'first_name':u"Emma",
                'member_status_id': MemberStatus.Active
            })
        MockAdapter.expected = False

        with self.assertRaises(ex.MemberUpdateError):
            mbr.save()
        self.assertEquals(mbr.account.adapter.called, 1)
        self.assertEquals(mbr.account.adapter.call,
            (
                'PUT',
                '/members/200',
                {
                    'member_id': 200,
                    'email':u"test@example.com",
                    'fields': {'first_name': u"Emma"},
                    'status_to': mbr['member_status_id']
                }
            ))

    def test_can_save_a_member5(self):
        mbr = Member(
            self.member.account,
            {
                'member_id': 200,
                'email':u"test@example.com",
                'fields': {'first_name':u"Emma"},
                'member_status_id': MemberStatus.Active
            })
        MockAdapter.expected = True
        result = mbr.save()
        self.assertIsNone(result)
        self.assertEquals(mbr.account.adapter.called, 1)
        self.assertEquals(mbr.account.adapter.call,
            (
                'PUT',
                '/members/200',
                {
                    'member_id': 200,
                    'email':u"test@example.com",
                    'fields': {'first_name': u"Emma"},
                    'status_to': mbr['member_status_id']
                }
            ))

    def test_can_save_a_member6(self):
        mbr = Member(
            self.member.account,
            {
                'email':u"test@example.com",
                'fields': {'first_name':u"Emma"}
            })
        MockAdapter.expected = {
            'status': u"a",
            'added': True,
            'member_id': 1024
        }

        result = mbr.save(group_ids=[1025])

        self.assertIsNone(result)
        self.assertEquals(mbr.account.adapter.called, 1)
        self.assertEquals(mbr.account.adapter.call,
            (
                'POST',
                '/members/add',
                {
                    'email':u"test@example.com",
                    'fields': {'first_name': u"Emma"},
                    'group_ids': [1025]
                }
            ))

    def test_can_delete_a_member(self):
        mbr = Member(self.member.account, {'email':u"test@example.com"})

        with self.assertRaises(ex.NoMemberIdError):
            mbr.delete()
        self.assertEquals(self.member.account.adapter.called, 0)
        self.assertFalse(self.member.is_deleted())

    def test_can_delete_a_member2(self):
        MockAdapter.expected = None
        mbr = Member(
            self.member.account,
            {
                'member_id': 200,
                'email':u"test@example.com",
                'deleted_at': datetime.now().strftime(SERIALIZED_DATETIME_FORMAT)
            })

        result = mbr.delete()

        self.assertIsNone(result)
        self.assertEquals(mbr.account.adapter.called, 0)
        self.assertTrue(mbr.is_deleted())

    def test_can_delete_a_member3(self):
        MockAdapter.expected = True
        mbr = Member(
            self.member.account,
            {
                'member_id': 200,
                'email':u"test@example.com",
                'deleted_at': None
            })

        result = mbr.delete()

        self.assertIsNone(result)
        self.assertEquals(mbr.account.adapter.called, 1)
        self.assertEquals(
            mbr.account.adapter.call,
            ('DELETE', '/members/200', {}))
        self.assertTrue(mbr.is_deleted())


class MemberGroupCollectionTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.groups =  Member(
            Account(account_id="100", public_key="xxx", private_key="yyy"),
            {
                'member_id':1000,
                'email':u"test@example.com",
                'status':u"opt-out"
            }
        ).groups

    def test_fetch_all_returns_a_dictionary(self):
        groups = MemberGroupCollection(Member(self.groups.member.account))
        with self.assertRaises(ex.NoMemberIdError):
            groups.fetch_all()
        self.assertEquals(groups.member.account.adapter.called, 0)

    def test_fetch_all_returns_a_dictionary2(self):
        MockAdapter.expected = [{'member_group_id': 200}]
        self.assertIsInstance(self.groups.fetch_all(), dict)
        self.assertEquals(self.groups.member.account.adapter.called, 1)
        self.assertEquals(
            self.groups.member.account.adapter.call,
            ('GET', '/members/1000/groups', {}))

    def test_fetch_all_populates_collection(self):
        MockAdapter.expected = [{'member_group_id': 200}]
        self.assertEquals(0, len(self.groups))
        self.groups.fetch_all()
        self.assertEquals(1, len(self.groups))

    def test_fetch_all_caches_results(self):
        MockAdapter.expected = [{'member_group_id': 200}]
        self.groups.fetch_all()
        self.groups.fetch_all()
        self.assertEquals(self.groups.member.account.adapter.called, 1)

    def test_collection_can_be_accessed_like_a_dictionary(self):
        MockAdapter.expected = [{'member_group_id': 200}]
        self.groups.fetch_all()
        self.assertIsInstance(self.groups, MemberGroupCollection)
        self.assertEquals(1, len(self.groups))
        self.assertIsInstance(self.groups[200], Group)

    def test_factory_produces_a_group(self):
        grp = self.groups.factory()
        self.assertIsInstance(grp, Group)
        self.assertEquals(0, len(grp))

    def test_factory_produces_a_group2(self):
        grp = self.groups.factory({'member_group_id':1024})
        self.assertIsInstance(grp, Group)
        self.assertEquals(1, len(grp))
        self.assertEquals(1024, grp['member_group_id'])

    def test_can_add_groups_to_a_member(self):
        mbr = Member(self.groups.member.account)

        with self.assertRaises(ex.NoMemberIdError):
            mbr.groups.save([
                mbr.groups.factory({'member_group_id':1024})
            ])
        self.assertEquals(self.groups.member.account.adapter.called, 0)

    def test_can_add_groups_to_a_member2(self):
        MockAdapter.expected = []
        self.groups.save([])
        self.assertEquals(self.groups.member.account.adapter.called, 0)

    def test_can_add_groups_to_a_member3(self):
        MockAdapter.expected = [300, 301]
        self.groups.save([
            self.groups.factory({'member_group_id': 300}),
            self.groups.factory({'member_group_id': 301})
        ])
        self.assertEquals(self.groups.member.account.adapter.called, 1)
        self.assertEquals(
            self.groups.member.account.adapter.call,
            ('PUT', '/members/1000/groups', {'group_ids': [300, 301]}))

    def test_can_add_groups_to_a_member4(self):
        MockAdapter.expected = [300, 301]
        self.groups.member.add_groups([300, 301])
        self.assertEquals(self.groups.member.account.adapter.called, 1)
        self.assertEquals(
            self.groups.member.account.adapter.call,
            ('PUT', '/members/1000/groups', {'group_ids': [300, 301]}))

    def test_can_drop_groups_from_a_member(self):
        mbr = Member(self.groups.member.account)

        with self.assertRaises(ex.NoMemberIdError):
            mbr.groups.delete([300, 301])
        self.assertEquals(self.groups.member.account.adapter.called, 0)

    def test_can_drop_groups_from_a_member2(self):
        self.groups.delete()

        self.assertEquals(self.groups.member.account.adapter.called, 1)
        self.assertEquals(
            self.groups.member.account.adapter.call,
            ('DELETE', '/members/1000/groups', {})
        )
        self.assertEquals(0, len(self.groups))

    def test_can_drop_groups_from_a_member3(self):
        MockAdapter.expected = [300, 301]
        self.groups._dict = {
            300: self.groups.factory({'member_group_id': 300}),
            301: self.groups.factory({'member_group_id': 301}),
            302: self.groups.factory({'member_group_id': 302})
        }

        self.groups.delete([300, 301])

        self.assertEquals(self.groups.member.account.adapter.called, 1)
        self.assertEquals(
            self.groups.member.account.adapter.call,
            (
                'PUT',
                '/members/1000/groups/remove',
                {'group_ids': [300, 301]}))
        self.assertEquals(1, len(self.groups))
        self.assertIsInstance(self.groups[302], Group)

    def test_can_drop_groups_from_a_member4(self):
        MockAdapter.expected = [300, 301]
        self.groups._dict = {
            300: self.groups.factory({'member_group_id': 300}),
            301: self.groups.factory({'member_group_id': 301}),
            302: self.groups.factory({'member_group_id': 302})
        }

        self.groups.member.drop_groups([300, 301])

        self.assertEquals(self.groups.member.account.adapter.called, 1)
        self.assertEquals(
            self.groups.member.account.adapter.call,
            (
                'PUT',
                '/members/1000/groups/remove',
                {'group_ids': [300, 301]}))
        self.assertEquals(1, len(self.groups))
        self.assertIsInstance(self.groups[302], Group)

    def test_can_drop_groups_from_a_member5(self):
        self.groups._dict = {
            300: self.groups.factory({'member_group_id': 300}),
            301: self.groups.factory({'member_group_id': 301}),
            302: self.groups.factory({'member_group_id': 302})
        }

        self.groups.delete()

        self.assertEquals(self.groups.member.account.adapter.called, 1)
        self.assertEquals(
            self.groups.member.account.adapter.call,
            ('DELETE', '/members/1000/groups', {})
        )
        self.assertEquals(0, len(self.groups))

    def test_can_drop_groups_from_a_member6(self):
        self.groups._dict = {
            300: self.groups.factory({'member_group_id': 300}),
            301: self.groups.factory({'member_group_id': 301}),
            302: self.groups.factory({'member_group_id': 302})
        }

        self.groups.member.drop_groups()

        self.assertEquals(self.groups.member.account.adapter.called, 1)
        self.assertEquals(
            self.groups.member.account.adapter.call,
            ('DELETE', '/members/1000/groups', {})
        )
        self.assertEquals(0, len(self.groups))

    def test_can_drop_a_single_group_with_del(self):
        # Setup
        MockAdapter.expected = True
        self.groups._dict = {
            300: self.groups.factory({'member_group_id': 300}),
            301: self.groups.factory({'member_group_id': 301})
        }

        del(self.groups[300])

        self.assertEquals(self.groups.member.account.adapter.called, 1)
        self.assertEquals(
            self.groups.member.account.adapter.call,
            (
                'PUT',
                '/members/1000/groups/remove',
                {'group_ids': [300]}))
        self.assertEquals(1, len(self.groups))
        self.assertIn(301, self.groups)


class MemberMailingCollectionTest(unittest.TestCase):
    def setUp(self):
        Account.default_adapter = MockAdapter
        self.mailings =  Member(
            Account(account_id="100", public_key="xxx", private_key="yyy"),
            {
                'member_id':1000,
                'email':u"test@example.com",
                'status':u"opt-out"
            }
        ).mailings

    def test_fetch_all_returns_a_dictionary(self):
        member = Member(self.mailings.member.account)
        mailings = MemberMailingCollection(member)
        with self.assertRaises(ex.NoMemberIdError):
            mailings.fetch_all()
        self.assertEquals(mailings.member.account.adapter.called, 0)

    def test_fetch_all_returns_a_dictionary2(self):
        MockAdapter.expected = [{'mailing_id': 201, 'delivery_type':u"d"}]
        self.assertIsInstance(self.mailings.fetch_all(), dict)
        self.assertEquals(self.mailings.member.account.adapter.called, 1)
        self.assertEquals(
            self.mailings.member.account.adapter.call,
            ('GET', '/members/1000/mailings', {}))

    def test_fetch_all_populates_collection(self):
        MockAdapter.expected = [{'mailing_id': 201, 'delivery_type':u"d"}]
        self.assertEquals(0, len(self.mailings))
        self.mailings.fetch_all()
        self.assertEquals(1, len(self.mailings))

    def test_fetch_all_caches_results(self):
        MockAdapter.expected = [{'mailing_id': 201, 'delivery_type':u"d"}]
        self.mailings.fetch_all()
        self.mailings.fetch_all()
        self.assertEquals(self.mailings.member.account.adapter.called, 1)

    def test_collection_can_be_accessed_like_a_dictionary(self):
        MockAdapter.expected = [{'mailing_id': 201, 'delivery_type':u"d"}]
        self.mailings.fetch_all()
        self.assertIsInstance(self.mailings, MemberMailingCollection)
        self.assertEquals(1, len(self.mailings))
        self.assertIsInstance(self.mailings[201], Mailing)
        self.assertEquals(self.mailings[201]['mailing_id'], 201)
        self.assertEquals(
            self.mailings[201]['delivery_type'],
            DeliveryType.Delivered)
