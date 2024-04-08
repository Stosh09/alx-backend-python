#!/usr/bin/env python3
"""
Module test_client
Implements TestMethods for the client.py file
"""
import unittest
from unittest.mock import patch, Mock, PropertyMock, call
from parameterized import parameterized, parameterized_class
from client import GithubOrgClient
from fixtures import TEST_PAYLOAD


class TestGithubOrgClient(unittest.TestCase):
    """Test GithubOrgClient functionality"""

    @parameterized.expand([
        ("google", {"google": True}),
        ("abc", {"abc": True})
    ])
    @patch('client.get_json')
    def test_org(self, org, expected, get_patch):
        """Test org retrieval"""
        get_patch.return_value = expected
        client = GithubOrgClient(org)
        self.assertEqual(client.org, expected)
        get_patch.assert_called_once_with("https://api.github.com/orgs/"+org)

    def test_public_repos_url(self):
        """Test _public_repos_url property"""
        expected = "www.yes.com"
        payload = {"repos_url": expected}
        with patch('client.GithubOrgClient.org',
                   PropertyMock(return_value=payload)):
            client = GithubOrgClient("x")
            self.assertEqual(client._public_repos_url, expected)

    @patch('client.get_json')
    def test_public_repos(self, get_json_mock):
        """Test public repos"""
        jeff = {"name": "Jeff", "license": {"key": "a"}}
        bobb = {"name": "Bobb", "license": {"key": "b"}}
        suee = {"name": "Suee"}
        with patch('client.GithubOrgClient._public_repos_url',
                   PropertyMock(return_value="www.yes.com")) as url_mock:
            get_json_mock.return_value = [jeff, bobb, suee]
            client = GithubOrgClient("x")

            self.assertEqual(client.public_repos(), ['Jeff', 'Bobb', 'Suee'])
            self.assertEqual(client.public_repos("a"), ['Jeff'])
            self.assertEqual(client.public_repos("c"), [])
            self.assertEqual(client.public_repos(45), [])

            get_json_mock.assert_called_once_with("www.yes.com")
            url_mock.assert_called_once_with()

    @parameterized.expand([
        ({'license': {'key': 'my_license'}}, 'my_license', True),
        ({'license': {'key': 'other_license'}}, 'my_license', False)
    ])
    def test_has_license(self, repo, license, expected):
        """Test the license checker"""
        self.assertEqual(GithubOrgClient.has_license(repo, license), expected)


@parameterized_class(
    ('org_payload', 'repos_payload', 'expected_repos', 'apache2_repos'),
    TEST_PAYLOAD
)
class TestIntegrationGithubOrgClient(unittest.TestCase):
    """Integration test for GithubOrgClient"""

    @classmethod
    def setUpClass(cls):
        """Prepare for testing"""
        org = TEST_PAYLOAD[0][0]
        repos = TEST_PAYLOAD[0][1]
        cls.org_mock = Mock(json=Mock(return_value=org))
        cls.repos_mock = Mock(json=Mock(return_value=repos))

        cls.get_patcher = patch('requests.get')
        cls.get = cls.get_patcher.start()

        options = {org["repos_url"]: cls.repos_mock}
        cls.get.side_effect = lambda y: options.get(y, cls.org_mock)

    @classmethod
    def tearDownClass(cls):
        """Unprepare for testing"""
        cls.get_patcher.stop()

    def test_public_repos(self):
        """Test public repos"""
        client = GithubOrgClient("x")
        self.assertEqual(client.org, self.org_payload)
        self.assertEqual(client.repos_payload, self.repos_payload)
        self.assertEqual(client.public_repos(), self.expected_repos)
        self.assertEqual(client.public_repos("NONEXISTENT"), [])
        self.get.assert_has_calls(
            [call("https://api.github.com/orgs/x"),
             call(self.org_payload["repos_url"])])

    def test_public_repos_with_license(self):
        """Test public repos with license"""
        client = GithubOrgClient("x")
        self.assertEqual(client.org, self.org_payload)
        self.assertEqual(client.repos_payload, self.repos_payload)
        self.assertEqual(client.public_repos(), self.expected_repos)
        self.assertEqual(client.public_repos("NONEXISTENT"), [])
        self.assertEqual(client.public_repos("apache-2.0"),
                         self.apache2_repos)
        self.get.assert_has_calls(
            [call("https://api.github.com/orgs/x"),
             call(self.org_payload["repos_url"])])


if __name__ == '__main__':
    unittest.main()
