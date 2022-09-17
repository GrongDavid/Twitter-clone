import os
from unittest import TestCase
from sqlalchemy import exc

from models import db, User, Message, Follows, Likes

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app
db.create_all()

class MessageModelTestCase(TestCase):
    def setUp(self):
        db.drop_all()
        db.create_all()

        user = User.signup("user4", "testemail4@gmail.com", "abc123", None)
        user.id = 4
        db.session.commit()

        self.user = User.query.get(self.user.id)

        self.client = app.test_client()

    def tearDown(self):
        down = super().tearDown()
        db.session.rollback()
        return down

    def test_message(self):
        message = Message(text="random message", user_id=self.user.id)

        db.session.add(message)
        db.session.commit()

        self.assertEqual(len(self.user.messages), 1)
        self.assertEqual(self.user.messages[0].text, "random message")

    def test_message_likes(self):
        m1 = Message(text="random message", user_id=self.user.id)

        m2 = Message(text="another random message", user_id=self.user.id)

        user = User.signup("user5", "testemail5@gmail.com", "abc123", None)
        user.id = 5
        db.session.add_all([m1, m2, user])
        db.session.commit()

        user.likes.append(m1)

        db.session.commit()

        likes = Likes.query.filter(Likes.user_id == user.id).all()
        self.assertEqual(len(likes), 1)
        self.assertEqual(likes[0].message_id, m1.id)



