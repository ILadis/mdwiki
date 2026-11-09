
import os.path
import pathlib
import hashlib
import datetime
import sqlite3
import logging
import random

class Manager:
    def __init__(self, config, repo):
        self.logger = logging.getLogger('mkdocs.plugins.files')
        self.config = config
        self.repo = repo

    @classmethod
    def to_note(cls, uid, file):
        note = dict()
        note['id'] = uid
        note['title'] = file.name[:-3]
        note['content'] = get_file_contents(file) or ''
        note['category'] = ''
        note['readonly'] = False
        note['favorite'] = False
        note['modified'] = get_file_mtime(file) or 0
        note['etag'] = get_file_etag(file)
        return note

    @classmethod
    def to_post(cls, uid, file):
        from mkdocs.utils import meta

        path = pathlib.Path(file.abs_src_path)
        source = get_file_contents(path)
        _, data = meta.get_data(source or '')

        title = data.get('title', file.name)
        summary = data.get('summary', '')
        date = data.get('date')
        tags = data.get('tags')
        public = data.get('public')

        if not isinstance(date, datetime.date):
            timestamp = get_file_mtime(path)
            date = datetime.date.fromtimestamp(timestamp or 0)
        if not isinstance(tags, list):
            tags = list()

        post = dict()
        post['id'] = uid
        post['title'] = title
        post['summary'] = summary
        post['date'] = date
        post['tags'] = tags
        post['public'] = public
        post['url'] = file.dest_path
        return post

    def update_files(self, files):
        # TODO add current timestamp to files table
        # TODO use this timestamp to find old files and check whether they were "moved by copying"

        for file in files.documentation_pages():
            path = pathlib.Path(file.abs_src_path)
            self.repo.update_file(path)
        self.files = files

    def file_by_path(self, path):
        if path.endswith('/'): path += 'index.html'

        for file in self.files.documentation_pages():
            if path.endswith(file.dest_path): break
        else: return False

        return file

    def create_note(self, title='', content='', category=''):
        file = pathlib.Path(self.config.docs_dir)
        file = file.joinpath(title + '.md')

        # never overwrite existing files when attempting to create new notes
        if file.is_file(): return False
        file.write_text(content)

        uid = self.repo.update_file(file)
        self.logger.info('Created new note and associated file uid %d', uid)

        note = self.to_note(uid, file)
        return note

    def update_note(self, uid, title='', content='', category=''):
        path = self.repo.file_path_by_uid(uid)
        if not path:
            self.logger.error('Failed to update note, file with uid %d not found', uid)
            return False

        # this may create the file again if it was deleted somehow
        file = pathlib.Path(path)
        file.write_text(content)

        # rename file if title was changed but never overwrite existing files
        newpath = file.parent.joinpath(title + '.md')
        if not newpath.is_file():
            file = file.rename(newpath)

        uid = self.repo.update_file(file)
        self.logger.info('Updated existing note with file uid %d', uid)

        note = self.to_note(uid, file)
        return note

    # TODO consider adding modified and category filter
    def all_notes(self):
        for uid, path in self.repo.all_files():
            file = pathlib.Path(path)
            note = self.to_note(uid, file)
            yield note

    def note_by_uid(self, uid):
        path = self.repo.file_path_by_uid(uid)
        if not path:
            self.logger.error('Failed to locate note, file with uid %d not found', uid)
            return False

        file = pathlib.Path(path)
        note = self.to_note(uid, file)
        return note

    def delete_note(self, uid):
        path = self.repo.file_path_by_uid(uid)
        if not path:
            self.logger.error('Failed to delete note, file with uid %d not found', uid)
            return False

        path = pathlib.Path(path)
        if path.is_file(): path.unlink()

        self.repo.delete_file(uid)
        self.logger.info('Deleted existing note with file uid %d', uid)

    def all_posts(self, tag=None, public=True):
        posts = list()

        for file in self.files.documentation_pages():
            uid = self.repo.file_uid_by_path(file.abs_src_path)
            post = self.to_post(uid, file)

            if public and not post['public']: continue
            if tag and not tag in post['tags']: continue

            posts.append(post)
        return posts

    def post_by_file(self, file):
        uid = self.repo.file_uid_by_path(file.abs_src_path)
        return self.to_post(uid, file)

    def all_tags(self, public=True):
        tags = set()

        for post in self.all_posts(None, public):
            for tag in post['tags']:
                tags.add(tag)
        return tags

def get_file_ino(file):
    try: return int(file.stat().st_ino)
    except: return False

def get_file_contents(file):
    try: return file.read_text()
    except: return False

def get_file_etag(file):
    etag = hashlib.md5()

    try:
        content = file.read_bytes()
        if len(content) > 0:
            etag.update(content)
    except: pass

    return str(etag.hexdigest())

def get_file_path(file):
    return str(file.absolute())

def get_file_mtime(file):
    try: return int(file.stat().st_mtime)
    except: return False

class Repository:
    def __init__(self, execute):
        self.execute = execute

    @classmethod
    def open(cls, path):
        from contextlib import contextmanager

        schema = ['''
            PRAGMA foreign_keys = ON''', '''
            CREATE TABLE IF NOT EXISTS "files" (
                "path" TEXT NOT NULL UNIQUE,
                "uid"  INTEGER NOT NULL,
                "ino"  INTEGER NOT NULL UNIQUE,
                "etag" TEXT NOT NULL
            ) STRICT''']

        @contextmanager
        def execute():
            conn = sqlite3.connect(path)
            try: yield conn.cursor()
            finally:
                conn.commit()
                conn.close()

        with execute() as cursor:
            for statment in schema:
                cursor.execute(statment)

        return cls(execute)

    def update_file(self, file):
        uid = random.randint(
            100_000_000_000_000,
            999_999_999_999_999)

        ino  = get_file_ino(file)
        path = get_file_path(file)
        etag = get_file_etag(file)

        if ino is False: return None

        # TODO when an entry for an inode with a different path already exists an error is thrown
        # (this can happen when the same inode is reused by another file later and that entry was not removed)
        parameters = (str(path), int(uid), int(ino), str(etag))
        statement = '''
            INSERT INTO "files" ("path", "uid", "ino", "etag")
            VALUES (?, ?, ?, ?)
            ON CONFLICT("path") DO UPDATE SET
                "ino"  = "excluded"."ino",
                "etag" = "excluded"."etag"
            ON CONFLICT("ino") DO UPDATE SET
                "path" = "excluded"."path",
                "etag" = "excluded"."etag"
            RETURNING "uid"
            '''

        with self.execute() as cursor:
            cursor.execute(statement, parameters)
            result = cursor.fetchone()
            return int(result[0]) if result else None

    def delete_file(self, uid):
        with self.execute() as cursor:
            cursor.execute('DELETE FROM "files" WHERE "uid"=?', [int(uid)])

    def all_files(self):
        with self.execute() as cursor:
            cursor.execute('SELECT "uid", "path" FROM "files"')
            for result in cursor:
                yield (int(result[0]), str(result[1]))

    def file_uid_by_path(self, path):
        with self.execute() as cursor:
            cursor.execute('SELECT "uid" FROM "files" WHERE "path"=?', [str(path)])
            result = cursor.fetchone()
            return int(result[0]) if result else None

    def file_path_by_uid(self, uid):
        with self.execute() as cursor:
            cursor.execute('SELECT "path" FROM "files" WHERE "uid"=?', [int(uid)])
            result = cursor.fetchone()
            return str(result[0]) if result else None
