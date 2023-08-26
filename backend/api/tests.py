from http import HTTPStatus

from django.test import Client, TestCase
from recipe import models
from users import models


class FoodgramAPITestCase(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_list_exists(self):
        """Проверка доступности списка рецептов."""
        response = self.guest_client.get('/api/recipes/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_task_creation(self):
        """Проверка создания рецепта."""
        data = {
            "ingredients": [{"id": 1, "amount": 10}],
            "tags": [1],
            "image": ("data:image/png;base64,iVBORw0K"
                      "GgoAAAANSUhEUgAAAAEAAAABAgMAAA"
                      "BieywaAAAACVBMVEUAAAD///9fX1/S"
                      "0ecCAAAACXBIWXMAAA7EAAAOxAGVKw"
                      "4bAAAACklEQVQImWNoAAAAggCByxOy"
                      "YQAAAABJRU5ErkJggg=="),

            "name": "string",
            "text": "string",
            "cooking_time": 1
        }
        response = self.guest_client.post('/api/recipes/', data=data)
        self.assertEqual(response.status_code, HTTPStatus.CREATED)
        self.assertTrue(models.Recipe.objects.filter(title='Test').exists())
