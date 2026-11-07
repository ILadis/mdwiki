
import unittest
import json

from utils import MdWikiInstance

class NotesApiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        MdWikiInstance.start()
        NotesApiTest.id = 0

    @classmethod
    def tearDownClass(cls):
        MdWikiInstance.stop()

    def test_1_creation_of_note(self):
        # act
        api = MdWikiInstance.call_api('POST', 'index.php/apps/notes/api/v1/notes', '''
            {
                "title": "New note",
                "content": "This is a new note, how exciting!"
            }''')

        note = json.loads(api.read() or '{ }')

        # assert
        self.assertEqual(200, api.status)
        self.assertTrue(0 < note['id'])
        self.assertEqual('New note', note['title'])
        self.assertEqual('This is a new note, how exciting!', note['content'])
        self.assertEqual('527426e7bfd2e01e228c6646c7579812', note['etag'])

        # assign
        NotesApiTest.id = note['id']

    def test_2_update_of_note_content(self):
        # act
        api = MdWikiInstance.call_api('PUT', f'index.php/apps/notes/api/v1/notes/{self.id}', '''
            {
                "title": "Changed title",
                "content": "New note ... now with updated contents!"
            }''')

        note = json.loads(api.read() or '{ }')

        # assert
        self.assertEqual(200, api.status)
        self.assertEqual(self.id, note['id'])
        self.assertEqual('Changed title', note['title'])
        self.assertEqual('New note ... now with updated contents!', note['content'])
        self.assertEqual('fc769fb97c6e330c5e0e06ae6fa94450', note['etag'])

    def test_3_deletion_of_note(self):
        # arrange
        api = MdWikiInstance.call_api('DELETE', f'index.php/apps/notes/api/v1/notes/{self.id}')

        # assert
        self.assertEqual(200, api.status)

    def test_4_creation_of_note_without_title(self):
        # act
        api = MdWikiInstance.call_api('POST', 'index.php/apps/notes/api/v1/notes', '''
            {
                "title": "",
                "content": "Creating a new note without title!"
            }''')

        note = json.loads(api.read() or '{ }')

        # assert
        self.assertEqual(200, api.status)
        self.assertTrue(0 < note['id'])
        self.assertEqual('Untitled', note['title'])
        self.assertEqual('Creating a new note without title!', note['content'])
        self.assertEqual('483521d1215a4715899bd866e6a72878', note['etag'])

        # assign
        NotesApiTest.id = note['id']

    def test_5_deletion_of_note(self):
        # arrange
        api = MdWikiInstance.call_api('DELETE', f'index.php/apps/notes/api/v1/notes/{self.id}')

        # assert
        self.assertEqual(200, api.status)

if __name__ == '__main__':
    unittest.main()
