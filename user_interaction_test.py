import logging
import unittest

from user_interaction import generate_initiative_result_and_resources
from unittest import IsolatedAsyncioTestCase

logger = logging.getLogger(__name__)

class MyTestCase(IsolatedAsyncioTestCase):

    async def test_generate_initiative_result_and_resources(self):
        world_id = 1

        character_description = "Король Артур"

        next_game_year = 1600

        world_data = "Франция 16й век"

        initiation_details = "Поднять налоги на 10 пунктов"

        response = await generate_initiative_result_and_resources(
            world_id,
            world_data,
            character_description,
            next_game_year,
            initiation_details
        )


        logger.info(response)

        self.assertEqual(True, True)  # add assertion here


if __name__ == '__main__':
    unittest.main()
