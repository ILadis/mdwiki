
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
        self.assertEqual('a1b84777521205ae8284413c0d6df4fa', note['etag'])

        # assign
        NotesApiTest.id = note['id']

    def test_2_update_of_note(self):
        # act
        api = MdWikiInstance.call_api('PUT', f'index.php/apps/notes/api/v1/notes/{self.id}', '''
            {
                "title": "New note",
                "content": "New note ... now with updated contents!"
            }''')

        note = json.loads(api.read() or '{ }')

        # assert
        self.assertEqual(200, api.status)
        self.assertEqual(self.id, note['id'])
        self.assertEqual('New note', note['title'])
        self.assertEqual('New note ... now with updated contents!', note['content'])
        self.assertEqual('7f65a348b4e57c2d0e0d081a42fc026b', note['etag'])

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
        self.assertEqual('85e773dcf6b237f5d2dd381796a8f6be', note['etag'])

        # assign
        NotesApiTest.id = note['id']

    def test_5_deletion_of_note(self):
        # arrange
        api = MdWikiInstance.call_api('DELETE', f'index.php/apps/notes/api/v1/notes/{self.id}')

        # assert
        self.assertEqual(200, api.status)

if __name__ == '__main__':
    unittest.main()
