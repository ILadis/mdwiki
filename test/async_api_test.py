
import unittest
import asyncio
import json

from utils import MdWikiInstance

class AsyncNotesApiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        MdWikiInstance.start()
        AsyncNotesApiTest.id = 0
        AsyncNotesApiTest.etag = ''

    @classmethod
    def tearDownClass(cls):
        MdWikiInstance.stop()

    def test_1_creation_of_note(self):
        # act
        api = MdWikiInstance.call_api('POST', 'index.php/apps/notes/api/v1/notes', '''
            {
                "title": "Async note",
                "content": "No updates yet"
            }''')

        note = json.loads(api.read() or '{ }')

        # assert
        self.assertEqual(200, api.status)
        self.assertTrue(0 < note['id'])

        # assign
        AsyncNotesApiTest.id = note['id']
        AsyncNotesApiTest.etag = note['etag']

    def test_2_async_updates_of_note(self):
        # arrange
        loop = asyncio.new_event_loop()
        successes = 0
        calls = []

        for counter in range(1, 100):
            call = MdWikiInstance.call_api('PUT', f'index.php/apps/notes/api/v1/notes/{self.id}','''
                {
                    "title": "Async note",
                    "content": "Call no. %d"
                }''' % counter, headers={ 'if-match': f'"{self.etag}"' }, defer=loop)
            calls.append(call)

        # act
        calls, _ = loop.run_until_complete(asyncio.wait(calls))

        api = MdWikiInstance.call_api('GET', f'index.php/apps/notes/api/v1/notes/{self.id}')
        expected = json.loads(api.read() or '{ }')

        # assert
        for call in calls:
            api = call.result()
            actual = json.loads(api.read() or '{ "content": "" }')

            successes += 1 if api.status == 200 else 0

            self.assertIn(api.status, [200, 412])
            self.assertTrue(successes <= 1)
            self.assertEqual(api.status == 200, expected['content'] == actual['content'])

    def test_3_deletion_of_note(self):
        # arrange
        api = MdWikiInstance.call_api('DELETE', f'index.php/apps/notes/api/v1/notes/{self.id}')

        # assert
        self.assertEqual(200, api.status)
