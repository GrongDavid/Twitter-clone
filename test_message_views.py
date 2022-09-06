"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -message unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, diff_user

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_diff_user_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data

db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False


class MessageViewTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""

        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.diff_user = diff_user.signup(diff_username="diff_user",
                                    email="testemail@gmail.com",
                                    password="abc123",
                                    image_url=None)
        self.diff_user_id = 8989
        self.diff_user.id = self.diff_user_id

        db.session.commit()

    def test_add_message(self):
        """Can use add a message?"""

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_diff_user_KEY] = self.diff_user.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            response = c.post("/messages/new", data={"text": "testText"})

            # Make sure it redirects
            self.assertEqual(response.status_code, 302)

            message = Message.query.one()
            self.assertEqual(message.text, "testText")

    def test_add(self):
        with self.client as c:
            response = c.post("/messages/new", data={"text": "testText"}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", str(response.data))

    def test_invalid_diff_user(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_diff_user_KEY] = 000

            response = c.post("/messages/new", data={"text": "testText"}, follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", str(response.data))
    
    def test_message(self):

        message = Message(id=1, text="random message", diff_user_id=self.diff_user_id)
        
        db.session.add(message)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_diff_user_KEY] = self.diff_user.id
            
            message = Message.query.get(1)

            response = c.get(f'/messages/{message.id}')

            self.assertEqual(response.status_code, 200)
            self.assertIn(message.text, str(response.data))

    def test_invalid_message(self):
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_diff_user_KEY] = self.diff_user.id
            
            response = c.get('/messages/0')
            self.assertEqual(response.status_code, 404)

    def test_message_delete(self):

        message = Message(id=1, text="a test message", diff_user_id=self.diff_user_id)
        db.session.add(message)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_diff_user_KEY] = self.diff_user.id

            response = c.post("/messages/1/delete", follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            message = Message.query.get(1)
            self.assertIsNone(message)

    def test_non_owner_message_delete(self):
        diff_user = diff_user.signup(diff_username="diff",
                        email="bademail@gmail.com",
                        password="abc123",
                        image_url=None)
        diff_user.id = 2

        #Message is owned by diff_user
        message = Message(id=1, text="more random messages", diff_user_id=self.diff_user_id
        )
        db.session.add(diff_user)
        db.session.add(message)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess['CURR_diff_user_KEY'] = 2

            response = c.post("/messages/1/delete", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertIn("Access unauthorized", str(response.data))

            message = Message.query.get(1)
            self.assertIsNotNone(message)

