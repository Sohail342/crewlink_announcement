import logging

logger = logging.getLogger(__name__)


class PushService:
    def send(self, member_id, title, preview):
        logger.info(
            "Push notification send",
            extra={"member_id": member_id, "title": title, "preview": preview},
        )
        return True
