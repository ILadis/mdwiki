
import unittest
import json

from utils import MdWikiInstance

class FastNotesApiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        MdWikiInstance.start()
        FastNotesApiTest.id = 0

    @classmethod
    def tearDownClass(cls):
        MdWikiInstance.stop()

    def test_1_creation_of_note(self):
        # act
        api = MdWikiInstance.call_api('POST', 'index.php/apps/notes/api/v1/notes', '''
            {
                "title": "Fast note",
                "content": "No updates yet"
            }''')

        note = json.loads(api.read() or '{ }')

        # assert
        self.assertEqual(200, api.status)
        self.assertTrue(0 < note['id'])

        # assign
        FastNotesApiTest.id = note['id']

    def test_2_fast_updates_of_note(self):
        # arrange
        etags = []

        for counter in range(1, 100):
            # act
            call = MdWikiInstance.call_api('PUT', f'index.php/apps/notes/api/v1/notes/{self.id}', '''
                {
                    "title": "Fast note",
                    "content": "Update no. %d"
                }''' % counter)

            api = MdWikiInstance.call_api('GET', f'index.php/apps/notes/api/v1/notes/{self.id}')
            note = json.loads(api.read() or '{ }')

            # assert
            self.assertEqual(200, call.status)
            self.assertEqual(200, api.status)
            self.assertEqual('Update no. %d' % counter, note['content'])
            self.assertFalse(note['etag'] in etags)

            # assign
            etags.append(note['etag'])

    def test_3_deletion_of_note(self):
        # arrange
        api = MdWikiInstance.call_api('DELETE', f'index.php/apps/notes/api/v1/notes/{self.id}')

        # assert
        self.assertEqual(200, api.status)
