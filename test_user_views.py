import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes, Follows
from bs4 import BeautifulSoup

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

from app import app, CURR_USER_KEY

db.create_all()

app.config['WTF_CSRF_ENABLED'] = False

class MessageViewTestCase(TestCase):
    def setUp(self):
        db.drop_all()
        db.create_all()

        self.client = app.test_client()

        self.testuser = User.signup(username="user",
                                    email="test@gmail.com",
                                    password="abc123",
                                    image_url=None)
        self.testuser.id = 123

        self.u1 = User.signup("u1", "testemail1@gmail.com", "abc123", None)
        self.u1.id = 1
        self.u2 = User.signup("u2", "testemail2@gmail.com", "abc123", None)
        self.u2.id = 2
        self.u3 = User.signup("u3", "testemail3@gmail.com", "abc123", None)
        self.u3.id = 3
        self.u4 = User.signup("u4", "testemail4@gmail.com", "abc123", None)
        self.u4.id = 4

        db.session.commit()

    def tearDown(self):
        response = super().tearDown()
        db.session.rollback()
        return response

    def test_index(self):
        with self.client as c:
            response = c.get("/users")

            self.assertIn("user", str(response.data))
            self.assertIn("u1", str(response.data))
            self.assertIn("u2", str(response.data))
            self.assertIn("u3", str(response.data))
            self.assertIn("u4", str(response.data))

    def test_search(self):
        with self.client as c:
            response = c.get("/users?q=test")

            self.assertIn("@user", str(response.data))           

            self.assertNotIn("u1", str(response.data))
            self.assertNotIn("u2", str(response.data))
            self.assertNotIn("u3", str(response.data))

    def test_user_show(self):
        with self.client as c:
            response = c.get(f"/users/{self.testuser.id}")

            self.assertEqual(response.status_code, 200)

            self.assertIn("@testuser", str(response.data))

    def setup_likes(self):
        m1 = Message(text="random message 1", user_id=self.testuser.id)
        m2 = Message(text="random message 2", user_id=self.testuser.id)
        m3 = Message(id=1, text="some other random message", user_id=self.u1.id)
        db.session.add_all([m1, m2, m3])
        db.session.commit()

        l1 = Likes(user_id=self.testuser.id, message_id=1)

        db.session.add(l1)
        db.session.commit()

    def test_show_likes(self):
        self.setup_likes()

        with self.client as c:
            response = c.get(f"/users/{self.testuser.id}")

            self.assertEqual(response.status_code, 200)

            self.assertIn("@testuser", str(response.data))
            soup = BeautifulSoup(str(response.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})

            self.assertEqual(len(found), 4)
            self.assertIn("2", found[0].text)
            self.assertIn("0", found[1].text)
            self.assertIn("0", found[2].text)
            self.assertIn("1", found[3].text)

    def test_add_like(self):
        m = Message(id=10, text="like message", user_id=self.u1.id)
        db.session.add(m)
        db.session.commit()

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.post("/messages/10/like", follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==10).all()
            self.assertEqual(len(likes), 1)
            self.assertEqual(likes[0].user_id, self.testuser.id)

    def test_undo_like(self):
        self.setup_likes()

        m = Message.query.filter(Message.text=="likable warble").one()
        self.assertIsNotNone(m)
        self.assertNotEqual(m.user_id, self.testuser.id)

        l = Likes.query.filter(
            Likes.user_id==self.testuser.id and Likes.message_id==m.id
        ).one()

        self.assertIsNotNone(l)

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.post(f"/messages/{m.id}/like", follow_redirects=True)
            self.assertEqual(response.status_code, 200)

            likes = Likes.query.filter(Likes.message_id==m.id).all()
            self.assertEqual(len(likes), 0)

    def setup_followers(self):
        f1 = Follows(user_being_followed_id=self.u1.id, user_following_id=self.testuser.id)
        f2 = Follows(user_being_followed_id=self.u2.id, user_following_id=self.testuser.id)
        f3 = Follows(user_being_followed_id=self.testuser.id, user_following_id=self.u1.id)

        db.session.add_all([f1,f2,f3])
        db.session.commit()

    def test_follows(self):
        self.setup_followers()

        with self.client as c:
            response = c.get(f"/users/{self.testuser.id}")

            self.assertEqual(response.status_code, 200)

            self.assertIn("@testuser", str(response.data))
            soup = BeautifulSoup(str(response.data), 'html.parser')
            found = soup.find_all("li", {"class": "stat"})

            self.assertEqual(len(found), 4)
            self.assertIn("0", found[0].text)
            self.assertIn("2", found[1].text)
            self.assertIn("1", found[2].text)
            self.assertIn("0", found[3].text)

    def test_show_following(self):
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.get(f"/users/{self.testuser.id}/following")
            self.assertEqual(response.status_code, 200)
            self.assertIn("@u1", str(response.data))
            self.assertIn("@u2", str(response.data))
            self.assertNotIn("@u3", str(response.data))
            self.assertNotIn("@u4", str(response.data))

    def test_show_followers(self):
        self.setup_followers()
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            response = c.get(f"/users/{self.testuser.id}/followers")

            self.assertIn("@u1", str(response.data))
            self.assertNotIn("@u2", str(response.data))
            self.assertNotIn("@u3", str(response.data))
            self.assertNotIn("@u4", str(response.data))

    def test_unauthorized_following_page_access(self):
        self.setup_followers()
        with self.client as c:

            response = c.get(f"/users/{self.testuser.id}/following", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("@u1", str(response.data))
            self.assertIn("Access unauthorized", str(response.data))

    def test_unauthorized_followers_page_access(self):
        self.setup_followers()
        with self.client as c:

            response = c.get(f"/users/{self.testuser.id}/followers", follow_redirects=True)
            self.assertEqual(response.status_code, 200)
            self.assertNotIn("@u1", str(response.data))
            self.assertIn("Access unauthorized", str(response.data))
