import logging
from typing import Optional, Dict, Any, List
from app.config import settings

logger = logging.getLogger(__name__)


class MockCalls:
    def __init__(self):
        self.created_calls: List[Dict[str, Any]] = []

    async def create(self, to: str, from_: str, twiml: str) -> Dict[str, Any]:
        logger.warning(
            "⚠️  TWILIO MOCK MODE — no real call placed. "
            "to=%s from=%s | Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env to place real calls.",
            to, from_
        )
        call_record = {
            "sid": f"CA_mock_{len(self.created_calls) + 1}",
            "to": to,
            "from": from_,
            "twiml": twiml,
            "status": "queued_mock"
        }
        self.created_calls.append(call_record)
        return call_record


class MockMessages:
    def __init__(self):
        self.sent_messages: List[Dict[str, Any]] = []

    async def create(self, to: str, from_: str, body: str) -> Dict[str, Any]:
        logger.warning(
            "⚠️  TWILIO MOCK MODE — no real SMS sent. "
            "to=%s | Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env to send real SMS.",
            to
        )
        msg_record = {
            "sid": f"SM_mock_{len(self.sent_messages) + 1}",
            "to": to,
            "from": from_,
            "body": body,
            "status": "sent_mock"
        }
        self.sent_messages.append(msg_record)
        return msg_record


class TwilioClientWrapper:
    """
    Wraps the real Twilio SDK client.

    MOCK MODE ACTIVATION:
    Mock mode is ONLY active when TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN is absent
    from the environment. Every mock call/SMS logs a visible WARNING so it is never
    silently mistaken for a real API operation during testing or demoing.

    REAL CALL SIDs:
    When the real Twilio client is active, `create_call` returns the actual
    `call.sid` from Twilio's API response (e.g. "CAxxxxxxxx..."), not a placeholder.

    WEBHOOK REACHABILITY:
    The /voice/connect-status webhook in the <Dial action=...> TwiML must be a
    publicly reachable URL. localhost:8080 is NOT reachable by Twilio's servers.
    For local development: set up an ngrok tunnel and use the ngrok HTTPS URL.
    For production: deploy behind a public domain with TLS.
    """
    def __init__(self):
        self.account_sid = settings.TWILIO_ACCOUNT_SID
        self.auth_token = settings.TWILIO_AUTH_TOKEN
        self.from_number = settings.TWILIO_NUMBER or settings.TWILIO_PHONE_NUMBER

        self._real_client = None
        self._mock_calls = MockCalls()
        self._mock_messages = MockMessages()

        if self.account_sid and self.auth_token:
            try:
                from twilio.rest import Client
                self._real_client = Client(self.account_sid, self.auth_token)
                logger.info("Twilio real client initialized with account %s", self.account_sid[:8] + "...")
            except Exception as e:
                logger.warning(
                    "⚠️  TWILIO MOCK MODE — failed to initialize live Twilio Client: %s. "
                    "All calls/SMS will be mocked.", e
                )
        else:
            logger.warning(
                "⚠️  TWILIO MOCK MODE — TWILIO_ACCOUNT_SID or TWILIO_AUTH_TOKEN not set in environment. "
                "All calls/SMS will be mocked and no real telephony will occur."
            )

    @property
    def is_mock(self) -> bool:
        return self._real_client is None

    async def create_call(self, to: str, twiml: str, from_: Optional[str] = None) -> Dict[str, Any]:
        sender = from_ or self.from_number
        if self._real_client:
            try:
                call = self._real_client.calls.create(to=to, from_=sender, twiml=twiml)
                logger.info("Twilio real call placed: SID=%s to=%s", call.sid, to)
                return {"sid": call.sid, "status": call.status, "to": to, "from": sender}
            except Exception as e:
                logger.error("Live Twilio Call failed: %s. NOT falling back to mock — re-raising.", e)
                raise
        return await self._mock_calls.create(to=to, from_=sender, twiml=twiml)

    async def send_sms(self, to: str, body: str, from_: Optional[str] = None) -> Dict[str, Any]:
        sender = from_ or self.from_number
        if self._real_client:
            try:
                msg = self._real_client.messages.create(to=to, from_=sender, body=body)
                logger.info("Twilio real SMS sent: SID=%s to=%s", msg.sid, to)
                return {"sid": msg.sid, "status": msg.status, "to": to}
            except Exception as e:
                logger.error("Live Twilio SMS failed: %s. NOT falling back to mock — re-raising.", e)
                raise
        return await self._mock_messages.create(to=to, from_=sender, body=body)


twilio_client = TwilioClientWrapper()


async def send_connection_sms(
    to: str,
    target_name: str,
    source_name: str,
    source_phone: str,
    problem: str = "crop advisory"
) -> Dict[str, Any]:
    """
    Sends SMS notification to the target solver farmer with the requesting farmer's contact details.
    """
    body = (
        f"KisanNet: {source_name} needs help with {problem}. "
        f"Please call them at {source_phone}."
    )
    return await twilio_client.send_sms(to=to, body=body)
