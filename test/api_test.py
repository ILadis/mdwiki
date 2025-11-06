
import unittest
import subprocess
import urllib, json, time

class NotesApiTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.noteid = 0
        cls.baseurl = 'http://localhost:8088/mdwiki'
        cls.process = subprocess.Popen(['python', './mkdocs.pyz'])

        # TODO read process stdout and wait for 'Serving on...' line
        time.sleep(3)

    @classmethod
    def tearDownClass(cls):
        cls.process.terminate()
        cls.process.wait()

    def test_1_creation_of_new_note(self):
        # arrange
        request = urllib.request.Request(method='POST',
            url=f'{self.baseurl}/index.php/apps/notes/api/v1/notes',
            data=b'''
                {
                  "title": "New note",
                  "content": "This is a new note, how exciting!"
                }''')

        # act
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as error:
            response = error
        body = json.loads(response.read() or '{ }')

        # assert
        self.assertEqual(200, response.status)
        self.assertTrue(0 < body['id'])
        self.assertEqual('New note', body['title'])
        self.assertEqual('This is a new note, how exciting!', body['content'])
        self.assertEqual('a1b84777521205ae8284413c0d6df4fa', body['etag'])

        # assign
        NotesApiTest.noteid = body['id']

    def test_2_update_of_new_note(self):
        # arrange
        request = urllib.request.Request(method='PUT',
            url=f'{self.baseurl}/index.php/apps/notes/api/v1/notes/{self.noteid}',
            data=b'''
                {
                  "title": "New note",
                  "content": "New note ... now with updated contents!"
                }''')

        # act
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as error:
            response = error
        body = json.loads(response.read() or '{ }')

        # assert
        self.assertEqual(200, response.status)
        self.assertEqual(self.noteid, body['id'])
        self.assertEqual('New note', body['title'])
        self.assertEqual('New note ... now with updated contents!', body['content'])
        self.assertEqual('7f65a348b4e57c2d0e0d081a42fc026b', body['etag'])

    def test_3_deletion_of_new_note(self):
        # arrange
        request = urllib.request.Request(method='DELETE',
            url=f'{self.baseurl}/index.php/apps/notes/api/v1/notes/{self.noteid}')

        # act
        try:
            response = urllib.request.urlopen(request)
        except urllib.error.HTTPError as error:
            response = error

        # assert
        self.assertEqual(200, response.status)

if __name__ == '__main__':
    unittest.main()
