from airflow.models import BaseOperator
from airflow.utils.decorators import apply_defaults

from utils.baseball_player_scrapper import BaseballPlayerScraper

class InflearnInfoToS3Operator(BaseOperator):
    @apply_defaults
    def __init__(self, db_config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_config = db_config

    def pre_execute(self, context):
        self.pitcher_scrapper = BaseballPlayerScraper(db_config=self.db_config, player_type="pitcher", max_retries=5)
        self.hitter_scrapper = BaseballPlayerScraper(db_config=self.db_config, player_type="hitter", max_retries=5)

    def execute(self, context):
        pass