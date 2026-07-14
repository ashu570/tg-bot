import os
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass(frozen=True)
class TelegramConfig:
    bot_token: str
    api_id: int
    api_hash: str
    raw_channel: int
    shadow_channel: int
    ready_channel: int
    tif_raw_channel: int

    @classmethod
    def from_env(cls) -> "TelegramConfig":
        """Factory method to parse and instantiate configuration from environment variables."""
        try:
            return cls(
                bot_token=os.environ["BOT_TOKEN"],
                api_id=int(os.environ["API_ID"]),
                api_hash=os.environ["API_HASH"],
                raw_channel=int(os.environ["RAW_CHANNEL_ID"]),
                shadow_channel=int(os.environ["SHADOW_CHANNEL_ID"]),
                ready_channel=int(os.environ["READY_TO_GO_CHANNEL_ID"]),
                tif_raw_channel=int(os.environ["TIF_RAW_CHANNEL_ID"]),
            )
        except KeyError as e:
            raise RuntimeError(f"Missing required environment variable: {e}")
        except ValueError as e:
            raise RuntimeError(f"Invalid environment variable format: {e}")
    
config = TelegramConfig.from_env()