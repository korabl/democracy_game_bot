import logging
import unittest

from user_interaction import generate_initiative_result_and_resources
from unittest import IsolatedAsyncioTestCase

logger = logging.getLogger(__name__)

class MyTestCase(IsolatedAsyncioTestCase):

    async def test_generate_initiative_result_and_resources(self):
        character_description = "Описание персонажа"

        next_game_year = 2

        world_data = "Описание мира"

        initiation_details = "Описание инициативы"


        response = await generate_initiative_result_and_resources(
            character_description,
            next_game_year,
            world_data,
            initiation_details
        )

        logger.info(response)

        self.assertEqual(True, True)  # add assertion here


if __name__ == '__main__':
    unittest.main()
