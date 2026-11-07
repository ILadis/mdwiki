
import unittest
import asyncio
import json, time

from utils import MdWikiInstance

class StableApiIdsTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        MdWikiInstance.start()
        StableApiIdsTest.ids = list()

    @classmethod
    def tearDownClass(cls):
        MdWikiInstance.stop()

    def test_1_creation_of_note(self):
        # act
        api = MdWikiInstance.call_api('POST', 'index.php/apps/notes/api/v1/notes', '''
            {
                "title": "Stable note",
                "content": "This is a new note for testing stable ids!"
            }''')

        note = json.loads(api.read() or '{ }')

        # assert
        self.assertEqual(200, api.status)
        self.assertTrue(0 < note['id'])

        # assign
        StableApiIdsTest.ids.append(note['id'])

    def test_2_update_note_title(self):
        # act
        api = MdWikiInstance.call_api('PUT', f'index.php/apps/notes/api/v1/notes/{self.ids[0]}', '''
            {
                "title": "Really stable note",
                "content": "This is a new note for testing stable ids!"
            }''')

        note = json.loads(api.read() or '{ }')

        # assert
        self.assertEqual(200, api.status)
        self.assertEqual(self.ids[0], note['id'])

    def test_3_creation_of_another_note(self):
        # act
        api = MdWikiInstance.call_api('POST', 'index.php/apps/notes/api/v1/notes', '''
            {
                "title": "Stable other note",
                "content": "This is a new note for testing stable ids!"
            }''')

        note = json.loads(api.read() or '{ }')

        # assert
        self.assertEqual(200, api.status)
        self.assertTrue(0 < note['id'])

        # assign
        StableApiIdsTest.ids.append(note['id'])

    def test_4_update_other_note_title(self):
        # act
        api = MdWikiInstance.call_api('PUT', f'index.php/apps/notes/api/v1/notes/{self.ids[1]}', '''
            {
                "title": "Really stable note",
                "content": "This is a new note for testing stable ids!"
            }''')

        note = json.loads(api.read() or '{ }')

        # assert
        self.assertEqual(200, api.status)
        self.assertEqual(self.ids[1], note['id'])
        self.assertEqual('Stable other note', note['title'])

    def test_5_deletion_of_other_note(self):
        # arrange
        api = MdWikiInstance.call_api('DELETE', f'index.php/apps/notes/api/v1/notes/{self.ids[1]}')

        # assert
        self.assertEqual(200, api.status)

    def test_6_rename_of_note(self):
        # arrange
        from pathlib import Path
        from mdwiki.files import Repository

        repo = Repository.open('files.db')
        path = Path(repo.file_path_by_uid(self.ids[0]))

        path.rename(path.parent.joinpath('Stable but renamed.md'))
        time.sleep(1)

        # act
        api = MdWikiInstance.call_api('GET', f'index.php/apps/notes/api/v1/notes/{self.ids[0]}')
        note = json.loads(api.read() or '{ }')

        # assert
        self.assertEqual(200, api.status)
        self.assertEqual('Stable but renamed', note['title'])

    def test_7_replace_of_note(self):
        # arrange
        from pathlib import Path
        from mdwiki.files import Repository

        repo = Repository.open('files.db')
        path = Path(repo.file_path_by_uid(self.ids[0]))

        path.unlink()
        time.sleep(1)

        path.write_text('New content')
        time.sleep(1)

        # act
        api = MdWikiInstance.call_api('GET', f'index.php/apps/notes/api/v1/notes/{self.ids[0]}')
        note = json.loads(api.read() or '{ }')

        # assert
        self.assertEqual(200, api.status)
        self.assertEqual('New content', note['content'])

    def test_8_deletion_of_note(self):
        # arrange
        api = MdWikiInstance.call_api('DELETE', f'index.php/apps/notes/api/v1/notes/{self.ids[0]}')

        # assert
        self.assertEqual(200, api.status)

if __name__ == '__main__':
    unittest.main()
